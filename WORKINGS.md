# ROS 2 Humble and Jazzy workspace repair: working notes

## Current outcome and reasons for the fixes

| Area | Change | Reason and observed result |
| --- | --- | --- |
| Humble/Jazzy build layout | Corrected the driver SDK path, selected the bundled library by CPU architecture, repaired the standalone SDK CMake file, excluded the nested ROS 1 package, and declared resolvable dependencies. | The old paths and missing CMake template prevented normal `colcon` builds. Both ROS 2 packages built on Humble; Jazzy is not installed here. |
| RViz startup | Resolved the installed RViz configuration path and removed Snap library/plugin paths from RViz's launch environment. | A Snap `libpthread` caused RViz to exit with a loader error. The user later confirmed RViz started successfully. |
| Frames and IMU | Published the fixed IMU-to-LiDAR transform at startup; corrected IMU quaternion order and stopped reading the same IMU sample twice. | RViz previously reported that `unilidar_lidar` did not exist when no sensor packets arrived. The static frame is now available independently of packets. |
| Network and serial setup | Added configurable serial/UDP launch arguments, corrected factory IP defaults, made the serial switch utility distinguish a command sent from a confirmed mode change, and added no-data warnings. | The supplied UART adapter opened but delivered zero bytes. A forced mode command had no acknowledgement. |
| Working live transport | Set the launch default back to Ethernet UDP (`initialize_type=2`, `work_mode=0`). | The host received 2,261 packets from `192.168.1.62:6101` in five seconds and ROS published one observed cloud and IMU message through Ethernet. |
| Unilidar 2 under Wine | Documented that its **Select UDP IP** list contained only `127.0.1.1` in the supplied screenshot. | That field selects the host address; Wine did not list the host's `192.168.1.2`. The native Linux ROS driver communicates successfully, so this Wine screen does not indicate a LiDAR network failure. |

Primary references: [Unitree L2 SDK and work modes](https://github.com/unitreerobotics/unilidar_sdk2), [Unitree L2 network and serial specifications](https://oss-global-cdn.unitree.com/static/Unitree%204D%20LiDAR%20L2%20User%20Manual.pdf), [Unilidar 2 connection and mode instructions](https://oss-global-cdn.unitree.com/static/Unilidar%202%20User%20Manual.pdf), and [Unitree SDK releases](https://github.com/unitreerobotics/unilidar_sdk2/releases). The measured packet count, ROS topic messages, build results, and screenshot finding are observations from this machine rather than claims from those documents.

## Scope and layout

This directory is a `colcon` workspace. Its source tree contains the ROS 2 driver at `src/unitree_lidar_ros2/src/unitree_lidar_ros2`, the standalone SDK and examples at `src/unitree_lidar_sdk`, and a nested upstream checkout at `src/unilidar_sdk2` that contains a ROS 1 package. Only ROS 2 Humble is installed on this machine, so the changes were built and checked with Humble. Jazzy compatibility is the target of the build changes, but a Jazzy build and hardware run remain unverified.

## What was broken

The earlier build logs in `log/build_2026-09-10_19-03-52` showed two independent failures:

1. The ROS 2 package looked for the SDK headers and `libunilidar_sdk2.a` under `../unitree_lidar_sdk` relative to its own package directory. That resolves inside `src/unitree_lidar_ros2/src`, where the SDK does not exist. The compiler consequently could not find `unitree_lidar_sdk_pcl.h`, and the linker had no rule for the nonexistent library path.
2. The standalone SDK CMake file tried to configure `unitree_lidar_sdkConfig.cmake.in`, but that template was absent. This prevented the SDK package from configuring in a normal workspace build.

`colcon list --base-paths src` also found the nested ROS 1 `unitree_lidar_ros` package. Including that Catkin package in the same default build would make this ROS 2 workspace harder to build consistently.

The node's direct-run UDP defaults had the host and LiDAR addresses reversed relative to the SDK's `example_lidar_udp.cpp`. The launch file already used the correct defaults: LiDAR `192.168.1.62`, host `192.168.1.2`.

## Changes made

### ROS 2 driver build

In `src/unitree_lidar_ros2/src/unitree_lidar_ros2/CMakeLists.txt`, `UNITREE_SDK_ROOT` now points three directory levels up and then into `unitree_lidar_sdk`. The SDK include directory and archive are derived from that root. The archive path uses `${CMAKE_SYSTEM_PROCESSOR}`, selecting the bundled `x86_64` or `aarch64` library for the current machine. CMake stops with a clear error if that archive is missing. The package still links the SDK archive and PCL libraries into `unitree_lidar_ros2_node`, and installs the executable, launch file, and RViz configuration.

The `target_link_libraries` call uses the plain CMake signature because Humble's `ament_target_dependencies` also calls `target_link_libraries` using that signature. Mixing `PRIVATE` with the plain signature caused a CMake configure error during the first repair build; the final build has no such error.

### Standalone SDK build

In `src/unitree_lidar_sdk/CMakeLists.txt`, the SDK archive is represented as an imported static library with its headers as an interface include directory. The five SDK example programs link against that target. The examples, headers, and archive are installed once each. The broken reference to the nonexistent CMake config template was removed. C++17 is set through CMake's standard variables, and an unsupported processor produces a clear error.

### Package discovery and dependencies

`src/unilidar_sdk2/COLCON_IGNORE` excludes the nested upstream ROS 1 checkout from `colcon` package discovery. The upstream files remain available for reference. After this change, `colcon list --base-paths src` reports only `unitree_lidar_ros2` and `unitree_lidar_sdk`.

In the ROS 2 `package.xml`, the PCL dependency uses the resolvable rosdep key `libpcl-all-dev`. The launch file's runtime dependencies on `ament_index_python` and `rviz2` are declared. On the Humble machine, `rosdep resolve libpcl-all-dev` mapped to the `libpcl-dev` system package, and `rosdep check --from-paths src --ignore-src` reported all system dependencies satisfied.

### Launch and runtime data

The launch file now gets its installed share directory through `ament_index_python` and loads `rviz/view.rviz` from the actual installed location. Previously it invoked a `ros2 pkg prefix` subprocess and constructed a path that omitted the `rviz` directory. The launch file retains the SDK example's UDP defaults: LiDAR `192.168.1.62`, host `192.168.1.2`.

In the node, the direct-run UDP defaults now match those launch defaults. The IMU callback calls `getImuData` once rather than consuming it twice. The published IMU orientation and TF rotation now use the same `(x, y, z, w)` index order documented by the bundled SDK example. The dynamic TF uses the IMU sample timestamp, matching the IMU message, rather than the wall clock at publication time. These runtime changes compile but still require LiDAR data to verify their behavior.

`README.md` was added at the workspace root with dependency installation, build, launch, default network settings, and direct-node commands.

## Verification performed

The following checks completed on ROS 2 Humble:

```bash
source /opt/ros/humble/setup.bash
colcon list --base-paths src
colcon build --base-paths src --event-handlers console_direct+
rosdep check --from-paths src --ignore-src
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py --show-args
```

The final build finished both packages successfully. `rosdep check` reported that all system dependencies were satisfied. The launch command found and parsed the installed launch file, and the installed `rviz/view.rviz` file was present. Python compilation of `launch.py` also passed. CMake printed policy warnings from the installed PCL configuration; those warnings did not prevent the build.

## Limits of this verification

Jazzy is not installed under `/opt/ros` on this machine, so a Jazzy compile or launch test was not possible here. The bundled SDK archives are prebuilt for `x86_64` and `aarch64`; their behavior with a particular Jazzy system's compiler and libraries must be checked on that system. At this earlier verification stage, a user launch confirmed that RViz started on Humble, but live point cloud and IMU data had not yet been verified. A later Ethernet test did verify both topics, as described below.

## Follow-up: RViz loader failure

A later Humble launch started the LiDAR node and bound UDP port 6201, but RViz exited with code 127. Its loader error named `/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0` and an unresolved `__libc_pthread_init` symbol with version `GLIBC_PRIVATE`. This points to a Snap runtime library being loaded into the host ROS RViz process. The Wayland message printed immediately before it is a separate warning; the fatal line is the library symbol error.

The environment available during diagnosis did not contain any Snap path in `LD_LIBRARY_PATH`, and `ldd` on the host RViz executable resolved the host C library. That means the exact source of the Snap path in the user's earlier terminal could not be observed from this session. The launch file now filters paths resolving under `/snap/` or `/var/lib/snapd/snap/` out of RViz's inherited `LD_LIBRARY_PATH`, `LD_PRELOAD`, `QT_PLUGIN_PATH`, and `QT_QPA_PLATFORM_PLUGIN_PATH`. It passes the filtered values only to the RViz action through `additional_env`, preserving the LiDAR node's environment and the non-Snap ROS and Qt paths.

The filter was checked with a simulated `LD_LIBRARY_PATH` containing both ROS and Snap entries. The resulting RViz action retained `/opt/ros/humble/lib:/usr/lib` and removed the `/snap/core20/...` entry. This verifies the launch configuration, not a live GUI startup from the affected terminal. If the loader error persists, the terminal's `LD_LIBRARY_PATH` and `LD_PRELOAD` values are needed to identify any remaining source.

### Second RViz launch attempt

The same loader error occurred again after the first filter. Inspection confirmed that the installed launch file is a symlink to the edited source, and that RViz's executable has ROS runpaths and resolves the host C library in this session. ROS launch's `additional_env` implementation merges values into the launch context environment, but the failing terminal's full environment was still unavailable. The revised launch action now sets `env` to a complete, sanitized copy of the environment. It removes Snap-specific variables, removes Snap entries from colon-separated paths and `LD_PRELOAD`, and drops individual variables whose value is a Snap path. This covers additional plugin and data paths that can load libraries indirectly. The sanitization applies only to RViz; the LiDAR node keeps its original environment.

A simulated environment containing Snap entries in `LD_LIBRARY_PATH`, `QT_PLUGIN_PATH`, `SNAP`, and `PATH` produced an RViz action with the Snap entries removed and ROS/host paths retained. A live RViz retry in the original terminal is still required to confirm that this resolves the loader failure there.

The user's environment output then showed `GIO_MODULE_DIR=/home/timl/snap/code/common/.cache/gio-modules`. That directory held symlinks to modules in `/snap/code/...`. Running `ldd` on those modules showed dependencies resolving to `/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0` and other Snap libraries, matching the RViz error. The path filter was extended to cover `~/snap/` as well as system Snap directories. A simulated launch environment confirmed that RViz no longer receives `GIO_MODULE_DIR` while it retains its ROS library paths.

The user subsequently supplied a launch log where RViz reported OpenGL 4.6 and did not exit with the loader error. The LiDAR node also bound UDP port 6201. This confirms that RViz starts in that terminal; the log does not establish that point clouds or IMU data were received or displayed. The Wayland `XDG_SESSION_TYPE` warning remains but is not fatal.

### Sources for the RViz launch fixes

**Configuration path.** The installed file on this machine is `install/unitree_lidar_ros2/share/unitree_lidar_ros2/rviz/view.rviz`; the driver's `CMakeLists.txt` installs the `rviz` directory into the package share directory. The previous launch path omitted `rviz/`. The [ROS 2 Humble `ament_index_python` implementation](https://raw.githubusercontent.com/ament/ament_index/humble/ament_index_python/ament_index_python/packages.py) documents that `get_package_share_directory(package_name)` returns the installed `share/<package_name>` directory. That is why the launch file now joins the returned path with `rviz/view.rviz`. The file's actual installed location and the launch check are local evidence, rather than claims from the ROS source.

**RViz process environment.** The user's loader error named `/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0`, and inspection found `GIO_MODULE_DIR` under `~/snap/code` with modules resolving to Snap libraries. These local observations identified the conflicting runtime. [Snap's environment documentation](https://snapcraft.io/docs/reference/development/environment-variables/) describes its separate runtime and paths under `/snap` and `~/snap`; the [Linux dynamic linker manual](https://man7.org/linux/man-pages/man8/ld.so.8.html) documents how `LD_LIBRARY_PATH` and `LD_PRELOAD` affect library loading. The exact `GIO_MODULE_DIR` to `libpthread` chain was established by the local `ldd` inspection, not by those general references.

**Why `env` is set on the RViz action.** The [ROS 2 Humble launch `ExecuteProcess` source](https://raw.githubusercontent.com/ros2/launch/humble/launch/launch/actions/execute_process.py) documents that `additional_env` adds or overrides values in the inherited environment, whereas `env` supplies a complete environment for the child process. The first filter used `additional_env` and the crash persisted. Passing the cleaned environment through `env` to RViz alone made the user's next RViz launch start successfully.

## Follow-up: RViz reports `Frame [unilidar_lidar] does not exist`

The RViz configuration uses `unilidar_lidar` as its fixed frame. Before this repair, the driver published both the dynamic IMU orientation and the fixed IMU-to-LiDAR offset only inside the IMU packet branch. With no IMU packets, no transform was published, so RViz could not resolve the LiDAR frame.

Live inspection found the ROS node and its publishers, but five-second checks received no cloud, IMU, or `/tf` messages. The host had no `192.168.1.2` address or wired interface, while the launch file was configured for UDP. The user clarified that the LiDAR is connected by serial. Host-side inspection found `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A64010467-if00`, pointing to `/dev/ttyACM0`, and confirmed that the user has access through the `dialout` group.

At this stage, the launch file was temporarily changed to default to serial initialization (`initialize_type=1`), serial work mode (`work_mode=8`), 4,000,000 baud, and that stable device path. The settings are launch arguments, so UDP remained available with `initialize_type:=2 work_mode:=0` and other serial devices could be passed with `serial_port:=...`. The node now checks SDK initialization results and fails clearly if the serial port cannot be opened. It also warns if no cloud or IMU data arrives. A later live Ethernet test showed UDP working, so the final launch defaults are UDP (`2`, `0`).

The fixed IMU-to-LiDAR offset is now sent once through `tf2_ros::StaticTransformBroadcaster` at startup, independent of IMU packets. The dynamic initial-IMU-to-IMU orientation remains in the IMU packet branch. This makes `unilidar_lidar` available as a frame even when data has not yet arrived. It does not create point clouds or prove that serial communication is working. Unitree's SDK documentation says a factory Ethernet-mode device must be switched to serial mode over Ethernet and power cycled before serial data will arrive.

The user asked how to make that first-time switch. The bundled `set_to_serial_mode` example had nonfactory default addresses `192.168.123.110` and `192.168.123.120`, unlike the SDK's factory Ethernet example (`192.168.1.62` and `192.168.1.2`). Its defaults were corrected, optional LiDAR and host IP arguments were added, and it now waits for a valid Ethernet packet before sending work mode `8`. It reports that the command was sent rather than claiming the mode is verified, and instructs a power cycle. This utility was built but not run against hardware because this machine had no Ethernet interface connected to the LiDAR during the repair.

A later serial launch opened the configured `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A64010467-if00` port but repeatedly reported `Serial port timeout!`. Live checks confirmed `initialize_type=1`, the expected serial path, and the fixed `unilidar_imu` to `unilidar_lidar` transform on `/tf_static`. A five-second cloud check still received no message. The RViz frame publication is therefore working, while serial sensor data is not arriving. The first-time Ethernet-to-serial mode switch remains the leading explanation until the device's current work mode is verified.

After the user configured the host's USB Ethernet adapter as `192.168.1.2/24`, the switch utility bound UDP port 6201 but received no LiDAR packets, so it correctly refused to claim a mode change. The host successfully pinged the LiDAR at `192.168.1.62`, proving Ethernet reachability at the factory IP. A six-second Ethernet receive-counter check showed no incoming packets while idle. Packet capture could not be run from this session because it lacked capture permission, and unattended `sudo` required a password. The user confirmed the LiDAR is powered and rotating and the destination host IP has not changed. These checks do not establish why the LiDAR is not streaming UDP.

The switch utility was therefore given an explicit `--force` option. It preserves the packet-checking default, but on `--force` it sends work mode `8` after a warning even if no stream was received. It reports that the command was sent without claiming device acknowledgement; the user must power cycle and verify serial data afterward. The utility built successfully. No unverified mode command was sent by the agent.

The user ran `set_to_serial_mode --force`, fully power cycled the LiDAR, and still saw serial timeouts. The device is powered and rotating. Host inspection confirmed the `usb-1a86_USB_Single_Serial_...` adapter appears as `/dev/ttyACM0` with no other process holding it. A direct five-second read of that port at the manual's 4,000,000 baud received zero bytes. This isolates the remaining problem below ROS message parsing: the LiDAR is not delivering serial bytes to this adapter. The force command gave no acknowledgement, so its mode change is unverified. Unitree's manuals say L2 outputs through only one transport at a time and recommend confirming UART output mode and the supplied adapter/wiring when serial data is absent.

The user confirmed that the serial lead is connected through Unitree's supplied UART adapter module. The bundled SDK archive matches the one tracked in the upstream `unilidar_sdk2` v2.0.10 checkout byte for byte; Unitree currently lists v2.0.10 as its latest tagged release. There is no evidence here that an SDK upgrade would restore the missing bytes. The next decisive check is Unitree's Unilidar 2 host application: connect over Ethernet, select **UART** under **ENET/UART Select**, click **SetMode**, confirm its success prompt, then click **Restart**. The prior `--force` command provided no such confirmation. If the application confirms UART mode and a fresh serial read still returns zero bytes, inspect the adapter's LiDAR-side connector seating, power and data wiring, or have Unitree test the adapter/LiDAR. See the [Unilidar 2 User Manual](https://oss-global-cdn.unitree.com/static/Unilidar%202%20User%20Manual.pdf) and [SDK release list](https://github.com/unitreerobotics/unilidar_sdk2/releases).

The user then asked how to install Unilidar 2. Its manual specifies Windows 64-bit, and the L2 manual says to run `Unilidar 2.exe` as administrator. Unitree's [L2 download page](https://www.unitree-robot.com/download/L2/) links directly to [Unilidar_2_V1.21.exe](https://oss-global-cdn.unitree.com/static/Unilidar_2_V1.21.exe). The current `unitree.com` L2 page omits the application button, so the earlier README link to that page was corrected to the direct executable. There is no native Ubuntu installer documented by Unitree.

The user tried `sudo wine Downloads/Unilidar_2_V1.21.exe`. That created a separate Wine prefix at `/root/.wine` and emitted Wine service, `wineusb`, and network bind errors. The Windows instruction to run as administrator does not mean using Linux `sudo`; Wine should run under the logged-in user. A 20-second trial of `wine /home/timl/Downloads/Unilidar_2_V1.21.exe` as that user did not immediately crash and produced only an `ntlm_auth` diagnostic before being stopped by the timeout. This does not establish that Unilidar 2 can exchange UDP packets through Wine. Host inspection found the Ethernet adapter `enx4cea41695080` currently at `192.168.1.20/24` on NetworkManager connection `Wired connection 3`, whereas the factory LiDAR targets `192.168.1.2`. An actual Windows 64-bit host remains the supported application environment.

After the user reconfigured `Wired connection 3`, host inspection showed `enx4cea41695080` at `192.168.1.2/24`, and two pings to the LiDAR at `192.168.1.62` succeeded. The `.2` address belongs to the host and is selected as the **local receiving address** in Unilidar 2; `.62` belongs to the LiDAR. The user reported that they could not see a connection to `.2` in the application. If `.2` is absent from the application's local-address list despite being configured on Ubuntu, this points to Wine's network interface handling rather than a missing host address. No process was listening on UDP 6201 during the host check.

The user clarified that they could not see `192.168.1.62` in Unilidar 2 and supplied a screenshot. Its **Select UDP IP** list contained only `127.0.1.1`, confirming that Wine was listing only a loopback address in this run. This selector is for the host's local receiving address, so the LiDAR's `.62` address would not appear there; the relevant missing address is the host's `.2`. The screenshot's empty data fields therefore do not demonstrate a LiDAR fault.

A native UDP receive test subsequently bound `192.168.1.2:6201` and received 2,261 datagrams totaling 1,223,424 bytes in five seconds, all from `192.168.1.62:6101`. The ROS driver was then run directly with `initialize_type:=2` and `work_mode:=0`; one message was received on `/unilidar/cloud` with frame `unilidar_lidar`, and one on `/unilidar/imu` with frame `unilidar_imu`. The node exited cleanly after the test. These results prove the LiDAR is currently delivering both cloud and IMU data through Ethernet on this host. The launch file defaults were changed back to UDP (`2`, `0`), and `ros2 launch unitree_lidar_ros2 launch.py --show-args` confirmed those defaults. UART remains selectable through explicit launch arguments. The full RViz launch in this mode has not yet been visually checked after this last change, but RViz itself previously started successfully with the sanitized environment.
