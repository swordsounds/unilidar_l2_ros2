cmake_minimum_required(VERSION 3.10)
project(unitree_lidar_sdk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(UNITREE_SDK_LIBRARY
  "${CMAKE_CURRENT_SOURCE_DIR}/lib/${CMAKE_SYSTEM_PROCESSOR}/libunilidar_sdk2.a")
if(NOT EXISTS "${UNITREE_SDK_LIBRARY}")
  message(FATAL_ERROR "No Unitree SDK library for ${CMAKE_SYSTEM_PROCESSOR}: ${UNITREE_SDK_LIBRARY}")
endif()

add_library(unilidar_sdk2 STATIC IMPORTED)
set_target_properties(unilidar_sdk2 PROPERTIES
  IMPORTED_LOCATION "${UNITREE_SDK_LIBRARY}"
  INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_SOURCE_DIR}/include")

foreach(example IN ITEMS example_lidar_udp example_lidar_serial
    set_ip_address set_to_serial_mode set_to_udp_mode)
  add_executable(${example} "examples/${example}.cpp")
  target_link_libraries(${example} PRIVATE unilidar_sdk2)
endforeach()

install(TARGETS example_lidar_udp example_lidar_serial
  set_ip_address set_to_serial_mode set_to_udp_mode
  RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
install(FILES "${UNITREE_SDK_LIBRARY}" DESTINATION lib)
