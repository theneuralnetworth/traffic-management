from re import L
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
from enum import Enum

from traffic_management.agents.vehicles import TrafficLightStatus


class LightState(Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"


class TrafficLightAgent(Agent):
    class ControlLightBehaviour(PeriodicBehaviour):
        async def run(self):
            match self.agent.light_state:
                case LightState.RED:
                    self.agent.light_state = LightState.GREEN
                case LightState.GREEN:
                    self.agent.light_state = LightState.YELLOW
                case LightState.YELLOW:
                    self.agent.light_state = LightState.RED
                case _:
                    self.agent.light_state = LightState.RED
            print(
                f"[{self.agent.name}] Light changed to {self.agent.light_state.value}."
            )

            await self.send(
                TrafficLightStatus().build_message(
                    to=f"vehicle@{self.agent.jid.domain}",
                    body=self.agent.light_state.value,
                )
            )

    async def set_light_state(self, state: LightState):
        self.light_state = state

    async def setup(self):
        self.light_state = LightState.RED
        print(f"[{self.name}] Traffic Light agent started.")
        self.add_behaviour(self.ControlLightBehaviour(period=5))
