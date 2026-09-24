# Robotics Development & ROS 2 Standards

This rule governs all code, simulation assets, and experiments developed for SIH26126 in this workspace.

## 1. ROS 2 Architectural & Code Standards
- **Naming Conventions:**
  - Package names: `snake_case` (e.g., `ugv_perception`, `ugv_bringup`, `ugv_nav2`).
  - Node names: `snake_case` (e.g., `traversability_node`, `visual_odometry_node`).
  - Topic names: `snake_case` (e.g., `/camera/image_raw`, `/ugv/cmd_vel`, `/odom/filtered`).
  - Service / Action names: `PascalCase` for types, `snake_case` for instances.
  - Parameter names: `snake_case` (e.g., `traversability_threshold`, `max_linear_velocity`).
- **Coordinate Frames & REP Compliance:**
  - Strictly adhere to **REP-103** (Units and Coordinate Conventions):
    - $x$: Forward
    - $y$: Left
    - $z$: Up
    - Angular: Counter-clockwise positive (Right-hand rule). Angles in radians, distances in meters.
  - Strictly adhere to **REP-105** (Coordinate Frames for Mobile Platforms):
    - `earth` -> `map` -> `odom` -> `base_footprint` -> `base_link` -> sensor frames (`camera_link`, `imu_link`).
    - The localization stack (`robot_localization` / Visual SLAM) publishes the `map` -> `odom` and/or `odom` -> `base_link` transforms.

## 2. Nav2 & Planning Conventions
- Use standard ROS 2 message types (`geometry_msgs/msg/Twist`, `nav_msgs/msg/Odometry`, `sensor_msgs/msg/Image`).
- Costmap updates must be published as costmap layers (`nav2_costmap_2d`) rather than ad-hoc arrays.
- Emergency stop or tracking loss conditions must command zero velocity immediately.

## 3. Experiment & Benchmark Discipline
- No performance claims ("real-time", "robust", "high-accuracy") without citing an experiment ID logged in `/eval/`.
- Every major test must be recorded following the template in Section 8 of `AGENTS.md`.
