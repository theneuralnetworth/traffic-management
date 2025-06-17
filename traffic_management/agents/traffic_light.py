from traffic_management.agents.base import BaseAgent
from spade.behaviour import PeriodicBehaviour
from enum import Enum
from traffic_management.agents.vehicles import TrafficLightStatus
from traffic_management.agents.simulation import ClockTickMessage


class LightState(Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"


class TrafficLightAgent(BaseAgent):
    def __init__(self, id: str):
        super().__init__(id=id)
        self.light_state = LightState.RED

    class ControlLightBehaviour(PeriodicBehaviour):
        async def run(self):
            match self.agent.light_state:
                case LightState.RED:
                    self.agent.set_light_state(LightState.GREEN)
                case LightState.GREEN:
                    self.agent.set_light_state(LightState.YELLOW)
                case LightState.YELLOW:
                    self.agent.set_light_state(LightState.RED)
                case _:
                    self.agent.set_light_state(LightState.RED)
            print(
                f"[{self.agent.name}] Light changed to {self.agent.light_state.value}."
            )

            await self.send(
                TrafficLightStatus().build_message(
                    to=f"vehicle@{self.agent.jid.domain}",
                    body=self.agent.light_state.value,
                )
            )

    def set_light_state(self, state: LightState):
        self.light_state = state
        self.mqtt.publish(f"traffic_light/{self.jid.local}/state", state.value)

    async def setup(self):
        self.setup_mqtt()
        self.light_state = LightState.RED
        print(f"[{self.name}] Traffic Light agent started.")
        self.add_behaviour(self.ClockTickReceiveBehaviour(), ClockTickMessage())
        self.add_behaviour(self.ControlLightBehaviour(period=5))
