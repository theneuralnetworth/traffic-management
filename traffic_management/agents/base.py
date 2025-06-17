import os
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import paho.mqtt.client as mqtt


class BaseAgent(Agent):
    def __init__(self, id: str, password: str = "password"):
        self.server = os.getenv("XMPP_HOST", "localhost")
        jid = f"{id}@{self.server}"
        super().__init__(jid=jid, password=password)

    class ClockTickReceiveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if msg and msg.metadata.get("type") == "clock_tick":
                print(f"[{self.agent.name}] Received clock tick")

    def on_mqtt_connect(self, client, userdata, flags, rc, properties):
        print(f"[{self.jid}] Connected to MQTT broker")

    def on_mqtt_message(self, client, userdata, msg):
        print(f"[{self.jid}] Received MQTT message on topic {msg.topic}")

    def setup_mqtt(self):
        MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
        MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.jid.local)
        self.mqtt.on_connect = self.on_mqtt_connect
        self.mqtt.on_message = self.on_mqtt_message

        self.mqtt.connect(MQTT_HOST, MQTT_PORT, 60)
