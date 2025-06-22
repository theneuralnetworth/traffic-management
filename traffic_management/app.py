import traci
import spade
import asyncio
import xml.etree.ElementTree as ET
from traffic_management.agents import TrafficLightAgent
from traffic_management.agents.car_agent import CarAgent


# --- SUMO Configuration ---
SUMO_CMD = ["sumo-gui", "-c", "config/sumo/map/map.sumocfg"]


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


def generate_car_agents(num_cars: int, routes: list) -> list:
    car_agents = []
    for i in range(num_cars):
        jid = f"car{i}"
        agent = CarAgent(jid, "password", jid, routes)
        car_agents.append(agent)
    return car_agents


async def main():
    conn = traci.connect(port=8813, label="main")

    conn.simulationStep()

    traffic_light_ids = conn.trafficlight.getIDList()
    print(f"[MAIN] Found traffic lights: {traffic_light_ids}")
    agents = generate_traffic_light_agents(traffic_light_ids)

    routes = conn.route.getIDList()
    routes = load_routes("config/sumo/map/trips.trips.xml")
    car_agents = generate_car_agents(5, routes)  # Create 5 car agents
    agents.extend(car_agents)

    # Start all agents
    try:
        await asyncio.wait_for(
            asyncio.gather(*(agent.start() for agent in agents)),
            timeout=10,
        )
    except asyncio.TimeoutError:
        print(
            "Timeout while starting agents. Please check your XMPP server configuration."
        )

    # Run the simulation loop
    try:
        step = 0
        while step < 5000:
            conn.simulationStep()  # Advance simulation by one step
            await asyncio.sleep(0.1)  # Allow async behaviors to run
            step += 1
    except KeyboardInterrupt:
        print("[MAIN] Simulation interrupted.")

    await spade.wait_until_finished(agents)
    conn.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
