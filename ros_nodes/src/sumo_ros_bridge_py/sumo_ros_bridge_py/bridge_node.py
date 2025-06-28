#!/usr/bin/env python3
import os
import sys
import rclpy
from rclpy.node import Node
import traci
from sumo_ros_bridge.msg import TrafficData
from ament_index_python.packages import get_package_share_directory
from sumo_ros_bridge.msg import LightCommand

class BridgeNode(Node):
    def __init__(self):
        super().__init__('bridge_node')
        
        sim_cfg_path = os.path.join(
            get_package_share_directory('sumo_ros_bridge_py'),
            'sim',
            'map.sumocfg'
        )
        self.declare_parameter('sumo_cfg_path', sim_cfg_path)
        self.declare_parameter('intersection_id', 'J4')
        
        self.publisher_ = self.create_publisher(TrafficData, '/traffic_data', 10)
        self.light_command_publisher = self.create_publisher(LightCommand, '/traffic_light_data', 10)
        
        self.command_subscriber_ = self.create_subscription(
            LightCommand,
            '/light_commands',
            self.handle_light_command,
            10)
        
        self.intersection_id = self.get_parameter('intersection_id').get_parameter_value().string_value
        
        # Add a parameter callback
        self.add_on_set_parameters_callback(self.parameter_callback)

        if not self.start_sumo():
            self.get_logger().error("Falha ao iniciar o SUMO. A desligar o nó.")
            self.destroy_node()
            return

        self.timer = self.create_timer(0.1, self.simulation_step)
        self.get_logger().info("Nó 'bridge_node' iniciado e conectado ao SUMO.")

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'intersection_id':
                self.intersection_id = param.value
                self.get_logger().info(f"Intersection ID updated to: {self.intersection_id}")
        return rclpy.parameter.ParameterValue()

    def handle_light_command(self, msg):
        self.get_logger().info(f'Recebido comando: ID={msg.traffic_light_id}, Estado={msg.new_state}')
        try:
            if msg.traffic_light_id in traci.trafficlight.getIDList():
                traci.trafficlight.setRedYellowGreenState(msg.traffic_light_id.strip(), msg.new_state.strip())
                self.get_logger().info(f"Estado do semáforo '{msg.traffic_light_id}' alterado para '{msg.new_state}'.")
            else:
                self.get_logger().warn(f"Semáforo com ID '{msg.traffic_light_id}' não encontrado na simulação.")

        except traci.TraCIException as e:
            self.get_logger().error(f"Erro no Traci ao tentar alterar o semáforo: {e}")

    def start_sumo(self):
        self.get_logger().info("A tentar iniciar o SUMO...")
        
        if 'SUMO_HOME' not in os.environ:
            self.get_logger().error("Por favor, defina a variável de ambiente 'SUMO_HOME'.")
            return False
        
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
        
        config_path = self.get_parameter('sumo_cfg_path').get_parameter_value().string_value
        if not os.path.exists(config_path):
            self.get_logger().error(f"Ficheiro de configuração do SUMO não encontrado em: {config_path}")
            return False

        sumo_cmd = ["sumo-gui", "--start", "-c", config_path]
        try:
            traci.start(sumo_cmd)
            return True
        except Exception as e:
            self.get_logger().error(f"Erro ao iniciar o SUMO: {e}")
            return False

    def simulation_step(self):
        try:
            # print(traci)
            traci.simulationStep()
            vehicle_count, vehicle_ids = self.get_vehicle_data(self.intersection_id)
            average_speed = self.get_average_speed(vehicle_ids)
            
            msg = TrafficData()
            msg.intersection_id = self.intersection_id
            msg.vehicle_count = vehicle_count
            msg.average_speed = average_speed
            msg.vehicle_ids = vehicle_ids
            msg.vehicle_types = [traci.vehicle.getTypeID(vid) for vid in vehicle_ids]
            msg.vehicle_speeds = [traci.vehicle.getSpeed(vid) for vid in vehicle_ids]
            msg.vehicle_accels = [traci.vehicle.getAccel(vid) for vid in vehicle_ids]
            msg.vehicle_decels = [traci.vehicle.getDecel(vid) for vid in vehicle_ids]
            msg.vehicle_distances = [traci.vehicle.getDistance(vid) for vid in vehicle_ids]
            msg.vehicle_waiting_times = [traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids]
            msg.vehicle_is_stopped = [traci.vehicle.isStopped(vid) for vid in vehicle_ids]
            msg.vehicle_positions = [str(traci.vehicle.getPosition(vid)) for vid in vehicle_ids]
            msg.vehicle_lane_ids = [traci.vehicle.getLaneID(vid) for vid in vehicle_ids]
            msg.vehicle_road_ids = [traci.vehicle.getRoadID(vid) for vid in vehicle_ids]
            
            self.publisher_.publish(msg)

            ## light command publisher
            light_command_msg = LightCommand()
            light_command_msg.traffic_light_id = self.intersection_id
            light_command_msg.new_state = traci.trafficlight.getRedYellowGreenState(self.intersection_id)
            self.light_command_publisher.publish(light_command_msg)

            self.get_logger().info(
                f'Published: id={msg.intersection_id}, count={msg.vehicle_count}, speed={msg.average_speed:.2f} m/s, '
                f'Vehicle IDs: {msg.vehicle_ids}, '
                f'Vehicle Types: {msg.vehicle_types}, '
                f'Vehicle Speeds: {msg.vehicle_speeds}, '
                f'Vehicle Accels: {msg.vehicle_accels}, '
                f'Vehicle Decels: {msg.vehicle_decels}, '
                f'Vehicle Distances: {msg.vehicle_distances}'
            )

        except Exception as e:
            self.get_logger().error(f"Exception in simulation_step: {e}")
            self.destroy_node()

    def get_vehicle_data(self, junction_id):
        try:
            all_vehicle_ids = set()
            lane_ids = traci.trafficlight.getControlledLanes(junction_id)
            for lane_id in lane_ids:
                vehicles_on_lane = traci.lane.getLastStepVehicleIDs(lane_id)
                all_vehicle_ids.update(vehicles_on_lane)
            return len(all_vehicle_ids), list(all_vehicle_ids)
        except Exception as e:
            self.get_logger().error(f"Error in get_vehicle_data: {e}")
            return 0, []

    def get_average_speed(self, vehicle_ids):
        if not vehicle_ids:
            return 0.0
        
        total_speed = 0.0
        for vehicle_id in vehicle_ids:
            total_speed += traci.vehicle.getSpeed(vehicle_id)
            
        return total_speed / len(vehicle_ids)

    def destroy_node(self):
        self.get_logger().info("A fechar a conexão com o SUMO...")
        traci.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = BridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 