import os
import traci
import spade
import asyncio
import xml.etree.ElementTree as ET
from traffic_management.agents import TrafficLightAgent
from traffic_management.agents.car_agent import CarAgent
from traffic_management.agents import ClockAgent, AmbulanceAgent, PoliceAgent


SUMO_HOST = os.getenv("SUMO_HOST", "localhost")


# --- Load routes from a .rou.xml file ---
def load_routes(filename):
    """
    Parses a SUMO .rou.xml file and extracts the list of routes.
    Each route is returned as a tuple: (vehicle_id, [edge1, edge2, ...])
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    routes = []
    for vehicle in root.findall("vehicle"):
        veh_id = vehicle.attrib["id"]
        route_elem = vehicle.find("route")
        if route_elem is not None:
            edges = route_elem.attrib["edges"].split()
            routes.append((veh_id, edges))
    return routes


def generate_traffic_light_agents(traffic_light_ids: tuple) -> list:
    traffic_light_agents = []
    for i, tl_id in enumerate(traffic_light_ids):
        jid = f"traffic-light-{i}"
        agent = TrafficLightAgent(jid, tl_id)
        traffic_light_agents.append(agent)
    return traffic_light_agents


def generate_emergency_vehicle_agents(num_ambulance: int, num_police: int) -> list:
    ambulances = [AmbulanceAgent(f"ambulance-{i}") for i in range(num_ambulance)]
    police = [PoliceAgent(f"police-{i}") for i in range(num_police)]
    return ambulances + police


def generate_car_agents(num_cars: int, routes: list) -> list:
    return [CarAgent(f"car{i}", "password", f"car{i}", routes) for i in range(num_cars)]


async def main():
    conn = traci.connect(host=SUMO_HOST, port=8813, label="main")
    conn.simulationStep()
    print("[MAIN] Starting simulation...")

    agents = []

    # Create and start the clock agent
    clock = ClockAgent("clock")
    await clock.start()

    # Create traffic light agents
    traffic_light_ids = conn.trafficlight.getIDList()
    print(f"[MAIN] Found traffic lights: {traffic_light_ids}")
    traffic_light_agents = generate_traffic_light_agents(traffic_light_ids)
    agents.extend(traffic_light_agents)

    # Create emergency vehicle agents
    emergency_agents = generate_emergency_vehicle_agents(num_ambulance=2, num_police=2)
    agents.extend(emergency_agents)

    # Create car agents
    # routes = conn.route.getIDList()
    # routes = load_routes("config/sumo/map/trips.trips.xml")
    # car_agents = generate_car_agents(5, routes)  # Create 5 car agents
    # agents.extend(car_agents)

    # Start all agents
    try:
        await asyncio.wait_for(
            asyncio.gather(*(agent.start() for agent in agents)),
            timeout=5,
        )
    except asyncio.TimeoutError:
        print(
            "Timeout while starting agents. Please check your XMPP server configuration."
        )

    await spade.wait_until_finished(agents)

    clock.stop()
    conn.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
