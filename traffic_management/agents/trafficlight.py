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
        self.starvation_threshold = 5     # total wait threshold for inline starvation
        self.starvation_inline_threshold = 8  # waiting_vehicles threshold to trigger inline starvation

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
            msg = await self.receive(timeout=0.5)
            if not msg:
                return
            # Only messages with metadata type "change-phase-request" are delivered here
            vehicle_id, lane_id = msg.body.split("|", 1)
            print(f"[{self.agent.jid}] Received change phase request from {vehicle_id} for lane {lane_id}")
            self.agent.phase_requests[lane_id] += 1

            target = self.agent.decide_next_lane()
            if target:
                self.agent.switch_to_lane(target)
                self.agent.reset_phase_requests()
                self.agent.reset_waits(target)
                self.agent.last_phase_change = time.time()

    class StarvationMonitor(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1)
            # enforce starvation policy if minimum green elapsed and any lane starved
            now = time.time()
            lane = self.agent.get_most_starved_lane()
            if lane and self.agent.waiting_vehicles[lane] >= self.agent.starvation_threshold:
                self.agent.switch_to_lane(lane)
                self.agent.reset_phase_requests()
                self.agent.reset_waits(lane)
                self.agent.last_phase_change = now

    async def setup(self):
        self.setup_mqtt()
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
        now = time.time()
        conn = self.sumo_conn
        controlled = conn.trafficlight.getControlledLanes(self.tl_id)
        phase = conn.trafficlight.getPhase(self.tl_id)
        program = conn.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        green_state = program.getPhases()[phase].state

        # 1) inline starvation: if any lane waited too long, serve it
        starved = self.get_most_starved_lane()
        if starved and self.waiting_vehicles[starved] >= self.starvation_inline_threshold:
            return starved

        # 2) handle explicit phase requests
        req_lanes = [l for l, count in self.phase_requests.items() if count > 0]
        if req_lanes:
            score = lambda l: (self.phase_requests[l], -self.approach_distance.get(l, float('inf')))
            return max(req_lanes, key=score)

        # 3) if current green has no moving vehicles, open closest waiting
        active = [l for i, l in enumerate(controlled) if green_state[i] == 'G']
        vehicles_active = sum(len(conn.lane.getLastStepVehicleIDs(l)) for l in active)
        if vehicles_active == 0 and self.approach_distance:
            close = [(l, d) for l, d in self.approach_distance.items() if d < 30]
            if close:
                return min(close, key=lambda x: x[1])[0]

        return None

    def switch_to_lane(self, lane_id):
        conn = self.sumo_conn
        program = conn.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        phases = program.getPhases()
        controlled = conn.trafficlight.getControlledLanes(self.tl_id)
        try:
            idx = controlled.index(lane_id)
            # set the phase with green for that lane
            for i, ph in enumerate(phases):
                if ph.state[idx] == 'G':
                    conn.trafficlight.setPhase(self.tl_id, i)
                    # publish the new phase index to MQTT
                    self.mqtt.publish(
                        f"traffic_light/{self.jid.local}/state", i
                    )
                    return
        except Exception:
            pass

    def reset_waits(self, served_lane: str):
        # only clear data for the lane that was just served
        self.waiting_vehicles.pop(served_lane, None)
        self.approach_distance.pop(served_lane, None)

    def reset_phase_requests(self):
        self.phase_requests.clear()
