# AGENTS.md — Tikka Techies | SIH 2026 | PS26126

**Version:** 1.3 — Unified Technical Architecture & Operating Manual  
**Status:** AUTHORITATIVE (Single Source of Truth)

This file is the shared operating context for every human and AI agent working on this repository. Read this in full before touching code, docs, or architecture. This document synthesizes the engineering roadmap, confirmed problem statement requirements, research documentation, and AI-agent governance rules.

---

## 0. Project Identity

- **Team:** Tikka Techies
- **Institution:** Government Engineering College, Jaipur
- **Hackathon:** Smart India Hackathon 2026
- **Problem Statement ID:** SIH26126
- **Organization / Sponsor:** Bharat Electronics Limited (BEL)
- **Theme:** Smart Automation
- **Category:** Software
- **Domain:** Robotics and Drones
- **Title:** Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor environment

### Mission Statement
Build a credible, evidence-backed, vision-based autonomous navigation system for an outdoor Unmanned Ground Vehicle (UGV) operating in GPS-denied environments. The deliverable is demonstrated first in end-to-end simulation (Gazebo/ROS 2), with a clear path to physical hardware. The system is not a collection of disconnected AI models; it is an integrated autonomous system whose primary responsibility is safe, collision-free navigation from Point A to Point B.

---

## 1. Source-of-Truth Hierarchy

When information conflicts, strictly enforce this precedence:
1. **Official SIH sources** (`sih.gov.in`, official SPOC announcements, and AICTE 6-slide template).
2. **Official BEL / government / ministry documentation**.
3. **Official software, package, and dataset documentation** (ROS 2, Nav2, Gazebo, PyTorch, RUGD/RELLIS-3D).
4. **Primary peer-reviewed research papers**.
5. **Verified past SIH winner repositories & decks**.
6. **Reputable secondary sources & technical articles** (marked as mirrors/secondary).
7. **AI-generated summaries** — *never treated as primary evidence; assumptions must be explicitly labeled*.

---

## 2. Confirmed Problem Statement Requirements

Cross-verified from official mirrors and secondary aggregators (see `docs/research/PS26126_DECONSTRUCTION.md` and `docs/research/SOURCE_REGISTER.md`).

### 2.1 Core Operational Challenges
- **Path Detection:** Real-time identification and classification of safe, traversable paths vs hazards (e.g., rocks, ditches, trees, drop-offs, vegetation).
- **Visual Localization:** Accurate UGV position and orientation estimation without GPS, using onboard visual (camera) and inertial sensing.
- **Collision Avoidance:** Dynamic rerouting around unexpected static and moving obstacles to reach the target destination.

### 2.2 Expected Software Architecture Components
1. **Perception AI:** Lightweight model for outdoor obstacle detection and terrain traversability segmentation.
2. **Visual SLAM / Odometry:** Pipeline tracking vehicle movement and visual ego-motion in GPS-denied terrain.
3. **Path Planner:** Global and local planner converting traversability/localization data into actionable motor/wheel commands (`cmd_vel`).

### 2.3 Primary Success Criterion
Collision-free autonomous navigation from Point A to Point B across varying outdoor scenarios under GPS-denied conditions.

---

## 3. Autonomy System Architecture

```text
CAMERA / ONBOARD SENSORS (RGB / Stereo / IMU)
       |
       v
PERCEPTION LAYER
       |
       +----> Terrain / Traversability (RUGD / RELLIS-3D segmentation)
       +----> Obstacle Detection (Lightweight instance seg / bounding boxes)
       +----> Depth / Geometry (Stereo depth / Monocular estimation)
       |
       v
WORLD MODEL & SENSOR FUSION
       |
       +----> Traversability Costmap Layer (Perception -> Costmap plugin)
       +----> Obstacle Costmap Layer (Static & Dynamic clearance)
       + <--- VISUAL LOCALIZATION / EKF (Visual Odometry + IMU fusion)
       |
       v
PATH PLANNING (Nav2)
       |
       +----> Global Planner (Traversability-weighted Dijkstra / NavFn / Smac)
       +----> Local Planner / Controller (DWB / MPPI - dynamic avoidance)
       |
       v
MOTION CONTROL & ACTUATION
       |
       v
UGV (Simulated in Gazebo Harmonic / Physical Hardware)
       |
       +------------------------------------+
                                            |
                                            v (closed loop feedback)
                                     CAMERA / SENSORS
```

All subsystems must communicate via standard ROS 2 interfaces, allowing individual components to be benchmarked and swapped without rewriting the system.

---

## 4. Technology Candidate Stack

All entries are CANDIDATES until validated by Phase 0/1 experiments (see `docs/research/TECHNOLOGY_COMPARISON.md`):

| Layer | Primary Candidate | Fallback / Alternative | Key Constraint / Trade-off |
|---|---|---|---|
| **Middleware** | ROS 2 Humble / Jazzy | None (ROS 1 EOL) | Jazzy is current LTS (Ubuntu 24.04); Humble has wider existing package wrappers. |
| **Simulation** | Gazebo (Harmonic) | Webots / Isaac Sim | Native `ros_gz_bridge`, outdoor heightmap terrain support. |
| **Planning & Control** | Nav2 Stack | Custom Planner (discouraged) | Pluggable costmap layers, DWB/MPPI controllers. Standard ROS 2 navigation backbone. |
| **Localization** | `robot_localization` (Wheel+IMU EKF) | RTAB-Map / VINS-Fusion / ORB-SLAM3 | EKF is the robust Phase 1 baseline; visual SLAM benchmarked head-to-head in Phase 3. |
| **Perception** | Lightweight Segmentation (BiSeNet / YOLO-seg) | FastSAM (obstacle proposal) | Must operate within edge inference budget; check Ultralytics licensing terms. |
| **Datasets** | RUGD (primary RGB), RELLIS-3D (secondary) | IDD, locally collected Indian campus data | US dataset domain gap addressed via local fine-tuning in Phase 6. |
| **Visualization** | RViz2 (competition default) | Foxglove Studio | Foxglove for high-polish live demonstration; RViz2 for zero-license dependency. |
| **ML Framework** | PyTorch | ONNX Runtime / TensorRT | Fast export to edge accelerators (Jetson Orin/Nano). |

---

## 5. Engineering Roadmap & Phased Execution

Detailed milestones are defined in `docs/research/ENGINEERING_ROADMAP.md`.

> **CRITICAL NON-NEGOTIABLE PRINCIPLE:**  
> **Build one thin vertical slice first — camera → basic perception → localization → planner → controller → robot moves — before deepening any single subsystem.**  
> The vertical slice established in Phase 1 must remain runnable end-to-end at the close of every subsequent phase.

- **Phase 0 — Ground Truth & Research (Current):** Reconcile PS text, baseline ADRs, lock repository structure and evaluation criteria.
- **Phase 1 — Minimal End-to-End Vertical Slice:** Simplest working pipeline in Gazebo: simulated UGV + heightmap + camera feed + wheel/IMU EKF + default Nav2 + simple obstacle A→B run.
- **Phase 2 — Perception Layer:** Replace stub with real terrain segmentation model (RUGD/RELLIS-3D pretrained).
- **Phase 3 — Localization / SLAM:** Benchmark visual SLAM (RTAB-Map vs VINS) against EKF baseline; record drift metrics (ATE/RPE).
- **Phase 4 — Planning Layer (Rank 2 Differentiation):** Integrate custom traversability-aware Nav2 costmap plugin (prefer safe terrain over risky terrain).
- **Phase 5 — Dynamic Obstacle Avoidance:** Moving obstacle injection into Gazebo; measure replanning latency and clearance.
- **Phase 6 — Optimization & Domain Adaptation (Rank 1 Differentiation):** Collect local Indian-terrain images, fine-tune segmentation model, measure accuracy delta (mIoU), optimize for edge FPS.
- **Phase 7 — Sim-to-Real Transfer (Contingent):** Deploy validated stack on physical UGV platform if hardware is available.
- **Phase 8 — Validation & Presentation:** Finalize metrics, record live visual demos with internal state overlays, build official 6-slide AICTE deck.

---

## 6. SIH Presentation & Winner Patterns

Synthesized from `docs/research/SIH_WINNER_PATTERN_ANALYSIS.md` and `docs/research/SIH_2026_PRESENTATION_ANALYSIS.md`:

### 6.1 Submission Constraints (Stage 1)
- Format: PDF only, created from the **official AICTE 6-slide PPT template**.
- Maximum slides: **Strictly 6 slides**.
- Team size: Exactly 6 students, same institution, minimum 1 female member.
- Deadline: **30 September 2026**.

### 6.2 Observed Winning Patterns (Patterns A–G)
1. **Problem-First Framing:** Quantify the operational pain point in GPS-denied defense/UGV navigation rather than reciting generic AI buzzwords.
2. **End-to-End Data Flow:** Display an intelligible visual pipeline (Input → Perception → Localization → Planning → Actuation).
3. **Technical Credibility:** Explicitly answer: Where does compute run? What is the latency? How is failure handled?
4. **Demonstrable Implementation:** A working Gazebo simulation with internal-state visualization (costmap heatmap, planned path) beats static UI mockups every time.
5. **Surviving Technical Scrutiny:** Prepare quantitative answers for lighting changes, visual tracking loss, and terrain hazards.
6. **Impact & Deployment:** Connect UGV capabilities to operational outcomes (perimeter security, human risk reduction, search-and-rescue efficiency).
7. **Differentiation:** Highlight **Rank 1** (closing the Indian terrain domain gap) and **Rank 2** (traversability-aware costmaps).

### 6.3 Core Rule
> **Build the system first. Prove the system second. Explain the system third. Polish the presentation last.**  
> *A beautiful presentation cannot rescue a broken system; a working system without quantitative metrics loses to evidence-backed competitors.*

---

## 7. Evaluation Model & Quantitative Metrics

Metrics must be measured, not claimed. Every phase must produce at least one metric logged in `/eval/`:

- **Perception:** mIoU (mean Intersection over Union), precision, recall, inference latency (ms), FPS on target compute.
- **Localization:** Absolute Trajectory Error (ATE RMSE), Relative Pose Error (RPE), tracking failure rate, recovery time.
- **Navigation:** Point-A-to-Point-B traversal success rate (%), collision count, path length vs optimal (m), navigation duration (s), minimum obstacle clearance (m).
- **System:** End-to-end perception-to-actuation latency, CPU/GPU utilization, memory footprint (MB).

---

## 8. Experiment Logging Policy

Every experiment conducted in simulation or on hardware must be logged in `/eval/` using this template:

```text
Experiment ID: EXP-YYYYMMDD-XX
Date: YYYY-MM-DD
Objective: [What specific question is being tested?]
Hypothesis: [What outcome is expected?]
Environment / World: [Gazebo world name, terrain type, lighting condition]
Model / Algorithm: [Specific model checkpoint or planner configuration]
Hardware / Compute: [CPU, GPU, RAM configuration]
Metrics:
  - Metric 1: Value
  - Metric 2: Value
Baseline Comparison: [Previous result vs new result]
Failure Cases: [Specific edge cases or tracking losses observed]
Interpretation: [Engineering takeaway]
Next Decision: [Next concrete code or config change]
```

---

## 9. Repository Layout

```text
/sih2026/
  ├── README.md                   # Project landing page & quickstart
  ├── AGENTS.md                   # This file (master operating context)
  ├── docs/
  │   ├── README.md               # Documentation hub
  │   ├── system_architecture.md  # End-to-end data flow, topic contracts & TF
  │   ├── phase1_vertical_slice.md # Phase 1 runnable simulation guide
  │   ├── hardware_and_environment.md # Hardware & compute specifications
  │   ├── troubleshooting_and_faq.md # WSL & Gazebo troubleshooting
  │   ├── decisions/              # Architectural Decision Records (ADR-0001-*.md)
  │   └── research/               # Research foundations & PS deconstruction
  │       ├── PS26126_DECONSTRUCTION.md
  │       ├── ENGINEERING_ROADMAP.md
  │       ├── TECHNOLOGY_COMPARISON.md
  │       ├── RESEARCH_GAPS.md
  │       ├── DATASETS.md
  │       ├── EXISTING_SOLUTIONS.md
  │       ├── SIH_WINNER_PATTERN_ANALYSIS.md
  │       ├── SIH_2026_PRESENTATION_ANALYSIS.md
  │       └── SOURCE_REGISTER.md
  ├── sim/                        # Gazebo worlds, URDF/SDF models, heightmaps
  ├── src/                        # ROS 2 packages (bringup, description, localization, nav2)
  ├── models/                     # Model checkpoints, export scripts, training configs
  ├── data/                       # Dataset scripts, taxonomy mappings, annotation manifests
  ├── eval/                       # Benchmark logs, trajectory evaluations, experiment records
  └── scripts/                    # Setup and execution shell scripts
```

---

## 10. AI-Agent Operating Rules

1. Read this file before modifying anything in the repository.
2. Inspect actual repository state before proposing or executing changes.
3. Never invent requirements or judging criteria. Use verified sources and labeled inferences.
4. Cite external claims and log sources in `docs/research/SOURCE_REGISTER.md`.
5. Major architectural choices must be documented in `/docs/decisions/` (`ADR-0001-*.md`).
6. Do not optimize for presentation visuals before the underlying technical subsystem is functional.
7. Do not use unearned superlatives ("real-time", "robust", "state-of-the-art") without citing a measured metric.
8. Interfaces between subsystems must remain explicit (documented ROS 2 topic names, message types, and TF frames).
9. Treat failures as engineering evidence; log failure cases in `/eval/`.
10. The Phase 1 vertical slice must remain runnable end-to-end at the conclusion of every phase.
