#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sumo_ros_bridge.msg import TrafficData, LightCommand
import paho.mqtt.publish as publish

class TrafficDataSubscriber(Node):
    def __init__(self):
        super().__init__('traffic_data_subscriber')
        self.subscription = self.create_subscription(
            TrafficData,
            '/traffic_data',
            self.listener_callback,
            10)
        self.subscription
        ## traffic light state sub
        self.light_command_subscription = self.create_subscription(
            LightCommand,
            '/traffic_light_data',
            self.traffic_light_data_listener_callback,
            10)
       

    def listener_callback(self, msg):
        self.get_logger().info(f'Received data: id={msg.intersection_id}, count={msg.vehicle_count}, speed={msg.average_speed:.2f} m/s')
        for i, vid in enumerate(msg.vehicle_ids):
            self.get_logger().info(f'Vehicle {vid}: Type={msg.vehicle_types[i]}, Speed={msg.vehicle_speeds[i]}, Accel={msg.vehicle_accels[i]}, Decel={msg.vehicle_decels[i]}, Distance={msg.vehicle_distances[i]}, WaitingTime={msg.vehicle_waiting_times[i]}, IsStopped={msg.vehicle_is_stopped[i]}, Position={msg.vehicle_positions[i]}, LaneID={msg.vehicle_lane_ids[i]}, RoadID={msg.vehicle_road_ids[i]}')

        # Log summary of received data
        self.get_logger().info(f'Total vehicles: {len(msg.vehicle_ids)}, Average speed: {msg.average_speed:.2f} m/s')
    
    def traffic_light_data_listener_callback(self, msg):
        new_state = str(msg.new_state).upper()[0]
        self.get_logger().info(f'Received traffic light data_: id={msg.traffic_light_id}, state={msg.new_state}_{new_state}')
        new_state = str(msg.new_state).upper()[0]
        publish.single("esp32/traffic_light", new_state, hostname="192.168.1.100")  # Use your broker's IP
        

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
