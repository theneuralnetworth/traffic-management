from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class VehicleAgent(Agent):
    class MoveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body == "green":
                    print(f"[{self.agent.name}] Light is green. Proceeding...")
                elif msg.body == "red":
                    print(f"[{self.agent.name}] Light is red. Stopping...")

    async def setup(self):
        print(f"[{self.name}] Vehicle agent started.")
        self.add_behaviour(self.MoveBehaviour())
