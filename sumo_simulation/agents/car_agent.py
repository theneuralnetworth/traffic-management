from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
import traci
import random

class CarAgent(Agent):
    def __init__(self, jid, password, car_id, routes):
        super().__init__(jid, password)
        self.car_id = car_id
        self.routes = routes  # List of routes: each route is (vehicle_id, [edge1, edge2, ...])

    class CreateVehicleBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"[{self.agent.car_id}] Creating vehicle...")

            # Choose a random route from the list
            _, route = random.choice(self.agent.routes)

            # Create a new route in SUMO and assign it to the vehicle
            route_id = f"route_{self.agent.car_id}"
            traci.route.add(route_id, route)
            traci.vehicle.add(self.agent.car_id, route_id)

            print(f"[{self.agent.car_id}] Vehicle created from {route[0]} to {route[-1]}")

    async def setup(self):
        print(f"[{self.car_id}] CarAgent started.")
        b = self.CreateVehicleBehaviour()
        self.add_behaviour(b)
