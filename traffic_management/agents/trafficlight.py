from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
import time

import traci
from collections import defaultdict

class TrafficLightAgent(Agent):
    def __init__(self, jid, password, tl_id):
        super().__init__(jid, password)
        self.tl_id = tl_id
        self.waiting_vehicles = defaultdict(int)
        self.phase_requests = defaultdict(int)
        self.approach_distance = {}
        self.last_phase_change = time.time()
        self.starvation_threshold = 5  # seconds

    class WaitNotificationReceiver(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if msg and msg.metadata.get("type") == "wait-notification":
                try:
                    vehicle_id, lane_id, wait_time, dist = msg.body.split("|")
                    wait_time = int(wait_time)
                    dist = float(dist)

                    prev_wait = self.agent.waiting_vehicles[lane_id]
                    self.agent.waiting_vehicles[lane_id] = max(prev_wait, wait_time)

                    prev_dist = self.agent.approach_distance.get(lane_id, float("inf"))
                    self.agent.approach_distance[lane_id] = min(prev_dist, dist)

                except Exception as e:
                   pass

    class ChangePhaseNegotiation(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)

            if msg and msg.metadata.get("type") == "change-phase-request":
                try:
                    vehicle_id, lane_id = msg.body.split("|")[0:2]
                    self.agent.phase_requests[lane_id] += 1

                    target_lane = self.agent.decide_next_lane()
                    if target_lane:
                        self.agent.switch_to_lane(target_lane)
                        self.agent.reset_phase_requests()
                        self.agent.reset_waits()
                        self.agent.last_phase_change = time.time()

                except Exception as e:
                    print(f"[{self.agent.tl_id}] ⚠️ Failed to process change-phase-request: {e}")

            await asyncio.sleep(1)

    class StarvationMonitor(CyclicBehaviour):
        async def run(self):
            lane = self.agent.decide_next_lane()
            if lane:
                self.agent.switch_to_lane(lane)
                self.agent.reset_phase_requests()
                self.agent.reset_waits()
                self.agent.last_phase_change = time.time()
            await asyncio.sleep(1)

    async def setup(self):
        print(f"[{self.tl_id}] TrafficLightAgent started.")
        self.add_behaviour(self.WaitNotificationReceiver())
        self.add_behaviour(self.ChangePhaseNegotiation())
        self.add_behaviour(self.StarvationMonitor())

    def get_most_starved_lane(self):
        if not self.waiting_vehicles:
            return None
        return max(self.waiting_vehicles.items(), key=lambda x: x[1])[0]

    def decide_next_lane(self):
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)
        current_phase = traci.trafficlight.getPhase(self.tl_id)
        program = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        green_state = program.getPhases()[current_phase].state

        active_lanes = [lane for i, lane in enumerate(controlled_lanes) if green_state[i] == 'G']
        vehicles_in_active = sum(len(traci.lane.getLastStepVehicleIDs(l)) for l in active_lanes)

        if vehicles_in_active == 0:
            candidates = [
                (lane, dist) for lane, dist in self.approach_distance.items()
                if dist < 30
            ]
            if candidates:
                lane = min(candidates, key=lambda x: x[1])[0]
                return lane


        requested_lanes = [lane for lane, count in self.phase_requests.items() if count > 0]
        starved_lane = self.get_most_starved_lane()
        time_since_change = time.time() - self.last_phase_change


        if starved_lane and time_since_change >= self.starvation_threshold:
            return starved_lane

        if requested_lanes:
            def score(lane):
                dist = self.approach_distance.get(lane, float("inf"))
                return (self.phase_requests[lane], -dist)  # mais pedidos e menor distância

            best_lane = max(requested_lanes, key=score)
            return best_lane

        return None

    def switch_to_lane(self, lane_id):
        program = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        phases = program.getPhases()
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)

        if lane_id in controlled_lanes:
            lane_index = controlled_lanes.index(lane_id)
            for i, phase in enumerate(phases):
                if phase.state[lane_index] == 'G':
                    traci.trafficlight.setPhase(self.tl_id, i)
                    return

    def reset_waits(self):
        self.waiting_vehicles.clear()
        self.approach_distance.clear()

    def reset_phase_requests(self):
        self.phase_requests.clear()