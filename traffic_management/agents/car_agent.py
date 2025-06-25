from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message

import traci
import random
import asyncio

class VehicleAgentLogic:
    def __init__(self, veh_id):
        self.id = veh_id
        self.total_wait_time = 0
        self.current_wait = 0
        self.lane = None
        self.stopped = False

    def update(self):
        if self.id not in traci.vehicle.getIDList():
            return None

        speed = traci.vehicle.getSpeed(self.id)
        lane_id = traci.vehicle.getLaneID(self.id)
        self.lane = lane_id

        if speed < 0.1:
            self.current_wait += 1
            self.stopped = True
        else:
            self.total_wait_time += self.current_wait
            self.current_wait = 0
            self.stopped = False

        tls_info = traci.vehicle.getNextTLS(self.id)
        if tls_info:
            tls_id, dist, light_state, lane = tls_info[0]

            if dist < 50 and light_state in ['r', 'y']:
                return (tls_id, lane_id, self.current_wait)

        return None

    def get_total_wait_time(self):
        return self.total_wait_time + self.current_wait


class CarAgent(Agent):
    def __init__(self, jid, password, car_id, routes, tls_agents_map):
        super().__init__(jid, password)
        self.car_id = car_id
        self.routes = routes  # List of (vehicle_id, [edge1, edge2, ...])
        self.tls_agents_map = tls_agents_map  # Dict[tls_id: str -> jid: str]
        self.logic = VehicleAgentLogic(car_id)

    class CreateVehicleBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"[{self.agent.car_id}] Creating vehicle...")

            _, route = random.choice(self.agent.routes)
            route_id = f"route_{self.agent.car_id}"

            traci.route.add(route_id, route)
            traci.vehicle.add(self.agent.car_id, route_id)

            print(f"[{self.agent.car_id}] Vehicle created from {route[0]} to {route[-1]}")

    class MonitorBehaviour(CyclicBehaviour):
        async def run(self):
            result = self.agent.logic.update()
            if result:
                tls_id, lane_id, wait = result
                if tls_id in self.agent.tls_agents_map:
                    receiver_jid = self.agent.tls_agents_map[tls_id]
                    msg = Message(to=receiver_jid)
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("type", "wait-notification")
                    msg.body = f"{self.agent.car_id}|{lane_id}|{wait}"
                    await self.send(msg)

                    msg_request = Message(to=receiver_jid)
                    msg_request.set_metadata("performative", "request")
                    msg_request.set_metadata("type", "change-phase-request")
                    msg_request.body = f"{self.agent.car_id}|{lane_id}"
                    await self.send(msg_request)
            await asyncio.sleep(1)

    async def setup(self):
        print(f"[{self.car_id}] CarAgent started.")
        self.add_behaviour(self.CreateVehicleBehaviour())
        self.add_behaviour(self.MonitorBehaviour())
