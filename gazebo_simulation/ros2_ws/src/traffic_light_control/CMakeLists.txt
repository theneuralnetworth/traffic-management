cmake_minimum_required(VERSION 3.8)
project(traffic_light_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(gazebo REQUIRED)
find_package(ament_index_cpp REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(
  include
  ${GAZEBO_INCLUDE_DIRS}
)

add_library(traffic_light_plugin SHARED
  src/traffic_light_plugin.cpp
)

ament_target_dependencies(traffic_light_plugin
  rclcpp
  std_msgs
  gazebo_ros
)

target_link_libraries(traffic_light_plugin
  ${GAZEBO_LIBRARIES}
)

install(
  TARGETS traffic_light_plugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib
)

ament_package()
