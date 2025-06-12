from spade.behaviour import PeriodicBehaviour
from traffic_management.agents.base import BaseAgent
from spade.message import Message
from spade.template import Template


class ClockMessage(Template):
    def __init__(self):
        super().__init__()
        self.set_metadata("type", "clock_tick")
        self.set_metadata("performative", "inform")

    def build_message(self, to) -> Message:
        msg = Message(to=to, body="tick")
        msg.set_metadata("type", "clock_tick")
        msg.set_metadata("performative", "inform")
        return msg


class ClockAgent(BaseAgent):
    def __init__(self, id: str):
        super().__init__(id=id)
        self.all_agents = [
            "trafficlight",
            "vehicle",
        ]

    class TickBehaviour(PeriodicBehaviour):
        async def run(self):
            for agent in self.agent.all_agents:
                msg: Message = ClockMessage().build_message(
                    to=f"{agent}@{self.agent.jid.domain}"
                )
                await self.send(msg)

    async def setup(self):
        print(f"[{self.name}] Clock agent started.")
        self.add_behaviour(self.TickBehaviour(period=1))
