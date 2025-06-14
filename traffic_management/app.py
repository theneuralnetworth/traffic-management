import spade
import asyncio
from traffic_management.agents import (
    TrafficLightAgent,
    VehicleAgent,
    Ambulance,
    EmergencyDispatch,
    ClockAgent,
)


async def main():
    agents = [
        # ClockAgent("clock"),
        # TrafficLightAgent("trafficlight"),
        # VehicleAgent("vehicle"),
        Ambulance("ambulance1"),
        Ambulance("ambulance2"),
        EmergencyDispatch("emergency_dispatch"),
    ]
    try:
        await asyncio.wait_for(
            asyncio.gather(*(agent.start() for agent in agents)),
            timeout=10,
        )
    except asyncio.TimeoutError:
        print(
            "Timeout while starting agents. Please check your XMPP server configuration."
        )
    await spade.wait_until_finished(agents)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
