from traffic_management.agents.base import BaseAgent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import Message
from traffic_management.agents.simulation import ClockMessage


class TrafficLightStatus(Template):
    def __init__(self):
        super().__init__()
        self.set_metadata("type", "traffic_light_update")
        self.set_metadata("performative", "update")

    def build_message(self, to, body) -> Message:
        msg = Message(to=to, body=body)
        msg.set_metadata("type", "traffic_light_update")
        msg.set_metadata("performative", "update")
        return msg


class VehicleAgent(BaseAgent):
    def __init__(self, id: str):
        super().__init__(id=id)

    class MoveBehaviour(CyclicBehaviour):
        async def run(self):
            msg: Message = await self.receive(timeout=10)
            if not msg:
                return
            match msg.body:
                case "green":
                    print(f"[{self.agent.name}] Light is green. Proceeding...")
                case "red":
                    print(f"[{self.agent.name}] Light is red. Stopping...")
                case "yellow":
                    print(f"[{self.agent.name}] Light is yellow. Caution...")

    class ClockBehaviour(CyclicBehaviour):
        async def run(self):
            msg: Message = await self.receive(timeout=1)
            if msg:
                print(f"[{self.agent.name}] Clock tick received: {msg.body}")

    async def setup(self):
        print(f"[{self.name}] Vehicle agent started.")
        self.add_behaviour(self.ClockBehaviour(), ClockMessage())
        self.add_behaviour(self.MoveBehaviour(), TrafficLightStatus())
