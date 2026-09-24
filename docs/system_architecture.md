# System Architecture Specification

**Project:** SIH26126 — Vision Based Autonomous Navigation for Outdoor UGV  
**Team:** Tikka Techies | Government Engineering College, Jaipur  
**Sponsor:** Bharat Electronics Limited (BEL)

---

## 1. End-to-End Autonomy Data Flow

```text
+-------------------------------------------------------------------------+
|                              SENSING LAYER                              |
|   +--------------------------+  +-------------+  +-------------------+  |
|   |  Forward RGB-D Camera    |  |  6-DOF IMU  |  |  Wheel Encoders   |  |
|   |  (RGB + Depth Images)    |  |  (100 Hz)   |  |  (50 Hz)          |  |
|   +-------------+------------+  +------+------+  +---------+---------+  |
+-----------------|----------------------|-------------------|------------+
                  |                      |                   |
                  v                      v                   v
+------------------------------------+ +----------------------------------+
|          PERCEPTION LAYER          | |     LOCALIZATION / EKF LAYER     |
|  +-------------------------------+ | |  +----------------------------+  |
|  | Terrain Segmentation          | | |  | robot_localization (EKF)   |  |
|  | (RUGD / RELLIS-3D classes)    | | |  | Fuses: /odom + /imu        |  |
|  +---------------+---------------+ | |  +--------------+-------------+  |
|                  |                 | |                 |                |
|  +---------------v---------------+ | |  +--------------v-------------+  |
|  | Obstacle Detection & Ranging  | | |  | Visual Odometry (Phase 3)  |  |
|  +---------------+---------------+ | |  +--------------+-------------+  |
+------------------|-----------------+ +-----------------|----------------+
                   |                                     |
                   +------------------+  +---------------+
                                      |  |
                                      v  v
+-------------------------------------------------------------------------+
|                       WORLD MODEL & COSTMAP 2D                          |
|  +-------------------------------------------------------------------+  |
|  | Global Costmap (Static + Obstacle + Inflation Layer)              |  |
|  | Local Rolling Costmap (Dynamic Obstacle + Traversability Layer)   |  |
|  +-----------------------------------+-------------------------------+  |
+--------------------------------------|----------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------+
|                             NAV2 PLANNING                               |
|  +-------------------------------------------------------------------+  |
|  | Global Planner (Navfn / Smac Traversability Planner)              |  |
|  | Computes collision-free global path from Start to Goal            |  |
|  +-----------------------------------+-------------------------------+  |
|                                      |                                  |
|  +-----------------------------------v-------------------------------+  |
|  | Local Controller (DWB / MPPI Dynamic Avoidance)                   |  |
|  | Computes instantaneous velocities avoiding sudden hazards         |  |
|  +-----------------------------------+-------------------------------+  |
+--------------------------------------|----------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------+
|                          MOTION & ACTUATION                             |
|  +-------------------------------------------------------------------+  |
|  | Output Topic: /cmd_vel (Twist: linear.x, angular.z)               |  |
|  | Gazebo DiffDrive Plugin / Hardware Motor Controller               |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 2. ROS 2 Topic & Interface Contracts

| Topic Name | Message Type | Source / Publisher | Target / Subscriber | Rate (Hz) | Purpose |
|---|---|---|---|---|---|
| `/camera/image_raw` | `sensor_msgs/msg/Image` | Camera Sensor / Bridge | Perception Nodes | 30 | RGB input for terrain segmentation |
| `/camera/depth/image_raw` | `sensor_msgs/msg/Image` | Depth Sensor / Bridge | Costmap Obstacle Layer | 30 | 3D obstacle distance & depth |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Camera Sensor / Bridge | Perception / SLAM | 30 | Camera intrinsics ($f_x, f_y, c_x, c_y$) |
| `/imu` | `sensor_msgs/msg/Imu` | IMU Plugin / Bridge | `robot_localization` | 100 | Angular velocities & linear accelerations |
| `/odom` | `nav_msgs/msg/Odometry` | Wheel Encoder / Bridge | `robot_localization` | 50 | Raw differential wheel odometry |
| `/odometry/filtered` | `nav_msgs/msg/Odometry` | `ekf_node` | Nav2 Stack / Controller | 30 | Drift-filtered vehicle state estimate |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Nav2 Controller | Actuator / Bridge | 20 | Motor velocity commands ($v_x, \omega_z$) |
| `/plan` | `nav_msgs/msg/Path` | Nav2 Planner | RViz2 / Monitoring | 10 | Computed global route to goal |
| `/local_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | Nav2 Costmap 2D | Controller / RViz2 | 5 | Local obstacle & traversability field |

---

## 3. Coordinate Frame Architecture (REP-105 Compliance)

All transforms adhere strictly to ROS standards:

```text
map (Global World Reference Frame)
 └── odom (Continuous Smooth Odometry Reference Frame)
      └── base_footprint (2D Ground Projection of UGV)
           └── base_link (Center of Mass / Structural Chassis)
                ├── left_front_wheel
                ├── left_rear_wheel
                ├── right_front_wheel
                ├── right_rear_wheel
                ├── imu_link
                └── camera_link
                     └── camera_optical_link (Optical frame: z forward, x right, y down)
```

- `robot_localization` (and later Visual SLAM) is responsible for maintaining the `odom -> base_footprint` and `map -> odom` transforms without discrete jumps.
- `robot_state_publisher` reads the URDF model and publishes the static and joint transforms from `base_link` out to wheels and sensors.
