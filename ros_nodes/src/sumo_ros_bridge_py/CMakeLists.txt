cmake_minimum_required(VERSION 3.8)
project(sumo_ros_bridge_py)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(sumo_ros_bridge REQUIRED)

ament_python_install_package(sumo_ros_bridge_py)

install(PROGRAMS
  sumo_ros_bridge_py/bridge_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  sumo_ros_bridge_py/traffic_data_subscriber.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY sim/
  DESTINATION share/${PROJECT_NAME}/sim
)

ament_package()
