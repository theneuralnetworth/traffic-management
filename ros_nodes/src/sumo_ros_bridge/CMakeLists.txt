cmake_minimum_required(VERSION 3.8)
project(sumo_ros_bridge)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TrafficData.msg"
)

ament_package()