# PS26126 Deconstruction

**PS Code:** SIH26126  
**Track / Category:** Software  
**Theme:** Smart Automation (Domain: Robotics and Drones)  
**Sponsor Organization:** Bharat Electronics Limited (BEL)  
**Title:** "Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor environment"  
**Submission Deadline:** 30 September 2026 (Idea Stage, max 6 slides, AICTE PPT template in PDF)

---

## 0. Source Status — VERIFIED

- **CONFIRMED (Official SIH 2026 Problem Statement):**
  - **Background:** Outdoor Unmanned Ground Vehicles (UGVs) face unpredictable terrain, changing light, and unreliable GPS signals. To achieve true autonomy in applications like search-and-rescue, agriculture, or delivery, UGVs must rely on onboard computer vision. Visual perception provides a cost-effective, data-rich way for vehicles to understand and safely navigate complex, unstructured outdoor surroundings.
  - **Description & Objective:** The objective is to build an autonomous navigation system for an Unmanned Ground Vehicle (UGV) operating in a GPS-denied outdoor environment, relying primarily on onboard camera feeds.
  - **Key Challenges Specified:**
    1. *Path Detection:* Real-time identification and classification of safe, traversable paths vs hazards (e.g., rocks, ditches, trees).
    2. *Visual Localization:* Estimating the UGV’s position and orientation accurately without GPS, using visual information.
    3. *Collision Avoidance:* Dynamically routing the vehicle around unexpected obstacles to reach a target destination.
  - **Expected Software Components:**
    - *Perception AI:* Lightweight model for detecting obstacles and paths.
    - *Visual SLAM / Odometry:* Pipeline capable of tracking the vehicle's movement.
    - *Path Planner:* Algorithm translating perception and localization data into actionable wheel or motor commands.
  - **Primary Success Criterion:** Collision-free autonomous navigation from Point A to Point B across varying outdoor scenarios.

---

## 1. Deconstruction of Problem Scope & Constraints

- **Software Track Deliverable:** The primary evaluation focuses on the software stack running in high-fidelity simulation (Gazebo / ROS 2). Physical deployment is a powerful Stage 2 stretch goal.
- **Vision-Based Primary Modality:** Camera(s) (monocular, stereo, or RGB-D) must serve as the primary sensor for perception, traversability, and visual localization. Auxiliary inertial (IMU) and wheel odometry are standard and permissible for fusion.
- **GPS-Denied Outdoor Environment:** Operation must not rely on satellite navigation. The system must navigate through unstructured, uneven terrain (vegetation, soil, rocks, ditches) with variable lighting and potential visual drift.
- **Autonomy:** Closed-loop, full autonomy without human-in-the-loop teleoperation during A→B navigation.

---

## 2. Requirements Matrix

| ID | Requirement | Status | Source |
|---|---|---|---|
| R1 | System must navigate a UGV from start to goal (Point A → Point B) safely | **CONFIRMED** | Official PS Success Criterion |
| R2 | Primary perception & localization must be **vision-based** | **CONFIRMED** | Official PS Title & Description |
| R3 | Operation must occur in **outdoor, unstructured terrain** | **CONFIRMED** | Official PS Title & Background |
| R4 | Navigation must be **autonomous** (no human teleoperation) | **CONFIRMED** | Official PS Title & Description |
| R5 | System must handle **path detection** (traversable vs rocks, ditches, trees) | **CONFIRMED** | Official PS Challenge 1 |
| R6 | System must achieve **visual localization** without GPS | **CONFIRMED** | Official PS Challenge 2 |
| R7 | System must perform **dynamic collision avoidance** & rerouting | **CONFIRMED** | Official PS Challenge 3 |
| R8 | Include lightweight perception AI, visual SLAM/odometry, & path planner | **CONFIRMED** | Official PS Expected Solution |
| R9 | Working simulation demonstration for software track | **CONFIRMED** | SIH Software Track Protocol |

---

## 3. Technical Subproblems & Mapping

- **P1 — Terrain & Traversability Segmentation:** Distinguishing drivable ground from non-drivable ground (soil, grass, trails vs rocks, ditches, water) from camera imagery.
- **P2 — Obstacle Detection & Ranging:** Detecting static and sudden/dynamic obstacles, determining distance and clearance.
- **P3 — GPS-Denied Visual Localization:** Estimating vehicle pose ($x, y, z, \text{yaw}$) over time from camera and IMU data without GPS drift.
- **P4 — Traversability-Aware Mapping:** Building a graded costmap (e.g., Nav2 custom costmap layer) that reflects terrain difficulty rather than a binary flat obstacle map.
- **P5 — Global & Local Path Planning:** Computing a global optimal path and dynamic local obstacle-avoidance maneuvers.
- **P6 — Motion Control:** Translating path plans into vehicle drive commands (`geometry_msgs/Twist` to motor controllers / Gazebo diff-drive plugin).
- **P7 — Environmental Robustness:** Handling outdoor lighting changes (glare, shadows, dusk) and unstructured surface changes.
- **P8 — Edge Compute Efficiency:** Ensuring perception AI and SLAM run within latency constraints of edge compute (e.g., NVIDIA Jetson).

---

## 4. Evaluation & SIH Presentation Alignment

- **Demonstration:** Autonomous traversal of a simulated outdoor course in Gazebo with real-time internal state visualization in RViz2 or Foxglove (costmap heatmaps, visual feature points, planned trajectory).
- **Submission:** AICTE 6-slide deck strictly adhering to the SIH protocol, backed by measured metrics (mIoU, tracking ATE, A→B success rate) produced from our Phase 1 vertical slice.
