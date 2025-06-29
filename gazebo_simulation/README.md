# Instructions to Run Gazebo + ROS 2

First, navigate to your workspace folder:

```bash
cd gazebo_simulation/ros2_ws
```

---

## Terminal 1

1. Source the ROS 2 Humble environment:
   ```bash
   source /opt/ros/humble/setup.bash
   ```
2. Source your workspace overlay:
   ```bash
   source install/setup.bash
   ```
3. Build only the traffic light control package:
   ```bash
   colcon build --packages-select traffic_light_control
   ```
4. Launch Gazebo with the traffic world:
   ```bash
   gazebo --verbose src/traffic_light_control/worlds/traffic_world.world
   ```

---

## Terminal 2

1. Source the ROS 2 Humble environment:
   ```bash
   source /opt/ros/humble/setup.bash
   ```
2. Source your workspace overlay:
   ```bash
   source install/setup.bash
   ```
3. Publish light change command (e.g. change light 2 to red):
   ```bash
   ros2 topic pub -1 /light_commands traffic_light_control/msg/LightCommand \ "{traffic_light_id: '2', new_state: 'red'}"
   ```
