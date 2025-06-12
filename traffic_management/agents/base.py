import os
from spade.agent import Agent


class BaseAgent(Agent):
    def __init__(self, id: str, password: str = "password"):
        self.server = os.getenv("XMPP_HOST", "localhost")
        jid = f"{id}@{self.server}"
        super().__init__(jid=jid, password=password)
