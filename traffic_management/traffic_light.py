import spade
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import asyncio


class TrafficLightAgent(Agent):
    class ControlLightBehaviour(PeriodicBehaviour):
        """Changes the traffic light color every 10 seconds."""

        async def run(self):
            if self.agent.light_state == "red":
                print(f"[{self.agent.name}] Changing light state to green.")
                self.agent.light_state = "green"
            elif self.agent.light_state == "green":
                print(f"[{self.agent.name}] Changing light state to yellow.")
                self.agent.light_state = "yellow"
            elif self.agent.light_state == "yellow":
                print(f"[{self.agent.name}] Changing light state to red.")
                self.agent.light_state = "red"
            else:
                print(f"[{self.agent.name}] Unknown light state, resetting to red.")
                self.agent.light_state = "red"

            # await self.send(
            #     Message(
            #         to="vehicle@localhost",
            #         sender=self.agent.jid,
            #         body=self.agent.light_state,
            #         metadata={"type": "traffic_light_update"},
            #     )
            # )

    async def setup(self):
        print("Setting up Traffic Light Agent...")
        self.light_state = "red"
        print(f"[{self.name}] Traffic Light agent started.")
        self.add_behaviour(self.ControlLightBehaviour(period=5))


async def main():
    print("Starting")
    traffic_light_agent = TrafficLightAgent("agent@localhost", "password")
    print("instantiated agent")
    try:
        await asyncio.wait_for(
            traffic_light_agent.start(auto_register=True), timeout=10
        )
    except asyncio.TimeoutError:
        print("Agent timed out")
    print("Traffic Light Agent started...")

    await spade.wait_until_finished(traffic_light_agent)
    print("Traffic Light Agent finished.")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
