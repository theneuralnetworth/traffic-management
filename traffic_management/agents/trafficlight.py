from traffic_management.agents.base import BaseAgent
from spade.behaviour import PeriodicBehaviour
import traci


class TrafficLightAgent(BaseAgent):
    def __init__(self, id: str, sumo_id: str = None):
        super().__init__(id=id)
        self.sumo_id = sumo_id
        self.current_phase = ""

    class ControlLightBehaviour(PeriodicBehaviour):
        async def run(self):
            """Cycles the traffic light state. ie. Green -> Yellow -> Red -> Green -> ..."""
            self.agent.current_phase = self.agent.sumo_conn.trafficlight.getPhase(
                self.agent.sumo_id
            )
            phases = self.agent.sumo_conn.trafficlight.getAllProgramLogics(
                self.agent.sumo_id
            )[0].phases
            next_phase_index = (self.agent.current_phase + 1) % len(phases)
            next_phase = phases[next_phase_index]
            self.agent.sumo_conn.trafficlight.setPhase(
                self.agent.sumo_id, next_phase_index
            )
            print(
                f"[{self.agent.name}] Traffic light {self.agent.sumo_id} changed to phase {next_phase}."
            )
            # Publish the new state to MQTT
            self.agent.mqtt.publish(
                f"traffic_light/{self.agent.jid.local}/state", next_phase_index
            )

    async def setup(self):
        self.setup_mqtt()
        self.connect_to_sumo()
        print(f"[{self.name}] Traffic Light agent started.")
        self.add_behaviour(self.ControlLightBehaviour(period=10))
