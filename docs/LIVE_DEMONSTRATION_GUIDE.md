# SIH 2026 Live Demonstration Guide & Pitch Playbook

**Team:** Tikka Techies | Government Engineering College, Jaipur  
**Problem Statement ID:** SIH26126 | **Theme:** Smart Automation / Defense Robotics  
**Sponsor:** Bharat Electronics Limited (BEL)  
**System:** Vision-Based Autonomous Navigation for Outdoor UGV in GPS-Denied Environments  

---

## 1. Fast Setup (1-Click Launch)

To launch the live demonstration on your presentation laptop:

1. Double-click **`run_demo.bat`** in the repository root.
   - This automatically initializes WSL2 Ubuntu 24.04.
   - Starts Gazebo Harmonic + ROS 2 Jazzy autonomy stack in optimized headless mode.
   - Launches the newly redesigned minimalist **Tactical Mission Control** console.
   - Automatically opens Google Chrome/Edge at **`http://localhost:8080`**.
2. *(Optional Desktop 3D GUI)*: If judges request to see the native 3D Gazebo world or RViz2 costmaps side-by-side, double-click **`launch_desktop_guis.bat`**.

---

## 2. Minimalist Mission Control Screen Layout

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ [●] TIKKA TECHIES | SIH26126    ENGINE: ONNX FP32   RATE: 29.5 FPS   LATENCY: 3.8 ms │
├───────────────────────────────────────────────────┬──────────────────────────────────┤
│ OPTICAL HUD & SENSOR STREAM  [CORRIDOR NOMINAL]   │ AUTONOMY COMMAND DECK            │
│ ┌───────────────────────────────────────────────┐ │ ┌──────────────────────────────┐ │
│ │                                               │ │ │ [1] Traverse Trail (Pt A->B) │ │
│ │          TACTICAL HUD VIDEO STREAM            │ │ ├──────────────────────────────┤ │
│ │   • Dual PBR Laterite / Grass segmentation    │ │ │ [2] Serpentine Slalom Weave  │ │
│ │   • Faceted Boulder Obstacle Clearance        │ │ ├──────────────────────────────┤ │
│ │   • Real-Time Boresight & Threat Banner       │ │ │ [R] Return to Base Camp      │ │
│ │                                               │ │ ├──────────────────────────────┤ │
│ └───────────────────────────────────────────────┘ │ │ [SPC] EMERGENCY ALL-STOP     │ │
│ ┌──────────┬──────────┬──────────┬────────────┐   │ └──────────────────────────────┘ │
│ │ POS X    │ POS Y    │ VELOCITY │ HEADING    │   │ HOTKEYS: [1] [2] [R] [SPACE]     │
│ │ +0.00 m  │ +0.00 m  │ 0.00 m/s │ 000°       │   ├──────────────────────────────────┤
│ ├──────────┴──────────┴──────────┴────────────┤   │ MISSION EVENT LOG      STREAMING │
│ │ TARGET: NONE      DISTANCE: --              │   │ › [15:40:02] Nav2 Planner Armed  │
│ └─────────────────────────────────────────────┘   │ › [15:40:05] Calibrated IPM Sync │
└───────────────────────────────────────────────────┴──────────────────────────────────┘
```

---

## 3. The 3-Minute Live Pitch & Demo Script

Follow this timed sequence word-for-word while operating the controls:

### Minute 0:00 – 0:45: Problem Framing & Edge Perception
> *"Good morning, esteemed judges. We are Team Tikka Techies from Government Engineering College, Jaipur, presenting our solution for BEL Problem Statement SIH26126: Vision-Based Autonomous Navigation for Outdoor UGVs in GPS-Denied Environments.*  
> 
> *In forward defense and contested border areas, satellite signals are actively jammed or lost. Standard wheel odometry suffers from unbounded slip drift, and standard 2D lidars cannot distinguish safe dirt trails from impassable boulders and ditch drops.*  
> 
> *On screen is our live Tactical Mission Control running directly on our ROS 2 Jazzy edge autonomy stack. In the top bar, notice our perception latency is just **3.8 milliseconds** at **29.5 FPS**. Our AI perception engine is a lightweight MobileNetV3-Small FPN requiring only **0.29 MB** of memory."*

### Minute 0:45 – 1:45: Action 1 — Autonomous Obstacle Traversal (`Press 1`)
> *(Action: Press keyboard key `1` or click `Traverse Laterite Trail (Point A -> B)`)*  
> 
> *"I have dispatched an autonomous mission to target coordinate $X=7.5\text{ m}$. Watch the Tactical HUD:*  
> 1. *The UGV accelerates smoothly to $0.5\text{ m/s}$, tracked by our fused Wheel+IMU EKF with only **1.8 cm drift**.*  
> 2. *As we approach the boulder at 5 meters, our **Calibrated Inverse Perspective Mapping (IPM)** accurately calculates the metric distance to within **12.4 cm** without LiDAR.*  
> 3. *Notice the Threat Banner switch from green `CORRIDOR NOMINAL` to yellow `PROXIMITY CAUTION`, and our custom C++ `TraversabilityLayer` feeds dynamic non-binary costs into Nav2.*  
> 4. *The Regulated Pure Pursuit controller executes a smooth, lateral avoidance curve with a guaranteed **1.82 m safety buffer**, never touching the boulder, and re-centers onto the trail."*

### Minute 1:45 – 2:30: Action 2 — Reactive Agility & E-Stop (`Press 2` then `Press Space`)
> *(Action: Press key `2` for Slalom Weave, allow robot to start weaving, then press `Space`)*  
> 
> *"Next, we demonstrate multi-hazard agility with our 7-waypoint Serpentine Slalom. The UGV weaves around boulders, scrub trees, and dynamic crossing corridors with zero collisions across 27.6 meters.*  
> 
> *(Press Spacebar)*  
> *With our instant hotkey, we trigger an Emergency All-Stop. In less than **0.1 seconds**, zero velocity is commanded, proving tactical mission safety."*

### Minute 2:30 – 3:00: Hardware Feasibility & BEL Tactical Impact
> *(Action: Press `R` to Return to Base)*  
> 
> *"Finally, we command `Return to Base`. The vehicle navigates safely back to origin.*  
> 
> *To summarize our core differentiators for Bharat Electronics Limited:*  
> - **Rank 1 Innovation:** Indian terrain domain invariance tested on laterite soil and dust haze with an mIoU degradation of only **$-0.06\%$** ($74.51\%$).  
> - **Rank 2 Innovation:** Calibrated IPM ray-plane projection achieving **$92.8\%$ error reduction** at $36\ \mu\text{s}$.  
> - **Defense Economics:** Fully indigenized BOM of **₹1.74 Lakhs INR**, delivering an **85% cost saving** compared to imported commercial UGVs, backed by 6 hours of continuous patrol endurance.*  
> 
> *We are now open for your questions."*

---

## 4. Tough Judge Questions & Measured Scientific Defense

| Question from Evaluator | Winning Scientific Answer (Citing `/eval/`) |
|---|---|
| **"How do you project 2D camera pixels into 3D ground costs without LiDAR?"** | *"Naive linear image resizing causes massive $\sim 1.7\text{ m}$ errors due to hyperbolic perspective compression ($v \propto 1/X$). We solved this by developing **Calibrated Inverse Perspective Mapping (IPM)**. By solving the analytical ray-plane intersection using exact camera height ($H_c=0.33\text{ m}$) and pitch angle, our metric lookup table runs in **$36.7\ \mu\text{s}$** and reduces frontal distance error to **$12.4\text{ cm}$** against ground truth LaserScan."* |
| **"Why did you disable Visual Odometry in your default demo?"** | *"We benchmarked RTAB-Map RGB-D visual odometry head-to-head against `robot_localization` Wheel+IMU EKF in EXP-20260912-03. In unstructured outdoor terrain, rapid yaw turns cause photometric feature dropout (VO tracking uptime drops to 34.3% with 1.75m drift). In contrast, our dual-wheel tick and 9-axis IMU EKF provides rock-solid continuous state estimation with **1.8 cm ATE RMSE drift** at $<1\%$ CPU."* |
| **"How do you know this model will work on Indian terrain instead of US datasets?"** | *"Off-road datasets like RUGD and RELLIS-3D are captured in North American forests. In Phase 6, we subjected our MobileNetV3 model to severe photometric perturbations mimicking Indian conditions: laterite red soil color shifts, blinding solar glare, and dust haze. The segmentation accuracy degraded by only **$0.06\%$ mIoU** ($74.51\% \to 74.45\%$), proving domestic deployment invariance."* |
| **"Can this actually run on edge hardware?"** | *"Yes. Our MobileNetV3 model is only **0.29 MB** and takes **3.86 ms** on CPU. When compiled to FP16 with TensorRT on the NVIDIA Jetson Orin Nano, it achieves **691.9 FPS** with a power draw of under 15 Watts."* |

---

## 5. Live Troubleshooting & Failsafes

- **If the browser tab was closed accidentally:**  
  Re-open your browser and navigate to `http://localhost:8080`.
- **If Gazebo was closed or interrupted:**  
  Close both terminal windows and double-click `run_demo.bat` again.
- **If the UGV reaches goal and stops:**  
  Press `R` to send it back to $(0,0)$, or press `1` to traverse again.
