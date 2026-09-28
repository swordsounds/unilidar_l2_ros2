# Unitree L2 ROS 2 workspace

This workspace contains the Unitree L2 SDK examples and the `unitree_lidar_ros2` driver. The bundled ROS 1 package is excluded from `colcon` discovery with `COLCON_IGNORE`.

## Build on ROS 2 Humble or Jazzy

Install the ROS 2 distribution for your operating system, then run from this directory:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

If `ROS_DISTRO` is unset, source the intended distribution explicitly, for example `source /opt/ros/humble/setup.bash` or `source /opt/ros/jazzy/setup.bash`.

The bundled static SDK libraries support `x86_64` and `aarch64`. The CMake build reports an error for other architectures.

## Run

The launch file defaults to Ethernet UDP, the mode that was verified to publish both point clouds and IMU data on this host. Connect the LiDAR at `192.168.1.62` through the Ethernet adapter configured as `192.168.1.2/24`, then run:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

To use serial after the LiDAR has been confirmed in UART output mode, use the supplied adapter and run:

```bash
ros2 launch unitree_lidar_ros2 launch.py initialize_type:=1 work_mode:=8
```

The serial launch argument defaults to this host's stable device path, `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A64010467-if00`, at 4,000,000 baud. For a different serial device, add `serial_port:=/dev/ttyACM0` or its actual path.

The launch file starts the LiDAR node and RViz. The node can also be run directly with ROS parameters. The direct-node defaults remain UDP:

```bash
ros2 run unitree_lidar_ros2 unitree_lidar_ros2_node --ros-args -p local_ip:=192.168.1.2 -p lidar_ip:=192.168.1.62
```

The node publishes `unilidar/cloud` and `unilidar/imu`. A live Ethernet test on this host received messages on both topics with frames `unilidar_lidar` and `unilidar_imu`.

The driver publishes the fixed IMU-to-LiDAR transform at startup, so RViz can resolve `unilidar_lidar` before the first sensor packet. If no cloud or IMU data arrives, the node logs a connection warning after about ten seconds. A valid frame alone does not mean sensor data is arriving. Check with `ros2 topic hz /unilidar/cloud` and `ros2 topic hz /unilidar/imu`.

### First-time switch from Ethernet to serial

Unitree documents that the L2 ships in Ethernet mode. A USB serial cable alone cannot make a factory-mode LiDAR send serial data. Connect the LiDAR by Ethernet to a host with an Ethernet port or USB Ethernet adapter. Set that host interface to `192.168.1.2/24` and leave the LiDAR at its factory address `192.168.1.62`. Then, from this workspace, run:

```bash
./install/unitree_lidar_sdk/bin/set_to_serial_mode
```

The utility waits for a valid Ethernet packet before sending work mode `8`. If the LiDAR has a custom address, pass both addresses as `set_to_serial_mode <lidar_ip> <host_ip>`. After the utility says the command was sent, **power cycle the LiDAR**, connect its serial cable, and use the explicit serial launch command above. You can also use Unitree's host configuration software to set serial mode. If the utility reports no packets, check power, Ethernet cabling, host IP, and the LiDAR's actual IP before retrying.

If the LiDAR answers ping at its configured IP but sends no Ethernet stream, the utility can still send the mode command with `./install/unitree_lidar_sdk/bin/set_to_serial_mode --force`. This bypasses the packet check and **does not confirm that the LiDAR accepted the command**. Power cycle afterward and verify serial data. Use this only after checking the LiDAR IP, host IP, cabling, and power.

Repeated `Serial port timeout!` messages mean that the port opened but the driver received no valid serial data. Confirm the Ethernet-to-serial switch and power cycle first. If it still times out afterward, check the cable, actual device path, baud rate, and LiDAR power. The static TF can appear in RViz even while no cloud data is arriving.

On this host, a direct five-second read from the supplied Unitree UART adapter at 4,000,000 baud returned zero bytes even after the `--force` command and a full power cycle. A later Ethernet test received 2,261 packets from `192.168.1.62:6101` in five seconds, and ROS published both cloud and IMU messages in UDP mode. The LiDAR is therefore currently working over Ethernet. Because the earlier `--force` command has no device acknowledgement, verify any future switch to UART with Unitree's [Unilidar 2 Windows application](https://oss-global-cdn.unitree.com/static/Unilidar_2_V1.21.exe): select **UART** under **ENET/UART Select**, click **SetMode**, confirm success, and click **Restart**. Unitree publishes the executable on its [L2 download page](https://www.unitree-robot.com/download/L2/) and documents Windows 64-bit support; it cannot be installed natively on this Ubuntu host.

## RViz and Snap library paths

If a terminal environment makes RViz load libraries from `/snap/core20`, RViz can fail with an `__libc_pthread_init` symbol error. On this machine, a terminal inherited `GIO_MODULE_DIR` from Snap-installed VS Code; that directory contained modules linked against `/snap/core20` libraries. The launch file gives RViz an explicit copy of the host environment with Snap paths, including paths under `~/snap`, and Snap-specific variables removed. It retains ROS and host paths and logs the names of variables it cleaned. The Wayland `XDG_SESSION_TYPE` warning by itself is not the crash.

# unilidar_l2_ros2
Reconciled
