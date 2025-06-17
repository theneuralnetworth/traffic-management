from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
import traci

class TrafficLightAgent(Agent):
    def __init__(self, jid, password, traffic_light_id):
        super().__init__(jid, password)
        self.tl_id = traffic_light_id  # The SUMO traffic light ID controlled by this agent

    class TrafficLightControlBehaviour(PeriodicBehaviour):
        async def run(self):
            # Get current phase of the traffic light
            current_phase = traci.trafficlight.getPhase(self.agent.tl_id)
            print(f"[{self.agent.tl_id}] Current phase: {current_phase}")

            # Example logic: cycle through all phases
            num_phases = len(traci.trafficlight.getCompleteRedYellowGreenDefinition(self.agent.tl_id)[0].phases)
            next_phase = (current_phase + 1) % num_phases
            traci.trafficlight.setPhase(self.agent.tl_id, next_phase)

            print(f"[{self.agent.tl_id}] Changed to phase: {next_phase}")

    async def setup(self):
        print(f"[{self.tl_id}] TrafficLightAgent started.")
        # Add periodic behavior that runs every 10 seconds
        b = self.TrafficLightControlBehaviour(period=10)
        self.add_behaviour(b)
