import os
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import paho.mqtt.client as mqtt


class BaseAgent(Agent):
    def __init__(self, id: str, password: str = "password"):
        self.server = os.getenv("XMPP_HOST", "localhost")
        jid = f"{id}@{self.server}"
        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        super().__init__(jid=jid, password=password)

    class ClockTickReceiveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if msg and msg.metadata.get("type") == "clock_tick":
                print(f"[{self.agent.name}] Received clock tick")

    def setup_mqtt_client(self):
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message
        self.mqtt.connect("localhost", 1883, 60)
        self.mqtt.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[{self.jid}] Connected to MQTT broker with result code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"[{self.jid}] Received MQTT message: {msg.topic} {msg.payload.decode()}")
