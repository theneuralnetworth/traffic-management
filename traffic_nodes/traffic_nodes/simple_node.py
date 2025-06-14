import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SimpleNode(Node):
    def __init__(self):
        super().__init__("simple_node")
        self.subscription = self.create_subscription(
            String, "topic", self.listener_callback, 10
        )
        self.get_logger().info(
            "SimpleNode has been started and is listening to 'topic'."
        )

    def listener_callback(self, msg):
        self.get_logger().info(
            f"Received message: '{msg.data}' from topic '{msg._topic_name}'"
        )


def main(args=None):
    rclpy.init(args=args)
    node = SimpleNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
