# ADR-0001: Baseline Architecture Candidates for Phase 1 Vertical Slice

- **Status:** CANDIDATE / PROPOSED
- **Date:** 2026-09-11
- **Deciders:** Tikka Techies (Team & AI Collaborators)
- **Relevant Requirements:** R1–R7 (`PS26126_DECONSTRUCTION.md`)
- **Related Documents:** `AGENTS.md`, `TECHNOLOGY_COMPARISON.md`, `ENGINEERING_ROADMAP.md`, `RESEARCH_GAPS.md`

---

## 1. Context and Problem Statement
SIH26126 ("Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor environment", BEL) requires an outdoor, vision-centric autonomous UGV navigation stack. 

Per `ENGINEERING_ROADMAP.md`, the team's core principle is:
> *Build one thin vertical slice first — camera → basic perception → localization → planner → controller → robot moves — before deepening any single subsystem.*

Before writing Phase 1 code, we must baseline the candidate middleware, simulation platform, baseline localization, and planning stack, while explicitly noting that advanced components (custom traversability segmentation, visual SLAM, custom costmaps) will be layered onto this running slice in Phases 2–4.

---

## 2. Considered Alternatives

### 2.1 Middleware
- **Option A (Candidate Choice):** ROS 2 Jazzy Jalisco (Ubuntu 24.04 LTS target, supported through 2029) or ROS 2 Humble Hawksbill (Ubuntu 22.04 LTS target).
  - *Trade-off:* Humble has historically broader community package maturity for niche SLAM wrappers; Jazzy is current LTS.
  - *Baseline decision:* Target ROS 2 Humble/Jazzy compatibility; verify Gazebo Harmonic + Nav2 support.

### 2.2 Simulation Environment
- **Option A (Candidate Choice):** Gazebo (Harmonic / modern Ignition line) with heightmap terrain and standard sensor plugins (`ros_gz_bridge`).
- **Option B:** Webots (quicker setup, less seamless Nav2 outdoor ecosystem).
- **Option C:** Unity/Unreal or Isaac Sim (high visual fidelity for vision testing, but heavy compute barrier and slower initial vertical slice integration).
  - *Baseline decision:* Gazebo Harmonic for the primary simulation and end-to-end integration pipeline. High-fidelity visual engines reserved only as potential stretch experiments if compute permits.

### 2.3 Baseline Localization (Phase 1 Slice)
- **Option A (Candidate Choice):** Wheel Odometry + IMU fusion via `robot_localization` (EKF).
- **Option B:** Direct integration of visual SLAM (RTAB-Map / ORB-SLAM3) in Phase 1.
  - *Baseline decision:* Option A for Phase 1. As dictated by `ENGINEERING_ROADMAP.md`, Phase 1 must not be blocked on visual SLAM tuning. Wheel+IMU provides the reliable baseline ground-truth/fallback against which visual SLAM (RTAB-Map / VINS) will be benchmarked in Phase 3.

### 2.4 Planning & Control Stack
- **Option A (Candidate Choice):** Nav2 with standard Costmap 2D (Static/Obstacle/Inflation layers) and DWB / MPPI controller.
- **Option B:** Custom path planner.
  - *Baseline decision:* Nav2 is the industry standard with high maturity and modular plugin support. Custom traversability-aware costmaps will be developed as a Nav2 plugin in Phase 4 (Rank 2 research gap).

### 2.5 Perception Layer (Phase 1 Slice)
- **Option A (Candidate Choice):** Minimal pass-through / obstacle point-cloud or range projection stub.
  - *Baseline decision:* For Phase 1, perception will use a minimal drivability/obstacle projection to prove data contract between simulated camera/depth sensor and the local costmap. Deep learning segmentation (RUGD/RELLIS-3D pretrained YOLO-seg / BiSeNet) replaces this stub in Phase 2.

---

## 3. Decision Outcome
Adopt the following candidate pipeline for the **Phase 1 Minimal Vertical Slice**:
1. **Middleware:** ROS 2 (Humble / Jazzy).
2. **Simulation:** Gazebo Harmonic with a simple outdoor heightmap, a differential/skid-steer UGV model, and simulated camera + IMU + wheel encoders.
3. **Localization:** `robot_localization` (EKF fusing wheel odometry + IMU).
4. **Planning & Control:** Nav2 with default costmap layers and standard controller.
5. **Perception:** Trivial depth/obstacle bridge to costmap.

---

## 4. Exit Criteria for Phase 1
- UGV spawns in Gazebo outdoor environment.
- Nav2 successfully commands the UGV from Point A to Point B around a simple obstacle without human teleoperation.
- All topics and TF frames conform to standard REP 103 / REP 105 conventions (`map` -> `odom` -> `base_link` -> sensor frames).
- Pipeline runs end-to-end and metrics (A→B traversal success, navigation duration, path length) are recorded.
