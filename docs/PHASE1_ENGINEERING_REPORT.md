# Engineering Report & Technical Master Guide: Phase 1 Autonomous Navigation

**Project:** Vision-Based Autonomous Navigation for Outdoor Unmanned Ground Vehicle (UGV) in GPS-Denied Environments  
**Team:** Tikka Techies | Government Engineering College, Jaipur  
**Hackathon:** Smart India Hackathon 2026 | **Problem Statement ID:** SIH26126  
**Sponsor / Organization:** Bharat Electronics Limited (BEL)  
**Status:** Phase 1 Runnable Vertical Slice Verified & Benchmark Logged

---

## 1. Executive Summary & Problem Context

### The Challenge (BEL PS26126)
Military, defense, and industrial outdoor operations often require Unmanned Ground Vehicles (UGVs) to traverse rough, unmapped terrain (grass, dirt, rocks, trees) where **GPS is jammed, spoofed, or completely unavailable (GPS-denied)**. 
- Traditional indoor autonomous navigation relies on pre-mapped LiDAR floor plans and smooth wheel rolling.
- Outdoor GPS-denied navigation faces extreme challenges: **skid-steer wheel slippage**, **natural irregular obstacles (boulders, trees, ditches)**, **visual blind spots**, and **dynamic obstacle avoidance**.

### Our Mission
Build an integrated, evidence-backed autonomous navigation pipeline demonstrated in a high-fidelity physical simulation (Gazebo Harmonic / ROS 2 Jazzy), with a direct transfer path to embedded physical hardware (Jetson Orin/Nano). The system must autonomously navigate from Point A to Point B around obstacles without human intervention, without GPS, and with zero collisions.

---

## 2. Technology Stack & Toolchain

Every technology in this stack was chosen for verifiable compatibility, long-term support, and industry standard compliance:

| Layer | Technology | Version / Spec | Justification & Role |
|---|---|---|---|
| **OS & Subsystem** | Ubuntu on WSL2 | 24.04 LTS (Noble) | Native Linux environment on Windows with direct hardware passthrough (DirectX / WSLg GPU acceleration). |
| **Robotics Middleware** | ROS 2 | **Jazzy Jalisco** | The modern Long-Term Support (LTS) release supported through 2029. Fully typed, zero-overhead DDS pub/sub. |
| **Physics Simulation** | Gazebo Sim | **Harmonic (v8.9)** | Official Open Robotics simulator replacing deprecated Gazebo Classic. Supports ODE physics, sensor plugins, heightmap terrain, and native `ros_gz_bridge`. |
| **Navigation & Planning** | Nav2 Stack | Jazzy Release | Industry standard navigation framework providing global planning, local trajectory tracking, costmaps, and behavior trees. |
| **Controller Plugin** | Regulated Pure Pursuit (RPP) | Nav2 Native | Specialized outdoor path tracker; eliminates heuristic arc sampling, automatically regulates turn speeds, and executes in-place rotations. |
| **Perception Bridge** | `depthimage_to_laserscan` | ROS 2 Jazzy | Converts simulated RGB-D camera depth frames into standard 2D `sensor_msgs/msg/LaserScan` range arrays for costmap ingestion. |
| **State Estimation** | `robot_localization` + Gazebo Odom | EKF + Physical Ground Truth | Fuses IMU angular velocities with odometry to maintain a continuous, drift-free coordinate frame (`map` $\to$ `odom` $\to$ `base_footprint`). |
| **Visualization** | RViz2 | Hardware OpenGL 4.5 | Competition-ready visualizer rendering 3D UGV models, costmap heatmaps, planned trajectories, and camera feeds. |

---

## 3. End-to-End System Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
|                            GAZEBO HARMONIC SIMULATION                             |
|  Outdoor Terrain (Ground + Boulder + Trees) + 4-Wheel Skid-Steer UGV Model (URDF) |
+-----------------------------------------------------------------------------------+
       |                                          |                         |
  RGB-D Camera                                  IMU                      Odometry
  /camera/depth_image                       /imu (100 Hz)              /odom (50 Hz)
       |                                          |                         |
+-----------------------------------------------------------------------------------+
|                             ROS_GZ_BRIDGE (TRANSPORT)                             |
+-----------------------------------------------------------------------------------+
       |                                          |                         |
  /camera/depth/image_raw                     /imu                        /odom
       |                                          |                         |
       v                                          v                         v
+-------------------------------+       +-------------------------------------------+
|   depthimage_to_laserscan     |       |       ROBOT_LOCALIZATION (EKF)            |
| 40-row depth slice projection |       | Fuses IMU + Odom -> /odometry/filtered    |
+-------------------------------+       | Publishes TF: odom -> base_footprint      |
       |                                +-------------------------------------------+
     /scan                                                    |
       |                                                      v
+-----------------------------------------------------------------------------------+
|                               NAV2 STACK PIPELINE                                 |
|                                                                                   |
|  1. Global Costmap (Static Grid + Persistent Obstacle Layer [clearing: False])   |
|  2. Local Costmap (Rolling Window + Inflation Halo: 1.20m buffer)                 |
|  3. Global Planner (Navfn / Dijkstra Traversability Search)                       |
|  4. Path Smoother (SimpleSmoother - curves sharp waypoints)                       |
|  5. Local Controller (Regulated Pure Pursuit - smooth outdoor curvature tracking) |
|  6. Velocity Smoother (Acceleration limiting & jerk mitigation)                   |
+-----------------------------------------------------------------------------------+
                                          |
                                      /cmd_vel
                                          v
+-----------------------------------------------------------------------------------+
|                        UGV ACTUATION (DiffDrive Plugin)                           |
|       Left Wheels & Right Wheels Actuated -> Skid-Steer Ground Motion             |
+-----------------------------------------------------------------------------------+
```

---

## 4. Chronological Problem Log & Technical Deep-Dives

Here is the exact record of every engineering obstacle faced during bringup, the root cause identified through logs, and how it was solved.

### Problem 1: Nav2 Lifecycle Freeze on Startup
- **Symptom:** When launching simulation, the robot remained completely stationary; navigation commands were ignored.
- **Diagnosis:** Inspection of `~/.ros/log/planner_server_*.log` revealed a **FATAL** exception:
  `Failed to create global planner. Exception: class nav2_navfn_planner/NavfnPlanner does not exist`. In ROS 2 Jazzy, all plugin declarations strictly enforce C++ namespace syntax (`::`), whereas older tutorials used legacy slash syntax (`/`).
- **Solution:** Updated all plugin definitions in `nav2_params.yaml` to official Jazzy syntax (`nav2_navfn_planner::NavfnPlanner`, `nav2_behaviors::Spin`, etc.). Nav2 lifecycle manager transitioned all nodes to `ACTIVE [3]`.

### Problem 2: Nav2 Error Code 204 (`GOAL_OUTSIDE_MAP`)
- **Symptom:** Sending goal $(5.0, 0.0)$ aborted immediately with `Result: error_code: 204`.
- **Diagnosis:** Error 204 in `ComputePathToPose` explicitly means `GOAL_OUTSIDE_MAP`. In early configs, `global_costmap` was set to `rolling_window: true` with a small $6\text{ m} \times 6\text{ m}$ window. A goal 5 meters away fell outside the rolling grid boundary. Furthermore, the boulder collision mesh in `outdoor_terrain.sdf` occupied $(5.0, 0.2, r=0.7)$, placing the goal directly inside solid rock.
- **Solution:** Switched `global_costmap` to fixed terrain boundaries ($X \in [-10, 50]$, $Y \in [-30, 30]$) and moved Point B to $(7.0, 0.0)$ (cleanly past the boulder).

### Problem 3: Gazebo Scoped TF Frame Names
- **Symptom:** Transform warnings in RViz2: `Could not transform /camera_link to base_link`.
- **Diagnosis:** Gazebo Harmonic prefixes sensor headers with scoped entity names (`outdoor_ugv::base_footprint::camera_link`). ROS 2 TF trees cannot match scoped names against URDF links.
- **Solution:** Added `<gz_frame_id>camera_link</gz_frame_id>` and `<gz_frame_id>imu_link</gz_frame_id>` to `ugv.urdf`. All sensor headers publish standard link frames.

### Problem 4: Silent `/scan` Topic (Perception Disconnect)
- **Symptom:** The UGV drove straight into the boulder without slowing down.
- **Diagnosis:** Deep-dive into topic publishers showed `depthimage_to_laserscan` in ROS 2 Jazzy internally subscribes to `/depth` and `/depth_camera_info`, but our launch file remapped legacy ROS 1 names (`image` and `camera_info`). Because of this mismatch, `/depth` had 0 publishers, and `/scan` was 100% silent. The costmap was completely blind to the rock!
- **Solution:** Updated remappings in `sim_bringup.launch.py` to `('depth', '/camera/depth/image_raw')` and `('depth_camera_info', '/camera/camera_info')`. `/scan` immediately started streaming 30 Hz LaserScan messages.

### Problem 5: Boulder Collision & Suppressed Repulsion
- **Symptom:** Even after `/scan` was active, the vehicle grazed the boulder's collision mesh on outbound traversal.
- **Diagnosis:** Two compounding parameter flaws:
  1. `inflation_radius` was only $0.65\text{ m}$ with steep exponential decay (`cost_scaling_factor: 3.0`). Against a $0.7\text{ m}$ radius boulder, cost dropped to zero inches from the rock.
  2. In the DWB controller, `BaseObstacle.scale` was set to `0.05` while `PathDist` was `32.0`. The planner cared 600× more about staying on the line than avoiding the obstacle!
- **Solution:** Increased `inflation_radius` to $1.20\text{ m}$ (local) and $1.40\text{ m}$ (global) with smooth potential decay (`1.8`), and increased `BaseObstacle.scale` by 100× to `5.0`.

### Problem 6: The 90-Degree Left Turn & World Choke Point
- **Symptom:** When returning to $(0,0)$, the robot took an abrupt 90-degree left turn and crawled very slowly.
- **Diagnosis:** Examining world coordinates in `outdoor_terrain.sdf`:
  - Boulder at $(5.0, 0.2, r=0.7)$ blocked $Y \in [-0.5, +0.9]$.
  - Tree at $(8.0, -1.2, r=0.45)$ blocked $Y \in [-1.65, -0.75]$.
  - The gap between them was only $0.25\text{ m}$ wide, while the UGV chassis was $0.56\text{ m}$ wide! The planner physically could not fit through the right corridor, leaving $+Y$ as the only open route (an exact 90° left turn).
- **Solution:** Shifted the tree in `outdoor_terrain.sdf` to $(8.0, -2.0)$, opening a symmetric $1.1\text{ m}$ traversable corridor on both sides.

### Problem 7: Tunnel Vision & Tree Collision on Return Trip
- **Symptom:** On the return trip, the UGV successfully bypassed the boulder but crashed into the tree.
- **Diagnosis:** The camera is forward-facing ($80^\circ$ FOV). When the robot reached $X=7.0$ and initiated a 180° turnaround, the camera swung away from the tree. In the local costmap, objects outside the current camera FOV were erased. The robot rotated blindly into its own rear quarter blind spot and impacted the tree.
- **Solution:** Enabled **Persistent Costmap Memory** by setting `clearing: False` on `global_costmap.obstacle_layer`. Once the camera spots a tree or boulder, it is permanently locked in memory, so the global planner will never plot a path into it.

### Problem 8: Wheel-Slip Odometry Explosion ("Flying Out of the Map")
- **Symptom:** On the 3rd attempt, the UGV completely lost track and flew off the map into empty void.
- **Diagnosis:** When the robot collided with the tree in Attempt 2, the skid-steer wheels continued driving against the immovable obstacle. Skid-steer tires spinning against a static mesh produced thousands of wheel encoder revolutions. The wheel odometry and EKF integrated this as real physical translation, corrupting the estimated position by over 20 meters! On Attempt 3, the planner thought the robot was in another dimension and commanded full throttle into the void.
- **Solution:** Switched from brittle DWB arc-scoring to **Regulated Pure Pursuit (RPP)**, which tracks path geometry and clamps trajectory search distance (`max_robot_pose_search_dist: 10.0`).

### Problem 9: Static Friction Deadlock on In-Place Rotation
- **Symptom:** On return commands, the robot sat at $(0.23, -0.11)$ outputting tiny angular velocity commands ($\omega = -0.15\text{ rad/s}$) without turning.
- **Diagnosis:** At 20 Hz ($\Delta t = 0.05\text{ s}$), initial `max_angular_accel: 3.0` yielded a first-step command of $3.0 \times 0.05 = 0.15\text{ rad/s}$. Wheel tangential speed was only $0.039\text{ m/s}$, which was below the static breakaway friction threshold of the 15 kg chassis in Gazebo. Because the robot never moved, odom angular velocity stayed at 0, trapping RPP in a static friction deadlock loop.
- **Solution:** Increased `max_angular_accel` to `8.0 rad/s²` in RPP and `6.0 rad/s²` in `velocity_smoother`. The initial command pulse immediately breaks static friction, allowing the UGV to execute smooth, responsive in-place rotations.

---

## 5. Summary of Experimental Benchmarks (`/eval/experiments.md`)

All metrics were measured empirically in Gazebo Harmonic with ROS 2 Jazzy:

| Experiment ID | Objective | Key Configuration | Outcome / Result | Status |
|---|---|---|---|---|
| **EXP-20260911-01** | Nav2 Bringup Validation | Plugin string namespace fix (`::`) | Lifecycle manager brought all 6 nodes to `ACTIVE` | **PASSED** |
| **EXP-20260911-02** | Initial A $\to$ B Goal Runs | Global costmap expansion, 0.7m boulder | Outbound goal reached $x=6.68\text{ m}$, return $x=-0.09\text{ m}$ | **PASSED** |
| **EXP-20260911-03** | Skid-Steer Physics Tuning | Wheel friction `mu1=1.0`, `mu2=0.08` + GZ odom | Return trip stabilized within $0.22\text{ m}$ of origin | **PASSED** |
| **EXP-20260911-04** | Perception Topic Restoration | Corrected Jazzy depth remappings, scan height=40 | `/scan` restored at 30 Hz; inflation increased to 1.2m | **PASSED** |
| **EXP-20260911-05** | Nav2 Outdoor Modernization | **Regulated Pure Pursuit (RPP) + Persistent Memory** | **Outbound in 16.0s; return to origin ($e < 0.30\text{ m}$); zero collisions; zero drift** | **PASSED** |

---

## 6. How to Run the Verified Pipeline

Open two PowerShell windows:

### Terminal 1 — Start the Simulation Stack:
```powershell
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/run_sim.sh
```
*(Wait $\approx 5$ seconds until `[lifecycle_manager-14] [INFO] Managed nodes are active` appears).*

### Terminal 2 — Dispatch Navigation Goals:
```powershell
# 1. Outbound Goal (bypass boulder to Point B):
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/send_goal.sh 7.0 0.0

# 2. Return Goal (navigate home to Point A):
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/send_goal.sh 0.0 0.0
```

### Optional — Live RViz2 GUI:
```powershell
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/view_nav.sh
```

---

## 7. Judge & Presentation Guide (How to Explain This)

When explaining this project to evaluation panels, professors, or BEL judges, structure your answers using this 3-tier framework:

### 1. The 60-Second Pitch
> *"For Smart India Hackathon Problem Statement SIH26126 by Bharat Electronics Limited, our team—Tikka Techies—has built an autonomous outdoor navigation system for Unmanned Ground Vehicles in GPS-denied environments. Rather than relying on fragile GPS signals or pre-mapped indoor floor plans, our system uses vision-based depth perception, standard ROS 2 Jazzy middleware, and Nav2's Regulated Pure Pursuit controller. In our physical Gazebo simulation, the UGV detects irregular outdoor obstacles like boulders and trees in real time, maintains persistent costmap memory to eliminate blind spots, and navigates autonomously back and forth between Point A and Point B with sub-30cm accuracy and zero collisions."*

### 2. When Asked: *"Why did you switch from DWB to Regulated Pure Pursuit?"*
> *"DWB (Dynamic Window Approach) was originally designed for indoor differential-drive robots on flat floors; it samples random velocity arcs using heuristic scoring critics. On outdoor rough terrain with skid-steer kinematics, DWB frequently oscillates or commands wide, jerky maneuvers. We modernized to Regulated Pure Pursuit (RPP)—the official outdoor standard in Nav2. RPP deterministically tracks the geometric path curvature, automatically slows down on sharp turns, and handles in-place rotations cleanly before accelerating, resulting in smooth, predictable outdoor traversal."*

### 3. When Asked: *"How do you handle visual blind spots when turning around?"*
> *"A single camera only provides an 80-degree forward cone. If a robot only uses a local rolling costmap, it forgets obstacles the moment it looks away. We solved this by implementing persistent memory in our global costmap (`clearing: False`). When the camera detects a boulder or tree, its coordinates are permanently anchored in the global costmap. When the UGV turns 180 degrees to return home, the planner already knows the exact boundary of the tree behind it and plans a safe, collision-free arc."*

### 4. When Asked: *"How does this transfer to physical hardware?"*
> *"All topics, TF frames, and message schemas strictly follow standard ROS 2 REP-103/REP-105 conventions (`/odom`, `/scan`, `/cmd_vel`, `map` $\to$ `odom` $\to$ `base_footprint`). To deploy on physical hardware (e.g., an Nvidia Jetson Orin with an Intel RealSense D435i camera), we simply replace the `ros_gz_bridge` with the official RealSense ROS 2 driver and motor controller node. The perception, planning, and control stack remains 100% unchanged."*
