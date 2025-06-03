import os
import spade
import asyncio
from traffic_management.agents import TrafficLightAgent
from traffic_management.agents import VehicleAgent


async def main():
    xmpp_server = os.getenv("XMPP_HOST", "localhost")

    tl = TrafficLightAgent(f"trafficlight@{xmpp_server}", "password")
    vh = VehicleAgent(f"vehicle@{xmpp_server}", "password")

    try:
        await asyncio.wait_for(asyncio.gather(tl.start(), vh.start()), timeout=10)
    except asyncio.TimeoutError:
        print(
            "Timeout while starting agents. Please check your XMPP server configuration."
        )
    await spade.wait_until_finished([tl, vh])


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
