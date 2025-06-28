from encodings.punycode import T
from spade.behaviour import PeriodicBehaviour
from traffic_management.agents.base import BaseAgent


class ClockAgent(BaseAgent):
    def __init__(self, id: str):
        super().__init__(id=id)

    class StepSimulationBehaviour(PeriodicBehaviour):
        async def run(self):
            if self.agent.sumo_conn:
                self.agent.sumo_conn.simulationStep()
                print("[clock] simulation step triggered")
            else:
                print("[clock] No SUMO connection established.")

    async def setup(self):
        print(f"[{self.name}] Clock agent started.")
        self.connect_to_sumo()
        self.add_behaviour(self.StepSimulationBehaviour(period=1))
