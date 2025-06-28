from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message

import traci
from traci import getConnection
import random
import asyncio

from traffic_management.agents.base import BaseAgent


class VehicleAgentLogic:
    def __init__(self, veh_id, conn_label="main"):
        self.id = veh_id
        self.conn_label = conn_label
        self.total_wait_time = 0
        self.current_wait = 0
        self.lane = None
        self.stopped = False

    def update(self):
        # Get the SUMO connection by label
        conn = getConnection(self.conn_label)

        # If the vehicle is no longer in the simulation, do nothing
        if self.id not in conn.vehicle.getIDList():
            return None

        # Retrieve current speed and lane
        speed = conn.vehicle.getSpeed(self.id)
        raw_lane = conn.vehicle.getLaneID(self.id)
        lane_id = raw_lane.lstrip(":-")
        self.lane = lane_id

        # Update waiting times based on speed
        if speed < 0.1:
            self.current_wait += 1
            self.stopped = True
        else:
            self.total_wait_time += self.current_wait
            self.current_wait = 0
            self.stopped = False

        # Check the next traffic light ahead, if any
        tls_info = conn.vehicle.getNextTLS(self.id)
        if tls_info:
            tls_id, lane_index, dist, light_state = tls_info[0]

            if dist < 50 and light_state in ['r', 'y']:
                return tls_id, lane_id, self.current_wait, dist

        return None

    def get_total_wait_time(self):
        # Return combined total of past and current waiting time
        return self.total_wait_time + self.current_wait


class CarAgent(BaseAgent):
    def __init__(self, car_id, routes, tls_agents_map, conn_label="main"):
        super().__init__(car_id)
        self.car_id = car_id  # store routes for dynamic or static use
        self.tls_agents_map = tls_agents_map
        self.routes = routes
        self.conn_label = conn_label
        self.logic = VehicleAgentLogic(car_id, conn_label)

    class CreateVehicleBehaviour(OneShotBehaviour):
        async def run(self):
            # Connect to the labeled SUMO instance
            conn = getConnection(self.agent.conn_label)
            vid, route = random.choice(self.agent.routes)

            route_id = f"route_{self.agent.car_id}"
            # Add the computed route and spawn the vehicle
            conn.route.add(route_id, route)
            conn.vehicle.add(self.agent.car_id, route_id)

    class MonitorBehaviour(CyclicBehaviour):
        async def run(self):
            conn = getConnection(self.agent.conn_label)

            # Update logic and, if needed, send messages to the traffic light agent
            result = self.agent.logic.update()
            if result:
                tls_id, lane_id, wait, dist = result
                if tls_id in self.agent.tls_agents_map:
                    receiver_jid = self.agent.tls_agents_map[tls_id]

                    # Inform traffic light about current wait
                    msg = Message(to=receiver_jid)
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "wait-notification")
                    msg.body = f"{self.agent.car_id}|{lane_id}|{wait}|{dist}"
                    await self.send(msg)

                    # Request a phase change if needed
                    msg_req = Message(to=receiver_jid)
                    msg_req.set_metadata("performative", "request")
                    msg_req.set_metadata("type", "change-phase-request")
                    msg_req.body = f"{self.agent.car_id}|{lane_id}"
                    await self.send(msg_req)

            # Pause briefly before next cycle
            await asyncio.sleep(1)

    async def setup(self):
        print(f"[{self.car_id}] CarAgent started.")
        # Add behaviors to spawn and monitor the vehicle
        self.add_behaviour(self.CreateVehicleBehaviour())
        self.add_behaviour(self.MonitorBehaviour())
