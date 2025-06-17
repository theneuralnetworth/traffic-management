from traffic_management.agents.base import BaseAgent
from spade.behaviour import PeriodicBehaviour
import traci


class TrafficLightAgent(BaseAgent):
    def __init__(self, id: str, sumo_id: str = None):
        super().__init__(id=id)
        self.sumo_id = sumo_id

    class ControlLightBehaviour(PeriodicBehaviour):
        async def run(self):
            self.agent.current_phase = traci.trafficlight.getPhase(self.agent.sumo_id)
            self.cycle_light_phase()

    def cycle_light_phase(self):
        """Cycles the traffic light state. ie. Green -> Yellow -> Red -> Green -> ..."""
        phases = traci.trafficlight.getCompleteRedYellowGreenDefinition(
            self.agent.tl_id
        )[0].phases
        next_phase = (self.current_phase + 1) % len(phases)
        traci.trafficlight.setPhase(self.agent.tl_id, next_phase)

        # Publish the new state to MQTT
        self.mqtt.publish(f"traffic_light/{self.jid.local}/state", next_phase)

    async def setup(self):
        self.setup_mqtt()
        print(f"[{self.name}] Traffic Light agent started.")
        self.add_behaviour(self.ControlLightBehaviour(period=10))
