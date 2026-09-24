# INSTRUCTIONS.md — Operational & Verification Manual

**Team:** Tikka Techies | Government Engineering College, Jaipur  
**Competition:** Smart India Hackathon 2026 | Problem Statement **SIH26126** (Bharat Electronics Limited — BEL)  
**System:** Vision-Based Autonomous Navigation for Outdoor UGV in GPS-Denied Environments  

---

## 1. Quickstart: Launching the System

To run the complete system with the **Tactical Web Mission Control Dashboard**, follow these 3 steps:

### Step 1: Launch the Optimized Simulation Stack
Open a WSL2 terminal (Ubuntu-24.04) and execute:

```bash
cd /mnt/c/Users/GIGA/Desktop/sih2026
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Launches Gazebo Harmonic, 4WD UGV, Calibrated IPM Perception, EKF, and Nav2
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True
```

> **Optimization Note:** By default, heavy RTAB-Map visual odometry is disabled (`enable_vo:=False`), reducing CPU utilization by ~40% while preserving high-precision **1.8 cm ATE RMSE** state estimation via Wheel+IMU EKF.

### Step 2: Launch the Web Mission Control Console
In a second WSL2 terminal (or background session):

```bash
cd /mnt/c/Users/GIGA/Desktop/sih2026
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Serves the real-time Tactical Mission Control console on port 8080
python3 scripts/web_mission_control.py
```

### Step 3: Open Mission Control in Your Web Browser
Open your Windows web browser (Google Chrome, Microsoft Edge, or Firefox) and navigate to:

👉 **`http://localhost:8080`**

---

## 2. Using the Web Mission Control Dashboard

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  TIKKA TECHIES | SIH26126 RECON               ENGINE: ONNX   RATE: 29.5 FPS  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   [Tactical HUD Video Stream: 512x384 @ 16 FPS]       [Command Deck]         │
│   • Live PBR Textured Laterite Trail                   [🎯 Point A -> B]     │
│   • 3D Faceted Boulder Obstacle                        [🌀 Slalom Weave]     │
│   • Color Segmentation (Trail/Grass/Rock)              [🏠 Return to Base]   │
│   • Threat Banner: "PROXIMITY CAUTION @ 3.20m"         [🛑 EMERGENCY STOP]   │
│   • Crosshair Reticle & Corner Brackets                                      │
│                                                                              │
│   [Telemetry Cards: X: 0.00m | Y: 0.00m | Speed: 0.00m/s | Heading: 000°]   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Interactive Command Deck Controls
- **`🎯 Traverse Laterite Trail (Point A → B)`**: Dispatches an autonomous mission to target coordinate $(X=7.5\text{ m}, Y=0.0\text{ m})$. The UGV accelerates, visually detects the boulder at $X=5.0\text{ m}$, smoothly executes a lateral avoidance curve around it, and re-centers onto the trail.
- **`🌀 Execute Serpentine Slalom Weave`**: Dispatches the advanced 7-leg obstacle slalom weaving around trail markers, the dynamic moving hazard corridor, and between boulders and trees.
- **`🏠 Return to Base Camp`**: Dispatches a return trajectory back to coordinate $(X=0.0\text{ m}, Y=0.0\text{ m})$, orienting the UGV to face forward.
- **`🛑 EMERGENCY ALL-STOP`**: Instantly publishes zero velocity commands (`/cmd_vel`) to cancel all active trajectories and halt the vehicle in $< 0.1\text{ s}$.

### Reading the Tactical HUD Overlay
- **Top Telemetry Bar**: Shows active inference mode (`[ONNX]`), instantaneous velocity ($v$), fused compass heading ($\theta$), framerate, and node latency.
- **Threat Alert Banner**:
  - 🟢 **`CORRIDOR NOMINAL: CLEAR PATHWAY`**: Forward sector is free of hazards.
  - 🟡 **`PROXIMITY CAUTION: HAZARD @ X.XXm | TRACKING`**: Obstacle detected ahead in safety corridor; tracking clearance.
  - 🔴 **`THREAT ALERT: HAZARD @ X.XXm | REPLANNING`**: Lethal hazard $< 1.2\text{ m}$; dynamic avoidance path planner engaged.
- **Center Boresight Crosshairs**: Visual targeting reticle aligned with camera optical axis.
- **Bottom Cost Legend**: Swatches displaying cost assignments (Trail: 0, Grass: 20, Bush: 70, Obstacle: 100).

---

## 3. Desktop 3D Visualization (RViz2 & Gazebo GUI)

If you wish to view 3D costmaps, particle point clouds, and path plans side-by-side with the web stream:

### Launch RViz2 Navigation Profile (via WSLg)
In a separate terminal:
```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Opens native desktop RViz2 window with preconfigured UGV layers
bash scripts/view_nav.sh
```

### View Native Gazebo 3D Simulation Window
To see the full 3D Gazebo rendering window on your desktop, launch with `headless:=False`:
```bash
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=False
```
*(Or launch client GUI separately while server runs: `gz sim -g`)*

---

## 4. Running Automated Scientific Benchmarks

Every performance claim in our presentation is supported by an automated benchmark script in `scripts/`:

### 1. High-Difficulty 7-Leg Serpentine Slalom Test
```bash
# Runs full 7-waypoint obstacle course, records duration, clearance, and drift
python3 scripts/serpentine_slalom_test.py
```

### 2. Dynamic Moving Hazard Clearance Benchmark
```bash
# Benchmarks reactive replanning against moving dynamic obstacles (Phase 5)
python3 scripts/benchmark_dynamic_obstacle.py
```

### 3. Metric Ground Projection & IPM Calibration Test
```bash
# Compares costmap obstacle positions against Ground Truth LaserScan range
python3 scripts/benchmark_detection_distance.py
```

### 4. Standalone Tactical HUD Unit Test
```bash
# Verifies HUD overlay drawing and costmap generation in a headless test harness
python3 eval/test_tactical_hud.py
```

### 5. CLI Waypoint Dispatch Utility
If you want to send arbitrary coordinates via command line:
```bash
# Syntax: bash scripts/send_goal.sh <X_COORDINATE> <Y_COORDINATE> [OPTIONAL_YAW_RAD]
bash scripts/send_goal.sh 6.5 1.2
```

---

## 5. Performance Optimization & Edge Deployment

### Enabling Visual Odometry Benchmark (Optional)
By default, heavy RTAB-Map RGB-D odometry is turned off to save CPU. If you wish to run Phase 3 localization benchmarks comparing VO against EKF:
```bash
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py enable_vo:=True
```

### Compiling TensorRT Engine for Jetson Orin
To compile the MobileNetV3 ONNX model into an FP16 TensorRT engine:
```bash
python3 deploy/export_tensorrt.py --onnx models/checkpoints/terrain_segmenter.onnx --fp16
```

### Building the Production Docker Container
On an NVIDIA Jetson Orin Nano / AGX Orin:
```bash
cd deploy/docker
docker build -t sih26126-ugv:latest -f Dockerfile.orin ../..
docker run --net=host --runtime=nvidia sih26126-ugv:latest
```

---

## 6. Troubleshooting & FAQ

### Q1: The browser button was clicked, but the UGV didn't move immediately.
**Cause:** Nav2 lifecycle nodes take approximately 4–6 seconds after simulation launch to transition to the `ACTIVE` state.  
**Resolution:** Check the terminal log on the right side of the dashboard. Ensure the log states `Nav2 accepted goal`. If Nav2 is still initializing, wait 5 seconds and click the button again, or use the CLI utility: `bash scripts/send_goal.sh 7.5 0.0`.

### Q2: Port 8080 is already in use by another application.
**Resolution:** Launch the mission control server on an alternate port (e.g., 8090):
```bash
python3 -c "from scripts.web_mission_control import main; import sys; main()"
```
Or edit port in `scripts/web_mission_control.py` line 694.

### Q3: How do I cleanly stop all background processes?
Run the following cleanup command in WSL:
```bash
pkill -9 -f gz-sim; pkill -9 -f ros2; pkill -9 -f web_mission_control
```
