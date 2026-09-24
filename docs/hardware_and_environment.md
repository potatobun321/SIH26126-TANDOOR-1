# Hardware & Environment Specifications

This document defines the development environment, sensor specifications, and physical target hardware architecture for SIH26126.

---

## 1. Development & Simulation Host Setup

| Component | Specification | Operational Role |
|---|---|---|
| **Host Operating System** | Windows 11 Pro 64-bit | Primary workstation |
| **Virtualization** | WSL2 (Linux 6.6.87.2-microsoft-standard) | Native Linux subsystem for ROS 2 |
| **Linux Distribution** | Ubuntu 24.04 LTS (Noble Numbat) | Host OS for ROS 2 Jazzy & Gazebo Harmonic |
| **Primary GPU** | NVIDIA GeForce RTX 5060 Ti (16 GB GDDR7) | Deep learning model training & Gazebo rendering |
| **GPU Driver & CUDA** | Driver 596.21 / CUDA 13.2 | Direct GPU passthrough into WSL2 |
| **Display Server** | WSLg (Wayland / X11 Direct Passthrough) | Hardware-accelerated rendering for Gazebo & RViz2 |

---

## 2. Target Edge Hardware (Phase 7 Sim-to-Real & Feasibility)

To answer the judging criteria on **Technical Credibility & Feasibility** (Slide 5 of AICTE deck), the system is architected for low-power edge compute:

### 2.1 Onboard Compute
- **Primary Embedded Computer:** NVIDIA Jetson Orin Nano (8 GB) or Jetson Orin NX (16 GB).
- **Power Envelope:** 7W to 25W configurable TDP.
- **AI Acceleration:** 40 to 100 TOPS (INT8) via TensorRT / Deep Learning Accelerator (DLA).
- **Storage:** 512 GB NVMe M.2 SSD.

### 2.2 Sensor Suite
- **Primary Vision Sensor:** Stereolabs ZED 2i or Intel RealSense D435i
  - *Modality:* Synchronized Global Shutter Stereo RGB-D + 6-DOF IMU.
  - *Range:* 0.3 m to 20 m outdoor depth sensing.
  - *Field of View:* ~110° horizontal.
  - *Enclosure:* IP66 water/dust resistant for outdoor rangeland/monsoon conditions.
- **Auxiliary Odometry:** Hall-effect wheel encoders (500–1000 CPR) on drive motors.

### 2.3 Mobile Base Platform
- **Drive Type:** 4-Wheel Skid-Steer / Differential Drive.
- **Payload Capacity:** 15–25 kg.
- **Motor Control:** Dual-channel brushless DC motor controller communicating over CAN bus or UART (`/cmd_vel` subscriber).
- **Power System:** 4S (14.8V) or 6S (22.2V) 10,000 mAh LiPo with isolated DC-DC step-down converters (19V for Jetson, 12V for sensors, 5V for logic).

---

## 3. Real-Time Latency & Compute Budgets

| Subsystem | Target Frequency | Maximum Allowed Latency | Expected Host Performance (RTX 5060 Ti) | Expected Edge Performance (Orin Nano) |
|---|---|---|---|---|
| Camera RGB Stream | 30 Hz | 33 ms | < 5 ms | < 15 ms |
| Terrain Segmentation AI | 20–30 Hz | 50 ms | ~ 8 ms (PyTorch / TensorRT) | ~ 25 ms (TensorRT INT8) |
| EKF Pose Estimation | 50 Hz | 20 ms | < 2 ms | < 5 ms |
| Costmap Update | 10 Hz | 100 ms | < 10 ms | < 25 ms |
| Local Controller (`/cmd_vel`) | 20 Hz | 50 ms | < 5 ms | < 15 ms |
| **End-to-End Latency** | **Full Loop** | **< 100 ms** | **~ 25 ms** | **~ 70 ms** |
