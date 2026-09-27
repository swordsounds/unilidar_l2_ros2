cmake_minimum_required(VERSION 3.10)
project(unitree_lidar_ros2)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(sensor_msgs REQUIRED)

set(UNITREE_SDK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../unitree_lidar_sdk")
set(UNITREE_SDK_INCLUDE_DIR "${UNITREE_SDK_ROOT}/include")
set(UNITREE_SDK_LIBRARY
  "${UNITREE_SDK_ROOT}/lib/${CMAKE_SYSTEM_PROCESSOR}/libunilidar_sdk2.a")
if(NOT EXISTS "${UNITREE_SDK_LIBRARY}")
  message(FATAL_ERROR "No Unitree SDK library for ${CMAKE_SYSTEM_PROCESSOR}: ${UNITREE_SDK_LIBRARY}")
endif()

include_directories(
  include
  ${PCL_INCLUDE_DIRS}
  ${UNITREE_SDK_INCLUDE_DIR}
)

link_directories(
  ${PCL_LIBRARY_DIRS}
)

add_definitions(${PCL_DEFINITIONS})

add_executable(unitree_lidar_ros2_node src/unitree_lidar_ros2_node.cpp)

target_link_libraries(unitree_lidar_ros2_node
  ${PCL_LIBRARIES}
  ${UNITREE_SDK_LIBRARY}
)

ament_target_dependencies(
  unitree_lidar_ros2_node
  rclcpp std_msgs 
  sensor_msgs
  geometry_msgs 
  tf2_ros
  pcl_conversions
)

install(TARGETS unitree_lidar_ros2_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY rviz launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
