# Multi-Agent Traffic Light Controller with SUMO, ROS2, and SPADE

## Project Overview

This project aims to build an intelligent traffic light control system using a distributed multi-agent setup. The system dynamically adjusts traffic light states based on real-time simulation data from SUMO. It is modular, extensible, and based on ROS 2 for integration with IoT systems.

## Core Components

### 1. sumo_ros_bridge

- **Purpose:** Acts as a bridge between SUMO and ROS2 using Traci.
- **Functionality:** Parses simulation data (like vehicle count or positions) and publishes it to ROS2 topics for other agents to consume.
- **Executables:** `bridge_node`, `traffic_data_subscriber`.

### 2. decision_publisher

- **Purpose:** SPADE-based agent system that subscribes to ROS2 data from SUMO.
- **Functionality:** Makes decisions (e.g., when to switch traffic lights) and publishes commands to ROS2 topics for SUMO to consume.


## Nodes

### 1. `bridge_node`

- **Role:** Acts as a bridge between SUMO and ROS 2.
- **Topics Published:**
  - `/traffic_data` (Type: `TrafficData`)
- **Topics Subscribed:**
  - `/light_commands` (Type: `LightCommand`)

### 2. `traffic_data_subscriber`

- **Role:** Subscribes to the `/traffic_data` topic to receive and log traffic data.
- **Topics Subscribed:**
  - `/traffic_data` (Type: `TrafficData`)

## Topics

### 1. `/traffic_data`

- **Type:** `TrafficData`
- **Publisher:** `bridge_node`
- **Subscriber:** `traffic_data_subscriber`

### 2. `/light_commands`

- **Type:** `LightCommand`
- **Publisher:** SPADE agents or other nodes
- **Subscriber:** `bridge_node`

## Message Types

### 1. `TrafficData`

- **Fields:**
  - `string intersection_id`
  - `int32 vehicle_count`
  - `float32 average_speed`
  - `string[] vehicle_ids`
  - `string[] vehicle_types`
  - `float32[] vehicle_speeds`
  - `float32[] vehicle_accels`
  - `float32[] vehicle_decels`
  - `float32[] vehicle_distances`
  - `float32[] vehicle_waiting_times`
  - `bool[] vehicle_is_stopped`
  - `string[] vehicle_positions`
  - `string[] vehicle_lane_ids`
  - `string[] vehicle_road_ids`

### 2. `LightCommand`

- **Fields:**
  - `string traffic_light_id`
  - `string new_state`

## How to Use

1. **Setup Environment:**

   - Ensure ROS 2 and SUMO are installed and configured.
   - Set the `SUMO_HOME` environment variable. This variable should point to the root directory of your SUMO installation, which contains subdirectories like `bin`, `tools`, and `data`. For example, if SUMO is installed in `/usr/local/share/sumo`, set it using:
     ```bash
     export SUMO_HOME=/usr/local/share/sumo
     ```
   - To make this change permanent, add the export command to your shell's configuration file (e.g., `.bashrc`, `.zshrc`).
   - Verify the setting by running:
     ```bash
     echo $SUMO_HOME
     ```

2. **Build the Packages:**

   - Navigate to the root of your workspace:
     ```bash
     cd ros_nodes
     ```
   - Build the packages using `colcon`:
     ```bash
     colcon build --packages-select sumo_ros_bridge sumo_ros_bridge_py
     ```

3. **Source the Workspace:**

   - After building, source the setup file to update your environment:
     ```bash
     source install/setup.bash
     ```

4. **Run the Nodes:**

   - Open a terminal and navigate to the `sumo_ros_bridge_py` package directory:
     ```bash
     cd src/sumo_ros_bridge_py
     ```
   - Run the `bridge_node.py`:

     ```bash
     ros2 run sumo_ros_bridge_py bridge_node.py
     ```

   - Open another terminal for the `traffic_data_subscriber` or any other node you wish to run, and repeat the sourcing step:
     ```bash
     source install/setup.bash
     ```
   - Navigate to the appropriate package directory and run the node:
     ```bash
     ros2 run sumo_ros_bridge_py traffic_data_subscriber.py
     ```

5. **Monitor and Control:**

   - Use the `traffic_data_subscriber` to monitor traffic data.
   - Use SPADE agents to publish commands to the `/light_commands` topic to control traffic lights.

## Notes

- The system is designed to be scalable and can handle multiple intersections by configuring the intersection ID parameter.
- Error handling and logging are implemented to ensure robustness and provide insights into system operations.

## Future Enhancements

- Integration with real-world IoT devices for enhanced data collection and decision-making.
- Implementation of advanced decision-making algorithms, such as reinforcement learning, for traffic optimization.
