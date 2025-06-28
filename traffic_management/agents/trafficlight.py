from spade.behaviour import CyclicBehaviour
from spade.template import Template
from collections import defaultdict
import asyncio
import time

from traffic_management.agents.base import BaseAgent

class TrafficLightAgent(BaseAgent):
    def __init__(self, id: str, tl_id: str):
        super().__init__(id)
        self.tl_id = tl_id
        self.waiting_vehicles = defaultdict(int)
        self.phase_requests = defaultdict(int)
        self.approach_distance = {}
        self.last_phase_change = time.time()
        self.starvation_threshold = 5  # seconds

    class WaitNotificationReceiver(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return
            # Only messages with metadata type "wait-notification" are delivered here
            vehicle_id, lane_id, wait_time, dist = msg.body.split("|")
            wait_time = int(wait_time)
            dist = float(dist)

            # update max wait and min distance
            self.agent.waiting_vehicles[lane_id] = max(
                self.agent.waiting_vehicles[lane_id], wait_time
            )
            self.agent.approach_distance[lane_id] = min(
                self.agent.approach_distance.get(lane_id, float('inf')), dist
            )

    class ChangePhaseNegotiation(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return
            # Only messages with metadata type "change-phase-request" are delivered here
            vehicle_id, lane_id = msg.body.split("|", 1)
            self.agent.phase_requests[lane_id] += 1

            target = self.agent.decide_next_lane()
            if target:
                self.agent.switch_to_lane(target)
                self.agent.reset_phase_requests()
                self.agent.reset_waits()
                self.agent.last_phase_change = time.time()

    class StarvationMonitor(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1)
            # enforce starvation policy if threshold exceeded
            if time.time() - self.agent.last_phase_change < self.agent.starvation_threshold:
                return
            lane = self.agent.decide_next_lane()
            if lane:
                self.agent.switch_to_lane(lane)
                self.agent.reset_phase_requests()
                self.agent.reset_waits()
                self.agent.last_phase_change = time.time()

    async def setup(self):
        # Connect to SUMO via BaseAgent
        self.connect_to_sumo(label='main')

        print(f"[{self.jid}] TrafficLightAgent for '{self.tl_id}' started.")

        # Behaviour to receive wait notifications
        t_wait = Template()
        t_wait.set_metadata("performative", "inform")
        t_wait.set_metadata("type", "wait-notification")
        self.add_behaviour(self.WaitNotificationReceiver(), t_wait)

        # Behaviour to handle change-phase requests
        t_req = Template()
        t_req.set_metadata("performative", "request")
        t_req.set_metadata("type", "change-phase-request")
        self.add_behaviour(self.ChangePhaseNegotiation(), t_req)

        # Periodic starvation monitor
        self.add_behaviour(self.StarvationMonitor())

    def get_most_starved_lane(self):
        if not self.waiting_vehicles:
            return None
        return max(self.waiting_vehicles.items(), key=lambda x: x[1])[0]

    def decide_next_lane(self):
        # Use self.sumo_conn instead of traci
        conn = self.sumo_conn
        controlled = conn.trafficlight.getControlledLanes(self.tl_id)
        phase = conn.trafficlight.getPhase(self.tl_id)
        program = conn.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        green_state = program.getPhases()[phase].state

        # identify lanes currently green
        active = [l for i,l in enumerate(controlled) if green_state[i] == 'G']
        vehicles_active = sum(len(conn.lane.getLastStepVehicleIDs(l)) for l in active)

        # if no one moving, pick closest waiting
        if vehicles_active == 0 and self.approach_distance:
            close = [(l,d) for l,d in self.approach_distance.items() if d < 30]
            if close:
                return min(close, key=lambda x: x[1])[0]

        # starvation check
        starved = self.get_most_starved_lane()
        if starved and time.time() - self.last_phase_change >= self.starvation_threshold:
            return starved

        # handle requests
        req_lanes = [l for l,count in self.phase_requests.items() if count>0]
        if req_lanes:
            # score by (#requests, -distance)
            score = lambda l: (self.phase_requests[l], -self.approach_distance.get(l, float('inf')))
            return max(req_lanes, key=score)

        return None

    def switch_to_lane(self, lane_id):
        conn = self.sumo_conn
        program = conn.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        phases = program.getPhases()
        controlled = conn.trafficlight.getControlledLanes(self.tl_id)
        idx = controlled.index(lane_id)
        # set the phase with green for that lane
        for i,ph in enumerate(phases):
            if ph.state[idx] == 'G':
                conn.trafficlight.setPhase(self.tl_id, i)
                return

    def reset_waits(self):
        self.waiting_vehicles.clear()
        self.approach_distance.clear()

    def reset_phase_requests(self):
        self.phase_requests.clear()
