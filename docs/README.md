# Tikka Techies Documentation — SIH26126

Welcome to the engineering and technical documentation for **Tikka Techies'** submission for **Smart India Hackathon 2026** (Problem Statement ID: **SIH26126** — *Bharat Electronics Limited*).

> **Problem Title:** Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor environment  
> **Mission:** Build a verified, evidence-backed, vision-centric autonomous navigation software stack for outdoor UGVs operating in GPS-denied environments.

---

## 1. Technical Documentation

| Document | Description |
|---|---|
| [System Architecture](file:///c:/Users/GIGA/Desktop/sih2026/docs/system_architecture.md) | Complete end-to-end software pipeline, data contracts, topic specifications, and TF transform tree. |
| [Phase 1 Vertical Slice Guide](file:///c:/Users/GIGA/Desktop/sih2026/docs/phase1_vertical_slice.md) | Step-by-step walkthrough of the minimal runnable prototype in Gazebo Harmonic, bridge, EKF, and Nav2. |
| [Phase 1 Engineering Report & Pitch Guide](file:///c:/Users/GIGA/Desktop/sih2026/docs/PHASE1_ENGINEERING_REPORT.md) | Comprehensive engineering master guide: Problem context, full toolchain, all 9 problems diagnosed and solved, benchmark data, and pitch script. |
| [Hardware & Environment Specifications](file:///c:/Users/GIGA/Desktop/sih2026/docs/hardware_and_environment.md) | Host development environment (RTX 5060 Ti, WSL2, Ubuntu 24.04), edge hardware target (Jetson), and sensor payload specs. |
| [Troubleshooting & FAQ](file:///c:/Users/GIGA/Desktop/sih2026/docs/troubleshooting_and_faq.md) | Practical fixes for WSL permissions, WSLg display, Gazebo spawning, TF delays, and ros_gz_bridge issues. |
| [ADR-0001: Baseline Architecture](file:///c:/Users/GIGA/Desktop/sih2026/docs/decisions/ADR-0001-baseline-architecture-candidates.md) | Architectural Decision Record baselining ROS 2, Gazebo Harmonic, EKF, and Nav2. |

---

## 2. Research & Foundation Archive (`docs/research/`)

| Document | Key Content |
|---|---|
| [PS26126 Deconstruction](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/PS26126_DECONSTRUCTION.md) | Verified BEL problem statement requirements (R1–R9) and technical subproblems. |
| [Engineering Roadmap](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/ENGINEERING_ROADMAP.md) | Detailed 9-phase execution roadmap and vertical-slice exit criteria. |
| [Technology Comparison](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/TECHNOLOGY_COMPARISON.md) | Trade-offs across ROS 2 distros, simulators, visual SLAM methods, and segmentation models. |
| [Research Gaps & Differentiation](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/RESEARCH_GAPS.md) | Ranked differentiators (Rank 1: Indian-terrain domain closure, Rank 2: Traversability costmap). |
| [Datasets Analysis](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/DATASETS.md) | RUGD and RELLIS-3D off-road dataset taxonomies and mapping. |
| [Existing Solutions](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/EXISTING_SOLUTIONS.md) | Literature review and commercial/academic baseline analysis. |
| [SIH Winner Patterns](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/SIH_WINNER_PATTERN_ANALYSIS.md) | Patterns A–G observed across successful SIH submissions (2020–2025). |
| [Presentation Analysis](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/SIH_2026_PRESENTATION_ANALYSIS.md) | Mandatory 6-slide AICTE PPT guidelines and content mapping. |
| [Source Register](file:///c:/Users/GIGA/Desktop/sih2026/docs/research/SOURCE_REGISTER.md) | Traceable registry of all government, academic, and technical sources. |

---

## Core Engineering Rules

1. **Vertical Slice First:** Every phase must keep the full end-to-end pipeline runnable (Camera → Perception → Localization → Planner → Controller → Robot moves).
2. **Quantitative Validation:** No claims of "real-time" or "robust" without an experiment log in `/eval/`.
3. **Core Rule:** *Build the system first. Prove the system second. Explain the system third. Polish the presentation last.*
