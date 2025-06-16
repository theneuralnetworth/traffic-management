#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sumo_ros_bridge.msg import TrafficData

class TrafficDataSubscriber(Node):
    def __init__(self):
        super().__init__('traffic_data_subscriber')
        self.subscription = self.create_subscription(
            TrafficData,
            '/traffic_data',
            self.listener_callback,
            10)
        self.subscription

    def listener_callback(self, msg):
        self.get_logger().info(f'Received data: id={msg.intersection_id}, count={msg.vehicle_count}, speed={msg.average_speed:.2f} m/s')
        for i, vid in enumerate(msg.vehicle_ids):
            self.get_logger().info(f'Vehicle {vid}: Type={msg.vehicle_types[i]}, Speed={msg.vehicle_speeds[i]}, Accel={msg.vehicle_accels[i]}, Decel={msg.vehicle_decels[i]}, Distance={msg.vehicle_distances[i]}, WaitingTime={msg.vehicle_waiting_times[i]}, IsStopped={msg.vehicle_is_stopped[i]}, Position={msg.vehicle_positions[i]}, LaneID={msg.vehicle_lane_ids[i]}, RoadID={msg.vehicle_road_ids[i]}')

        # Log summary of received data
        self.get_logger().info(f'Total vehicles: {len(msg.vehicle_ids)}, Average speed: {msg.average_speed:.2f} m/s')

def main(args=None):
    rclpy.init(args=args)
    node = TrafficDataSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 