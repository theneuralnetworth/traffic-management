#!/usr/bin/env python3
import sys
import asyncio
from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String as RosString

from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

from credentials import AGENTS

class LightState(Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    NONE = "none"

class TrafficLightAgent(Agent, Node):
    def __init__(self, jid: str, password: str):
        rclpy.init(args=None)
        Node.__init__(self, "traffic_light_agent_node")
        super().__init__(jid=jid, password=password)

        self.ros_pub = self.create_publisher(RosString, "/stop_light/color", 10)
        self.light_state = LightState.NONE
        self.add_behaviour(self.ControlLightBehaviour(period=5))

    class ControlLightBehaviour(PeriodicBehaviour):
        async def run(self):
            next_state = {
                LightState.NONE: LightState.RED,
                LightState.RED: LightState.GREEN,
                LightState.GREEN: LightState.YELLOW,
                LightState.YELLOW: LightState.RED,
            }[self.agent.light_state]

            self.agent.set_light_state(next_state)
            print(f"[{self.agent.name}] Light changed to {next_state.value}")

    def set_light_state(self, state: LightState):
        self.light_state = state
        msg = RosString()
        msg.data = state.value
        self.ros_pub.publish(msg)

    async def setup(self):
        print(f"[{self.name}] started")

    def stop(self):
        super().stop()
        rclpy.shutdown()


if __name__ == "__main__":
    creds = AGENTS["Semaphores"]["semaphore_0"]
    jid = creds["email"]
    pwd = creds["password"]

    agent = TrafficLightAgent(jid, pwd)
    future = agent.start(auto_register=True)

    asyncio.get_event_loop().run_until_complete(future)
    print("Agent running")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass

    agent.stop()
