import json
import random
import asyncio
import math
from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from traffic_management.agents.base import BaseAgent
from traffic_management.agents.utils import (
    get_random_sumo_position,
)
from traffic_management.contact_book import (
    MEDICAL_AGENTS,
    POLICE_AGENTS,
    EMERGENCY_AGENTS,
)


class EmergencyRequestMessage(Template):
    def __init__(self):
        super().__init__()
        self.set_metadata("performative", "request")
        self.set_metadata("type", "emergency_request")

    @classmethod
    def build_message(
        cls, to, location: tuple[float, float], emergency_type: str
    ) -> Message:
        msg = Message(
            to=to, body=json.dumps({"location": location, "type": emergency_type})
        )
        msg.set_metadata("performative", "request")
        msg.set_metadata("type", "emergency_request")
        return msg


class AmbulanceDistanceMessage(Template):
    def __init__(self):
        super().__init__()
        self.set_metadata("performative", "inform")
        self.set_metadata("type", "ambulance_distance")

    @classmethod
    def build_message(cls, to, distance: float) -> Message:
        msg = Message(to=to, body=json.dumps({"distance": distance}))
        msg.set_metadata("performative", "inform")
        msg.set_metadata("type", "ambulance_distance")
        return msg


class EmergencyDispatchAgent(BaseAgent):
    def __init__(self, id: str, random_seed: tuple[float, float] = (5, 15)):
        self.random_seed = random_seed
        super().__init__(id=id)

    class EmergencyRequestBehaviour(CyclicBehaviour):
        async def run(self):
            delay = random.uniform(*self.agent.random_seed)
            await asyncio.sleep(delay)

            emergency_location = get_random_location()
            emergency_type = random.choice(["medical", "police"])

            for agent in EMERGENCY_AGENTS:
                msg = EmergencyRequestMessage.build_message(
                    to=f"{agent}@{self.agent.jid.domain}",
                    location=emergency_location,
                    emergency_type=emergency_type,
                )
                await self.send(msg)
            print(
                f"[{self.agent.name}] New {emergency_type} emergency request at {emergency_location} dispatched."
            )

    async def setup(self):
        print(f"[{self.name}] Emergency dispatch agent started.")
        self.add_behaviour(self.EmergencyRequestBehaviour())


class AmbulanceAgent(BaseAgent):
    def __init__(self, id: str):
        self.on_call = False
        self.location = None
        super().__init__(id=id)

    class HandleEmergencyRequestBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                data = json.loads(msg.body)
                if data.get("type") != "medical":
                    return
                self.agent.emergency_location = data.get("location")
                self.agent.distance_to_emergency = math.dist(
                    self.agent.location, self.agent.emergency_location
                )
                self.agent.add_behaviour(self.agent.CoordinateResponseBehaviour())

    class CoordinateResponseBehaviour(OneShotBehaviour):
        async def run(self):
            for peer in MEDICAL_AGENTS:
                msg = AmbulanceDistanceMessage.build_message(
                    to=f"{peer}@{self.agent.jid.domain}",
                    distance=self.agent.distance_to_emergency,
                )
                await self.send(msg)

            min_distance = self.agent.distance_to_emergency
            closest_agent = self.agent.jid
            for _ in MEDICAL_AGENTS:
                msg = await self.receive(timeout=5)
                if msg:
                    distance = json.loads(msg.body).get("distance", float("inf"))
                    if distance < min_distance:
                        min_distance = distance
                        closest_agent = msg.sender

            if closest_agent == self.agent.jid:
                print(
                    f"[{self.agent.name}] I am the closest ambulance to the emergency."
                )
                self.agent.on_call = True
                self.agent.location = self.agent.emergency_location

    def add_to_sumo(self):
        try:
            self.sumo_conn.vehicle.add(
                vehID=self.jid.local,
                routeID="",
                typeID="ambulance",
            )
            print(f"[{self.name}] Ambulance added to SUMO.")
        except Exception as e:
            print(f"[{self.name}] Error adding ambulance to SUMO: {e}")

    async def setup(self):
        self.connect_to_sumo()
        # self.location = get_random_sumo_position(self.sumo_conn)
        self.add_to_sumo()
        print(f"[{self.name}] Ambulance agent started at location {self.location}.")
        self.add_behaviour(
            self.HandleEmergencyRequestBehaviour(), EmergencyRequestMessage()
        )


class PoliceAgent(BaseAgent):
    def __init__(self, id: str):
        super().__init__(id=id)

    class HandleEmergencyRequestBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                data = json.loads(msg.body)
                if data.get("type") != "police":
                    return
                self.agent.emergency_location = data.get("location")
                self.agent.distance_to_emergency = math.dist(
                    self.agent.location, self.agent.emergency_location
                )
                self.agent.add_behaviour(self.agent.CoordinateResponseBehaviour())

    class CoordinateResponseBehaviour(OneShotBehaviour):
        async def run(self):
            for peer in POLICE_AGENTS:
                msg = AmbulanceDistanceMessage.build_message(
                    to=f"{peer}@{self.agent.jid.domain}",
                    distance=self.agent.distance_to_emergency,
                )
                await self.send(msg)

            min_distance = self.agent.distance_to_emergency
            closest_agent = self.agent.jid
            for _ in POLICE_AGENTS:
                msg = await self.receive(timeout=5)
                if msg:
                    distance = json.loads(msg.body).get("distance", float("inf"))
                    if distance < min_distance:
                        min_distance = distance
                        closest_agent = msg.sender

            if closest_agent == self.agent.jid:
                print(f"[{self.agent.name}] I am the closest police to the emergency.")
                self.agent.on_call = True
                self.agent.location = self.agent.emergency_location

    async def setup(self):
        self.on_call = False
        self.location = get_random_location()
        print(f"[{self.name}] Police agent started at location {self.location}.")
        self.add_behaviour(
            self.HandleEmergencyRequestBehaviour(), EmergencyRequestMessage()
        )
