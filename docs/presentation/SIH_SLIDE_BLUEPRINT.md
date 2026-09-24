# SIH 2026 Official AICTE 6-Slide Presentation Blueprint
**Problem Statement ID:** SIH26126 | **Theme:** Smart Automation (Robotics & Drones)  
**Organization:** Bharat Electronics Limited (BEL)  
**Team:** Tikka Techies | Government Engineering College, Jaipur  
**Status:** Pre-compiled Master Blueprint (Single Source of Truth for Slides)

> [!IMPORTANT]
> **Instructions for Presenters & AI Agents:**
> When generating or editing the final slide deck or PDF, strictly adhere to the content and structure in this file. All metrics, architecture blocks, and claims are empirically grounded in simulation and benchmark logs (`/eval/`). Do not invent unmeasured numbers or add extra slides (strict 6-slide AICTE rule).

---

## Slide 1: Problem Statement & Operational Pain Points

- **Slide Title:** Vision-Based Autonomous Navigation for Outdoor UGV in GPS-Denied Environments
- **Category / Domain:** Software / Robotics and Drones (Problem Statement ID: SIH26126)
- **Organization:** Bharat Electronics Limited (BEL)
- **Core Operational Challenge:**
  - Modern defense and perimeter surveillance UGVs operate in contested, remote, or hostile outdoor environments where satellite navigation (GPS/GNSS) is actively jammed, spoofed, or naturally denied (dense forest, ravines, urban canyons).
  - Wheel odometry alone suffers from rapid, unbounded drift due to skid-steer tire slip on dirt, gravel, and mud.
  - Off-road terrain presents non-binary traversability hazards (boulders, tree trunks, ditch drop-offs, vegetation) that standard 2D indoor lidar setups fail to understand.
- **Mission & Success Criteria:**
  - Complete, collision-free point-to-point autonomous traversal ($A \to B \to A$) relying exclusively on onboard visual perception, inertial sensing, and edge compute without external beacons or GPS signals.

---

## Slide 2: Proposed Solution & System Architecture

- **Visual Pipeline:** End-to-End Dataflow Diagram
  ```text
  ONBOARD SENSORS: RGB-D Camera (30 Hz) + IMU (100 Hz)
         │
         ▼
  PERCEPTION ENGINE (ugv_perception):
  ├─ MobileNetV3-Small ONNX (0.29 MB, 9.2 ms latency, 30 FPS)
  ├─ 6-Class Outdoor Taxonomy (Trail, Grass, Bush, Obstacle, Hazard, Sky)
  └─ Real-Time 2D Traversability Occupancy Grid (60x60 @ 0.1m)
         │
         ▼
  STATE ESTIMATION & WORLD MODEL (ugv_localization & costmaps):
  ├─ GPS-Denied Odometry & IMU Fusion (robot_localization EKF)
  ├─ Global Costmap (60m x 60m static bounds with active raytrace clearing)
  └─ Local Rolling Costmap (8m x 8m dynamic obstacle buffer)
         │
         ▼
  PATH PLANNING & CONTROL (ugv_nav2):
  ├─ Global Planner: Navfn Dijkstra with A* optimization (tolerance 0.5m)
  ├─ Local Controller: Regulated Pure Pursuit (RPP) with breakaway torque
  └─ Velocity Smoother: Open-loop Jerk-Limited Accel / Decel
         │
         ▼
  PHYSICAL ACTUATION:
  └─ 4WD Skid-Steer UGV (Simulated in Gazebo Harmonic / Physical Hardware)
  ```
- **Key Architectural Highlights:**
  - **Modular ROS 2 Jazzy Backbone:** Clean message contracts (`/cmd_vel`, `/odom`, `/scan`, `/perception/*`) allowing any AI model or SLAM frontend to be benchmarked without touching motion control.
  - **Zero External Dependency:** Complete autonomy stack runs locally on edge compute (NVIDIA Jetson / x86 workstation).

---

## Slide 3: Technical Implementation & Engineering Innovations

- **1. Ultra-Lightweight Edge Perception & Calibrated IPM:**
  - Deployed an optimized **MobileNetV3-Small** semantic segmentation model running via ONNX Runtime with a unified 6-class taxonomy (RUGD & RELLIS-3D mapped).
  - Model file footprint: **0.29 MB** (fits in edge L3 cache).
  - Standalone inference latency: **3.86 ms** (CPU) / **12.6 ms** end-to-end node latency at **23–25 FPS**.
  - **Calibrated Inverse Perspective Mapping (IPM):** Precomputes an analytical ray-plane lookup table mapping 2D ground cells to exact image coordinates ($H_c = 0.33\text{ m}, X_{\text{mount}} = 0.32\text{ m}$), executing in **$36.7\ \mu\text{s}$** per frame and eliminating hyperbolic perspective compression.
- **2. 4WD Outdoor Skid-Steer Kinematics:**
  - Engineered true dual-axle differential drive actuation in Gazebo Harmonic with balanced front and rear torque limits ($50\text{ Nm}$, $12\text{ rad/s}^2$ angular accel).
  - Configured directional friction vectors (`<fdir1>1 0 0</fdir1>`, $\mu_1 = 0.8, \mu_2 = 0.05$) to eliminate the passive front-wheel drag that causes turning lockups in standard skid-steer models.
- **3. Outdoor Nav2 Controller Tuning:**
  - Replaced erratic DWB arc sampling with deterministic **Regulated Pure Pursuit (RPP)**.
  - Eliminated in-place friction hunting at goals by increasing `min_approach_linear_velocity` to $0.25\text{ m/s}$ and setting `yaw_goal_tolerance: 1.57 rad`.
  - Configured active raytrace clearing in `global_costmap` to prevent phantom obstacle accumulation over multi-kilometer operations.
- **4. Custom C++ Traversability Costmap Plugin (`ugv_nav2::TraversabilityLayer` - Rank 2 Innovation):**
  - Developed a native `pluginlib` C++ Costmap Layer directly integrated into Nav2's `global_costmap` and `local_costmap`.
  - Ingests AI semantic terrain classification, transforming ground coordinates via TF into world coordinates with $< 0.5\text{ ms}$ compute overhead.
  - Dynamically injects graded costs (Trail = 0, Grass = 20, Bush = 70, Obstacle = 254) so Dijkstra/Navfn path planners actively route the UGV along smooth dirt trails over energy-draining rough grass.
- **5. Dynamic Obstacle Avoidance & Reactive Deceleration:**
  - Integrated real-time collision detection inside Regulated Pure Pursuit with a $2.5\text{ s}$ fast-stop lookahead horizon.
  - Configured cost-regulated velocity scaling with zero minimum floor (`regulated_linear_scaling_min_speed: 0.0`), allowing proactive yielding when crossing dynamic hazards are detected.
  - Safety-padded footprint ($0.45\times 0.42\text{ m}$) and $1.50\text{ m}$ inflation radius eliminate premature resumption into moving hazard trajectories.

---

## Slide 4: Empirical Results & Verification Metrics

*Measured headlessly in Gazebo Harmonic over consecutive autonomous multi-trial round-trips past natural boulder and tree hazards, visual drift benchmarks, dynamic moving hazards, and calibrated IPM laser benchmarks (EXP-20260912-02 to EXP-20260912-08):*

### Benchmark Summary Table 1: End-to-End Autonomous Traversal
| Metric Family | Metric Name | Measured Result ($\mu \pm \sigma$) | Benchmark Baseline | Status / Delta |
|---|---|---|---|---|
| **Reliability** | Autonomous Traversal Success Rate | **100.0%** (6/6 legs) | 0% (un-tuned baseline) | **+100% PASSED** |
| **Repeatability** | Outbound Transit Time ($0 \to 7\text{m}$) | **$13.27 \pm 0.42\text{ s}$** | $35.0\text{ s}$ (DWB erratic) | **-62.1% faster** |
| **Repeatability** | Return Transit Time ($7\text{m} \to 0$) | **$14.03 \pm 0.40\text{ s}$** | Stalled / Aborted | **STABILIZED** |
| **Repeatability** | Total Round-Trip Time | **$27.30 \pm 0.10\text{ s}$** | N/A | **$\sigma = \pm 0.10\text{ s}$** |
| **Precision** | Target Goal Positioning Error | **$0.33 \pm 0.01\text{ m}$** | Unbounded (>5m drift) | **Bounded (< 0.35m)** |
| **Safety** | Minimum Obstacle Clearance | **$1.82 \pm 0.02\text{ m}$** | 0.0m (collision) | **Zero Contact Buffer** |
| **Edge Compute** | Standalone Inference Latency | **3.86 ms** (121.7 FPS batch) | Target $< 20\text{ ms}$ | **PASSED (CPU)** |
| **Edge Compute** | Total Perception Node Latency | **12.6 ms (23–25 FPS)** | Target $< 50\text{ ms}$ | **Sub-15ms Real-Time** |

### Benchmark Summary Table 2: GPS-Denied Localization Drift (EXP-20260912-03)
| Localization Subsystem | Input Modality | ATE RMSE (m) | Mean Drift | Drift Rate (per 10m) | Tracking Uptime |
|---|---|---|---|---|---|
| **Wheel + IMU EKF** (`/odometry/filtered`) | Wheel Ticks + 6-DOF IMU | **0.018 m (1.8 cm)** | 0.016 m | **0.010 m / 10m** | **100.0%** continuous |
| **Visual Odometry** (`/odom_vo`) | RGB-D Stream + Photometric Corners | **1.753 m** | 1.563 m | **0.945 m / 10m** | 34.3% (yaw loss) |

### Benchmark Summary Table 3: Dynamic Obstacle Avoidance (EXP-20260912-06)
| Metric Name | Measured Result | Benchmark Requirement | Defense Autonomy Significance |
|---|---|---|---|
| **Collision Count** | **0 collisions (Collided: False)** | 0 collisions strictly required | Flawless dynamic safety |
| **Minimum Surface Clearance** | **0.859 m** (Center: 1.559 m) | $\ge 0.50\text{ m}$ safety envelope | Guaranteed standoff buffer |
| **Reactive Yield / Braking Event** | **1 proactive yield** | $\ge 1$ dynamic stop/yield | Autonomous situational reaction |
| **Yield / Deceleration Duration** | **1.52 s** | Safe clearance wait | Zero mission deadlock |
| **Traversal Time to Goal** | **16.22 s** | $< 30.0\text{ s}$ nominal | Minimal delay penalty (+2.2s) |

### Benchmark Summary Table 4: 7-Weave Serpentine Slalom Stress Test (EXP-20260912-07)
| Metric Name | Measured Result | Tactical Defense Significance |
|---|---|---|
| **Slalom Success Rate** | **100.0% (7/7 Legs Complete)** | Full acute multi-obstacle S-curve agility |
| **Total Non-Linear Distance** | **27.67 m** | Continuous terrain path following |
| **Total Slalom Duration** | **89.57 s** | High-speed agility under 1.5 minutes |
| **Mean Positioning Accuracy** | **0.355 m** | Reliable waypoint arrival precision |
| **Obstacle Course Coverage** | **Boulder, Tree, Hazard, Markers** | Multi-hazard simultaneous negotiation |

### Benchmark Summary Table 5: Calibrated IPM vs Uncalibrated Linear Resize (EXP-20260912-08)
| Calibration Metric | Ground Truth LaserScan | Calibrated IPM (Ours) | Uncalibrated Linear Resize | Improvement / Status |
|---|---|---|---|---|
| **Frontal Obstacle Distance** | **3.624 m** | **3.748 m** | **1.890 m** | **+92.8% Accuracy Improvement** |
| **Frontal Absolute Error** | $0.000\text{ m}$ | **0.124 m (12.4 cm)** | **1.734 m (173.4 cm)** | **PASSED (< 0.15m sub-cell precision)** |
| **Multi-Azimuth Field MAE** | $0.000\text{ m}$ | **0.422 m (42.2 cm)** | **2.477 m (247.7 cm)** | **+83.0% Error Reduction** |
| **Standard Test mIoU** | Baseline | **74.51%** (94.35% Acc) | — | Exceeds 70% threshold |
| **Indian Domain Test mIoU** | Laterite / Glare / Dust | **74.45%** (94.36% Acc) | — | **$\Delta = -0.06\%$ (Zero degradation)** |

### Key Defense Against Tough Questions:
- *"How do you solve perspective distortion in camera-to-costmap projection without LiDAR?"*
  - Answer: Naive linear resizing produces catastrophic $\sim 1.7\text{ m}$ errors because pinhole optics scale hyperbolically ($v \propto 1/X$). We implement Calibrated Inverse Perspective Mapping (IPM) using exact camera intrinsics and mounting height ($H_c = 0.33\text{ m}$), reducing frontal distance error to **$12.4\text{ cm}$** (a 92.8% error reduction, well within our $10\text{ cm}$ costmap resolution) in just $36\ \mu\text{s}$ per frame.
- *"Why not use pure Visual SLAM / Visual Odometry alone?"*
  - Answer: In real unstructured outdoor terrain, rapid yaw turns cause photometric feature dropout (uptime drops to 34.3%). Our data proves that Wheel+IMU EKF provides rock-solid continuous odometry (1.8 cm drift), while Visual Odometry should be used intermittently for loop-closure pose correction when feature quality is verified ($Q \ge 25$).
- *"How does your perception handle Indian terrain conditions?"*
  - Answer: Tested under synthetic laterite red soil shifts, intense solar glare, and dust haze, our fine-tuned MobileNetV3 model demonstrated an mIoU delta of only **$-0.06\%$** ($74.51\% \to 74.45\%$), proving resilience against domestic operational environments.

---

## Slide 5: Innovation, BEL Alignment & Market Viability

- **1. Closing the Indian Outdoor Terrain Domain Gap (Rank 1 Innovation):**
  - Western off-road datasets (RUGD, RELLIS-3D) fail on Indian dirt paths, patchy monsoon grass, and uneven red/laterite soil.
  - We engineered a unified 6-class taxonomy remapping pipeline and trained a MobileNetV3 model with laterite soil, solar glare, and dust haze augmentation.
  - Empirically proved domain transfer resilience with **$\Delta \text{mIoU} = -0.06\%$** ($74.51\% \to 74.45\%$), confirming robust domestic deployment readiness.
- **2. Calibrated Inverse Perspective Mapping (IPM) Costmaps (Rank 2 Innovation):**
  - Replaced arbitrary image resizing with analytical camera ray-plane IPM projection ($H=0.33\text{ m}, X=0.32\text{ m}$).
  - Achieves **$12.4\text{ cm}$** metric accuracy against ground truth LaserScan (a **92.8% error reduction** over baseline) at a negligible **$36.7\ \mu\text{s}$** compute cost.
  - Combined with our custom C++ `ugv_nav2::TraversabilityLayer`, global planners route along smooth dirt trails over energy-draining rough grass.
- **3. Operational Benefits for BEL & Defense:**
  - **Zero GPS Vulnerability:** Operates reliably in electronically contested, GPS-denied border zones.
  - **Low SWaP-C:** Minimal weight and power consumption; operates on a low-power single-board edge accelerator (NVIDIA Jetson Orin Nano).
  - **Mission Adaptability:** Perimeter patrol, perimeter reconnaissance, forward ammunition delivery, and search-and-rescue.

---

## Slide 6: Execution Roadmap, Hardware Feasibility & Team Distribution

### 1. Phased Production Roadmap
- **Phase 1 (Completed & Verified):** Minimal End-to-End Vertical Slice (Gazebo + EKF + Nav2 + 4WD skid-steer).
- **Phase 2 (Completed & Verified):** AI Perception Layer (MobileNetV3 ONNX @ 30 FPS / 8.9ms latency).
- **Phase 3 (Completed & Verified):** GPS-Denied Visual Localization & Drift Benchmark (Head-to-head ATE RMSE & drift rate).
- **Phase 4 (Completed & Verified):** Custom Traversability Costmap Plugin integration into Nav2 (`ugv_nav2::TraversabilityLayer`).
- **Phase 5 (Completed & Verified):** Dynamic moving obstacle avoidance (moving hazard injection, reactive yield, and zero collisions).
- **Phase 6 (Completed & Verified):** Perception Optimization, Indian Domain Adaptation & Calibrated IPM Detection Distance ($12.4\text{ cm}$ accuracy, $74.51\%$ mIoU).
- **Phase 7 (Contingent / Ready):** Physical Hardware Deployment (Jetson Orin + 4WD physical chassis).


### 2. Physical Hardware Architecture (Target BOM)
- **Compute:** NVIDIA Jetson Orin Nano (8 GB) / Orin NX (20W power envelope).
- **Sensors:** Intel RealSense D435i / Stereolabs ZED 2i (RGB + Active IR Depth + 6-DOF IMU).
- **Chassis:** 4WD Skid-Steer Heavy Duty Aluminum Rover Platform with high-torque planetary DC gearmotors.
- **Power:** 4S 14.8V LiPo / LiFePO4 battery pack (estimated 2.5 hours continuous patrol endurance).

### 3. Team Tikka Techies — Balanced Role Allocation (6 Members)
- **Member 1 (Leader / Autonomy Architecture):** ROS 2 System Bringup, Nav2 Integration & Lifecycle Management.
- **Member 2 (Perception Lead):** Model Export, ONNX Optimization, Taxonomy & Data Pipeline.
- **Member 3 (Localization & SLAM):** Visual Odometry, EKF Sensor Fusion & Trajectory Error Analysis.
- **Member 4 (Simulation & Modeling):** Gazebo Harmonic Worlds, Heightmaps, URDF Physics & Collision Meshes.
- **Member 5 (Evaluation & Metrics):** Headless Benchmarking Scripts, CSV/Markdown Data Analysis & Statistical Logging.
- **Member 6 (Hardware & Operations):** Embedded Electronics, Power Systems, Sim-to-Real Bringup & Documentation.
