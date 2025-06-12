import spade
import asyncio
from traffic_management.agents import TrafficLightAgent
from traffic_management.agents import VehicleAgent
from traffic_management.agents.simulation import ClockAgent


async def main():
    clock = ClockAgent("clock")
    tl = TrafficLightAgent("trafficlight")
    vh = VehicleAgent("vehicle")

    try:
        await asyncio.wait_for(
            asyncio.gather(clock.start(), tl.start(), vh.start()), timeout=10
        )
    except asyncio.TimeoutError:
        print(
            "Timeout while starting agents. Please check your XMPP server configuration."
        )
    await spade.wait_until_finished([tl, vh])


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
