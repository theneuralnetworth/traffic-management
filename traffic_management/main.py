import traci
import asyncio
import xml.etree.ElementTree as ET
from traffic_management.agents.trafficlight import TrafficLightAgent
from traffic_management.agents.car_agent import CarAgent

# --- SUMO Configuration ---
SUMO_CMD = ["sumo-gui", "-c", "../config/sumo/map/map.sumocfg"]
# SUMO_CMD = ["sumo", "--start", "-c", "../config/sumo/map/map.sumocfg"]

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

async def main():
    # Start the SUMO simulation (TraCI connection)
    traci.start(SUMO_CMD)

    # --- Create traffic light agents ---
    traffic_light_ids = traci.trafficlight.getIDList()
    print(f"[MAIN] Found traffic lights: {traffic_light_ids}")

    agents = []

    tls_agents_map = {}
    for i, tl_id in enumerate(traffic_light_ids):
        jid = f"semaforo{i}@localhost"
        password = "password"
        agent = TrafficLightAgent(jid, password, tl_id)
        try:
            await agent.start(auto_register=True)
            tls_agents_map[tl_id] = jid
            print(f"[MAIN] ✅ Started agent {jid} for traffic light {tl_id}")
            agents.append(agent)
        except Exception as e:
            print(f"[MAIN] ❌ Failed to start agent {jid} for {tl_id}: {e}")

    # --- Load pre-generated routes ---
    routes = load_routes("../config/sumo/map/routes.rou.xml")

    # --- Create car agents (each adds a vehicle to the simulation) ---
    for i in range(40):
        jid = f"car{i}@localhost"
        password = "password"
        car_id = f"car{i}"
        agent = CarAgent(jid, password, car_id, routes, tls_agents_map)  # Pass routes to the agent
        try:
            await agent.start(auto_register=True)
            print(f"[MAIN] ✅ Started agent {jid} for vehicle {car_id}")
            agents.append(agent)
        except Exception as e:
            print(f"[MAIN] ❌ Failed to start agent {jid} for vehicle {car_id}: {e}")

    # --- Run the simulation loop ---
    try:
        step = 0
        while step < 200:
            traci.simulationStep()          # Advance simulation by one step
            await asyncio.sleep(0.1)        # Allow async behaviors to run
            step += 1
    except KeyboardInterrupt:
        print("[MAIN] Simulation interrupted.")

    # --- Shutdown all agents and close simulation ---
    for agent in agents:
        await agent.stop()
    traci.close()

if __name__ == "__main__":
    asyncio.run(main())
