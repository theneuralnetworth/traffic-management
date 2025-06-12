import os
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour


class BaseAgent(Agent):
    def __init__(self, id: str, password: str = "password"):
        self.server = os.getenv("XMPP_HOST", "localhost")
        jid = f"{id}@{self.server}"
        super().__init__(jid=jid, password=password)

    class ClockTickReceiveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if msg and msg.metadata.get("type") == "clock_tick":
                print(f"[{self.agent.name}] Received clock tick")
