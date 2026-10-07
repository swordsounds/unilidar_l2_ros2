import os
import re

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.logging import get_logger
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    initialize_type = LaunchConfiguration('initialize_type')
    work_mode = LaunchConfiguration('work_mode')
    serial_port = LaunchConfiguration('serial_port')
    baudrate = LaunchConfiguration('baudrate')

    # Run unitree lidar
    node1 = Node(
        package='unitree_lidar_ros2',
        executable='unitree_lidar_ros2_node',
        name='unitree_lidar_ros2_node',
        output='screen',
        parameters= [
                
                {'initialize_type': ParameterValue(initialize_type, value_type=int)},
                {'work_mode': ParameterValue(work_mode, value_type=int)},
                {'use_system_timestamp': True},
                {'range_min': 0.0},
                {'range_max': 100.0},
                {'cloud_scan_num': 18},

                {'serial_port': serial_port},
                {'baudrate': ParameterValue(baudrate, value_type=int)},

                {'lidar_port': 6101},
                {'lidar_ip': '192.168.1.62'},
                {'local_port': 6201},
                {'local_ip': '192.168.1.2'},
                
                {'cloud_frame': "unilidar_lidar"},
                {'cloud_topic': "unilidar/cloud"},
                {'imu_frame': "unilidar_imu"},
                {'imu_topic': "unilidar/imu"},
                ]
    )

    # Run Rviz
    rviz_config_file = os.path.join(
        get_package_share_directory('unitree_lidar_ros2'), 'rviz', 'view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='log'
    )
    return LaunchDescription([
        DeclareLaunchArgument('initialize_type', default_value='2',
                              description='1 for serial, 2 for UDP'),
        DeclareLaunchArgument('work_mode', default_value='0',
                              description='8 for serial, 0 for UDP'),
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A64010467-if00'),
        DeclareLaunchArgument('baudrate', default_value='4000000'),
        node1,
        rviz_node,
    ])
