from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio

import traci
from collections import defaultdict


class TrafficLightAgent(Agent):
    def __init__(self, jid, password, tl_id):
        super().__init__(jid, password)
        self.tl_id = tl_id
        self.waiting_vehicles = defaultdict(int)  # lane_id -> total wait time
        self.phase_requests = defaultdict(int)  # lane_id -> nº de pedidos de mudança

    class WaitNotificationReceiver(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if msg and msg.metadata.get("type") == "wait-notification":
                try:
                    vehicle_id, lane_id, wait_time = msg.body.split("|")
                    wait_time = int(wait_time)

                    prev_wait = self.agent.waiting_vehicles[lane_id]
                    self.agent.waiting_vehicles[lane_id] = max(prev_wait, wait_time)

                    print(f"[{self.agent.tl_id}] ⏱️ Vehicle {vehicle_id} is waiting {wait_time}s on lane {lane_id}")
                except Exception as e:
                    print(f"[{self.agent.tl_id}] ⚠️ Failed to parse wait-notification: {e}")

    class ChangePhaseNegotiation(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)

            if msg and msg.metadata.get("type") == "change-phase-request":
                try:
                    vehicle_id, lane_id = msg.body.split("|")
                    self.agent.phase_requests[lane_id] += 1

                    print(f"[{self.agent.tl_id}] 🔁 Received change-phase request from {vehicle_id} on {lane_id} "
                          f"(count: {self.agent.phase_requests[lane_id]})")

                    # Verifica se só há um pedido ativo
                    active_lanes = [l for l, c in self.agent.phase_requests.items() if c > 0]

                    if len(active_lanes) == 1 and active_lanes[0] == lane_id:
                        print(f"[{self.agent.tl_id}] ✅ Only one car waiting. Prioritizing lane {lane_id} now.")

                        program = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.agent.tl_id)[0]
                        phases = program.getPhases()
                        controlled_lanes = traci.trafficlight.getControlledLanes(self.agent.tl_id)

                        if lane_id in controlled_lanes:
                            lane_index = controlled_lanes.index(lane_id)

                            for i, phase in enumerate(phases):
                                if phase.state[lane_index] == 'G':  # green for this lane
                                    traci.trafficlight.setPhase(self.agent.tl_id, i)
                                    print(f"[{self.agent.tl_id}] 🚦 Changed to phase {i} for lane {lane_id}")
                                    break
                        else:
                            print(f"[{self.agent.tl_id}] ⚠️ Lane {lane_id} not found in controlled lanes.")

                        self.agent.reset_phase_requests()
                        self.agent.reset_waits()

                except Exception as e:
                    print(f"[{self.agent.tl_id}] ⚠️ Failed to process change-phase-request: {e}")

            await asyncio.sleep(1)

    async def setup(self):
        print(f"[{self.tl_id}] TrafficLightAgent started.")
        self.add_behaviour(self.WaitNotificationReceiver())
        self.add_behaviour(self.ChangePhaseNegotiation())

    def get_most_starved_lane(self):
        if not self.waiting_vehicles:
            return None
        return max(self.waiting_vehicles.items(), key=lambda x: x[1])[0]

    def reset_waits(self):
        self.waiting_vehicles.clear()

    def reset_phase_requests(self):
        self.phase_requests.clear()
