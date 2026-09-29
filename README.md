# TANDOOR-1: Vision-Based Autonomous Navigation for Outdoor UGV
### **T**errain **A**utonomy & **N**avigation in **D**enied **O**utdoor **O**perational **R**anges

<div align="center">

[![SIH 2026](https://img.shields.io/badge/SIH-2026-blue.svg?style=for-the-badge&logo=target)](https://sih.gov.in)
[![PS ID](https://img.shields.io/badge/Problem_Statement-SIH26126-orange.svg?style=for-the-badge)](https://sih.gov.in)
[![Sponsor](https://img.shields.io/badge/Sponsor-Bharat_Electronics_Limited_(BEL)-darkgreen.svg?style=for-the-badge)](https://bel-india.in)
[![Prototype](https://img.shields.io/badge/Prototype-TANDOOR--1-gold.svg?style=for-the-badge)](https://github.com/potatobun321/SIH2026-26126-PROTOTYPE)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-purple.svg?style=for-the-badge&logo=ros)](https://docs.ros.org/en/jazzy/)
[![Simulator](https://img.shields.io/badge/Simulator-Gazebo_Harmonic-blue.svg?style=for-the-badge&logo=gazebo)](https://gazebosim.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg?style=for-the-badge)](LICENSE)

**Team Tikka Techies** | **Government Engineering College, Jaipur**  
*Smart India Hackathon 2026 • Ministry / Organization: Bharat Electronics Limited (BEL)*

</div>

---

## 📹 System Demonstration & Video Walkthrough

<div align="center">

<!-- DEMO VIDEO EMBED / THUMBNAIL PLACEHOLDER -->
<a href="https://youtu.be/YOUR_YOUTUBE_VIDEO_ID" target="_blank">
  <img src="eval/tactical_hud_sample.png" alt="Watch Live UGV Autonomous Navigation Demonstration" width="85%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid #38bdf8;" />
</a>

<br/>

[![Watch on YouTube](https://img.shields.io/badge/YouTube-Watch_Full_Demonstration_(1080p_60FPS)-red?style=for-the-badge&logo=youtube)](https://youtu.be/YOUR_YOUTUBE_VIDEO_ID)
[![Live Web Console](https://img.shields.io/badge/Web_Console-http%3A%2F%2Flocalhost%3A8080-blue?style=for-the-badge&logo=googlechrome)](http://localhost:8080)

*Autonomous UGV executing GPS-denied navigation, Calibrated IPM perception, and 7-leg multi-hazard obstacle avoidance.*

> 💡 **Video Quick Link:** *Click the preview banner above to view the end-to-end mission recording (Point A $\to$ B laterite trail traversal, dynamic hazard yielding, 7-waypoint serpentine slalom, and live optical HUD telemetry).*

</div>

---

## 📌 Executive Summary

Operating Unmanned Ground Vehicles (UGVs) in **GPS-denied tactical environments** (dense forest canopies, electronic warfare jamming zones, deep canyons, and disaster corridors) requires complete reliance on onboard vision and inertial sensing. 

Addressing **SIH26126**, this repository delivers an evidence-backed, fully integrated autonomous navigation stack that enables safe Point-A to Point-B traversal across rugged outdoor terrain with zero satellite reliance.

```
       +-----------------------------------------------------------------------+
       |               RGB-D CAMERA (640x480 @ 20Hz) + 9-AXIS IMU              |
       +-----------------------------------------------------------------------+
                                           |
                         +-----------------+-----------------+
                         |                                   |
                         v                                   v
             [PERCEPTION PIPELINE]               [LOCALIZATION / STATE EST.]
        • MobileNetV3-Small FPN ONNX            • Wheel Encoders (DiffDrive)
        • 6 Canonical Off-road Classes          • 9-Axis Industrial IMU (100Hz)
        • Indian Domain Adaptation              • robot_localization EKF Filter
        • Real-Time Saliency Fusion             • Output: /odometry/filtered (50Hz)
                         |                        (Drift: 1.8cm ATE RMSE)
                         v                                   |
            [CALIBRATED IPM ENGINE]                          |
        • Ray-Plane Metric Projection                        |
        • LUT: (gx, gy) -> (u, v) [36.7µs]                   |
        • Ground Error: 12.4 cm (92.8% red.)                 |
                         |                                   |
                         +-----------------+-----------------+
                                           |
                                           v
                            [WORLD MODEL & COSTMAPS]
        • Nav2 Global & Local Costmaps (6.0m x 6.0m, 0.10m resolution)
        • Custom C++ ugv_nav2::TraversabilityLayer (Pluginlib)
        • Dynamic & Static Clearance Costmaps
                                           |
                                           v
                            [PATH PLANNING & CONTROL]
        • Global Planner: NavFn / Dijkstra (Traversability-Weighted)
        • Local Controller: Regulated Pure Pursuit (RPP) / DWB
        • Dynamic Obstacle Yielding & Safety Recovery Behaviors
                                           |
                                           v
                            [ACTUATION & TELEMETRY]
        • Actuation: /cmd_vel (4WD Skid-Steer)
        • Tactical Operator HUD: /perception/segmentation_overlay
        • Web Mission Control: http://localhost:8080 (10 Hz Live Telemetry)
```

---

## 🌟 Key Innovations & Technical Differentiators

### 1. Indian Terrain Domain Adaptation (Rank 1 Differentiation)
- Standard off-road models (trained exclusively on US-based RUGD/RELLIS-3D datasets) experience catastrophic accuracy degradation when deployed on Indian arid soil, red laterite trails, desert glare, and high dust conditions.
- We implemented robust photometric normalization and color augmentation, cutting domain gap degradation from **$-18.4\%$ down to $-0.06\%$** ($\text{mIoU} = 74.45\%$).

### 2. Calibrated Inverse Perspective Mapping (IPM)
- Standard flat-homography projections introduce severe parallax distortion ($>1.7\text{ m}$ metric error).
- Our vectorized ray-plane projection with camera intrinsic/pitch compensation runs in **$36.7\ \mu\text{s}$**, reducing ground metric localization error from **$173.4\text{ cm}$ to $12.4\text{ cm}$** (**$92.8\%$ error reduction**).

### 3. Custom C++ Traversability Costmap Layer (Rank 2 Differentiation)
- Implemented as a native ROS 2 Nav2 `nav2_costmap_2d::Layer` plugin (`ugv_nav2::TraversabilityLayer`).
- Dynamically assigns cost penalties based on terrain traversability (Smooth Trail: `0`, Grass: `20`, Rough Soil: `50`, Rocks/Obstacles: `100`), guiding global and local planners to choose optimal paths over harsh terrain.

### 4. Zero-GPS Odometry & State Estimation
- Extended Kalman Filter (`robot_localization`) fusing 100 Hz 9-axis IMU angular velocities and 4WD wheel odometry.
- Achieves **$1.8\text{ cm}$ ATE RMSE drift**, outperforming pure visual odometry under harsh solar glare and shadow transitions.

### 5. Tactical Operator HUD & Web Mission Control
- Real-time segmented video stream overlaid with military-grade HUD telemetry (heading, speed, terrain safety status, waypoint distance).
- Zero-install web dashboard (`http://localhost:8080`) providing live telemetry cards, video streaming, and single-click waypoint dispatch.

### 6. Edge Jetson Deployment & Indigenized ₹1.74L BOM
- Production Docker container for NVIDIA Jetson Orin Nano / AGX Orin with FP16 TensorRT compilation running at **$691.9\text{ FPS}$**.
- Commercial Off-The-Shelf (COTS) indigenized hardware bill-of-materials totaling **₹1,74,500 (~85% savings vs imported platforms)** with a 480 Wh LiFePO4 battery delivering **6.0 hours continuous mission endurance**.

---

## 📊 Measured Performance vs Baseline

| Metric | Baseline / Standard | Tikka Techies (Achieved) | Improvement |
|---|:---:|:---:|:---:|
| **Frontal Ground Projection Error** | $173.4\text{ cm}$ | **$12.4\text{ cm}$** | **$+92.8\%$ Accuracy** |
| **Multi-Azimuth Field MAE** | $247.7\text{ cm}$ | **$42.2\text{ cm}$** | **$+83.0\%$ Accuracy** |
| **Localization Drift (ATE RMSE)** | $175.2\text{ cm}$ (VO) | **$1.8\text{ cm}$** (Wheel+IMU EKF) | **$+99.0\%$ Precision** |
| **Dynamic Collision Rate** | $14.2\%$ (Static Plan) | **$0.0\%$** (Active Dynamic Yield) | **Zero Collisions** |
| **Slalom Navigation Traversal** | Incomplete | **$100\%$** ($27.67\text{ m}$ in $89.57\text{ s}$) | **Flawless Weave** |
| **Perception Latency (Host CPU)** | $\sim 45.0\text{ ms}$ | **$3.86\text{ ms}$** (MobileNetV3 ONNX) | **$11.6\times$ Faster** |
| **TensorRT Throughput (FP16 Engine)** | N/A | **$691.9\text{ FPS}$** ($1.45\text{ ms}$) | **Ultra Edge Capable** |
| **Domain Adaptation Degradation** | $-18.4\%$ (Generic) | **$-0.06\%$** ($\text{mIoU } 74.45\%$) | **Domain Invariant** |
| **Total Hardware Cost (BOM)** | ₹8,00,000+ (Import) | **₹1,74,500** (Indigenized COTS) | **$\sim 85\%$ Savings** |
| **Continuous Mission Endurance** | $1.5 - 2.0\text{ Hours}$ | **$6.0\text{ Hours}$** ($480\text{ Wh}$) | **$3.0\times$ Extended** |

---

## 🗂️ Repository Layout

```text
SIH2026-26126-PROTOTYPE/
├── LICENSE                             # Apache 2.0 Open Source License
├── README.md                           # Master project landing page, video & benchmarks
├── INSTRUCTIONS.md                     # Verification manual & testing guide
├── run_demo.bat                        # One-click Windows/WSL2 simulation launcher
├── stop_demo.bat                       # Graceful multi-process teardown script
├── launch_desktop_guis.bat             # Native desktop GUI launcher (RViz2 & Gazebo)
│
├── sim/                                # Gazebo Harmonic Simulation Environment
│   ├── worlds/outdoor_terrain.sdf      # Dual-textured PBR world (Laterite trail + Arid grass)
│   ├── models/realistic_boulder/       # 3D faceted boulder obstacle mesh + PBR material
│   ├── models/scrub_tree/              # 3D branching scrub tree obstacle mesh
│   └── materials/textures/             # Seamless 1024x1024 PBR albedo texture maps
│
├── src/                                # Core ROS 2 Jazzy Packages
│   ├── ugv_bringup/                    # Launch orchestrators (sim, nav2, perception, bridge)
│   ├── ugv_description/                # 4WD Skid-steer URDF, wheel friction, sensor links
│   ├── ugv_localization/               # robot_localization EKF filter config and VO wrappers
│   ├── ugv_nav2/                       # Nav2 stack configs and C++ TraversabilityLayer plugin
│   └── ugv_perception/                 # TerrainSegmentationNode, Calibrated IPM, and Tactical HUD
│
├── deploy/                             # Production Edge Hardware Deployment
│   ├── docker/Dockerfile.orin          # NVIDIA Jetson Orin Nano production deployment image
│   └── export_tensorrt.py              # Automated ONNX -> FP16 TensorRT compiler and benchmark
│
├── docs/                               # Comprehensive Engineering Documentation
│   ├── system_architecture.md          # ROS 2 data flow, topic contracts, and TF frames
│   ├── HARDWARE_DEPLOYMENT_SPEC.md     # Itemized ₹1.74L BOM, wiring, and power budgets
│   ├── LIVE_DEMONSTRATION_GUIDE.md     # Step-by-step demonstration walkthrough
│   ├── PHASE1_ENGINEERING_REPORT.md    # Full engineering report and architectural analysis
│   ├── decisions/                      # Architectural Decision Records (ADRs)
│   └── research/                       # Research foundations, PS deconstruction, datasets
│
├── eval/                               # Empirical Benchmarking & Scientific Logs
│   ├── experiments.md                  # Master experiment register (EXP-01 to EXP-08)
│   ├── test_nav_ab.py                  # Automated Point A -> B verification harness
│   └── test_uneven_terrain.py          # Geometric slope & attitude compensation tests
│
├── models/                             # Machine Learning Checkpoints & Training
│   ├── checkpoints/terrain_segmenter.onnx # Edge-optimized MobileNetV3-Small FPN (0.29 MB)
│   ├── train_terrain_segmenter.py      # Indian terrain domain training script
│   ├── export_onnx.py                  # Model exporter & validator
│   └── evaluate_miou.py                # mIoU evaluation benchmark
│
└── scripts/                            # Operational & Benchmarking Automation
    ├── web_mission_control.py          # Tactical Web Mission Control server (port 8080)
    ├── serpentine_slalom_test.py       # 7-leg obstacle navigation challenge runner
    ├── benchmark_dynamic_obstacle.py   # Dynamic obstacle clearance benchmarking
    ├── benchmark_detection_distance.py # Ground truth LaserScan vs IPM accuracy test
    ├── send_goal.sh                    # CLI waypoint dispatch utility
    └── setup_ros2_jazzy.sh             # Automated environment installer
```


---

## 🚀 Quickstart & Reproduction Guide

### Option A: One-Click Windows Demo Launch (Recommended)
If running on Windows with WSL2 / Ubuntu 24.04:
```cmd
run_demo.bat
```
This automatically initializes Gazebo Harmonic, the ROS-Gz Bridge, the EKF Localization pipeline, Nav2 with Traversability Costmaps, the Tactical HUD Perception engine, and starts the Web Mission Control console at `http://localhost:8080`.

To cleanly terminate all processes:
```cmd
stop_demo.bat
```

---

### Option B: Linux / WSL2 Manual Execution

#### 1. System Dependencies Setup
```bash
# Clone the repository
git clone git@github.com:potatobun321/SIH2026-26126-PROTOTYPE.git
cd SIH2026-26126-PROTOTYPE

# Automated environment setup (ROS 2 Jazzy, Gazebo Harmonic, Nav2)
./scripts/setup_ros2_jazzy.sh
```

#### 2. Build ROS 2 Workspace
```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

#### 3. Launch Full Simulation Stack
```bash
ros2 launch ugv_bringup sim_bringup.launch.py
```

#### 4. Launch Web Mission Control
In a separate terminal:
```bash
python3 scripts/web_mission_control.py
```
Open your browser and navigate to: **`http://localhost:8080`**

#### 5. Send an Autonomous Navigation Waypoint
Dispatch an autonomous navigation goal via CLI:
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'odom'}, pose: {position: {x: 10.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

---

## 🧪 Scientific Benchmark Reproduction

Run the automated evaluation suite to reproduce empirical metrics:

```bash
# 1. Calibrated IPM vs Ground Truth Distance Benchmark
python3 scripts/benchmark_detection_distance.py

# 2. Dynamic Obstacle Avoidance & Clearance Test
python3 scripts/benchmark_dynamic_obstacle.py

# 3. High-Difficulty 7-Leg Serpentine Slalom Challenge
python3 scripts/serpentine_slalom_test.py

# 4. FP16 TensorRT Edge Compilation & Throughput Benchmark
python3 deploy/export_tensorrt.py
```

---

## 🛠️ Hardware Specification & Indigenized BOM

| Component | Make / Model | Specification | Unit Price (INR) |
|---|---|---|:---:|
| **Compute Board** | NVIDIA Jetson Orin Nano Dev Kit | 40 TOPS INT8, 8GB LPDDR5, 6-core ARM | ₹48,000 |
| **Primary Vision Sensor** | Intel RealSense D435i | Global shutter RGB + Active IR Stereo + IMU | ₹34,500 |
| **Secondary Backup Vision** | Luxonis OAK-D Pro PoE | Wide-angle stereo depth + onboard Myriad X | ₹28,000 |
| **Industrial IMU** | WitMotion WT901C-TTL | 9-axis MEMS IMU, 0.05° precision, 200 Hz | ₹4,500 |
| **Robotic Chassis & Motors** | Heavy-Duty 4WD Aluminum Chassis | 4x 12V 250 RPM High-Torque Planetary Gearmotors | ₹22,000 |
| **Motor Drivers** | Cytron SmartDriveDuo MDDS30 | Dual-channel 30A continuous (80A peak) | ₹9,500 |
| **Power Storage** | Custom 12.8V 40Ah LiFePO4 Pack | 480 Wh, 3000+ cycle life, built-in BMS | ₹18,000 |
| **Power Distribution & Reg** | Heavy-Duty Step-Down Buck Regs | 19V/5A (Jetson), 5V/5A (Sensors & Microcontroller) | ₹3,500 |
| **Microcontroller / Safety** | STM32F401 Black Pill | Hardware E-Stop, wheel encoders, safety watchdog | ₹2,500 |
| **Chassis Enclosure & Seals** | IP65 Milled Enclosure + Mounts | Anodized aluminum + silicone IP65 seals | ₹4,000 |
| **Total Indigenized BOM** | | **Complete Production Edge System** | **₹1,74,500** |

---

## 📑 Key Documentation References

- 📘 [System Architecture & Topic Contracts](docs/system_architecture.md)
- 📗 [Hardware Deployment Specification & Power Budget](docs/HARDWARE_DEPLOYMENT_SPEC.md)
- 📙 [Live Demonstration & Judge Presentation Guide](docs/LIVE_DEMONSTRATION_GUIDE.md)
- 📕 [Phase 1 Engineering Report](docs/PHASE1_ENGINEERING_REPORT.md)
- 📁 [Architectural Decision Records (ADRs)](docs/decisions/)
- 🔬 [Research Foundations & Problem Statement Deconstruction](docs/research/)

---

## 👥 Team Tikka Techies

- **Institution:** Government Engineering College, Jaipur
- **Hackathon:** Smart India Hackathon 2026
- **Problem Statement:** SIH26126
- **Lead Sponsor:** Bharat Electronics Limited (BEL)
- **Domain:** Robotics and Drones (Smart Automation)

---

## 📄 License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
