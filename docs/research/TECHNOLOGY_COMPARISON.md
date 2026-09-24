# Technology Comparison

All entries are CANDIDATES unless marked CONFIRMED CHOICE (none are confirmed yet — that decision comes after Phase 0/1 experiments per `ENGINEERING_ROADMAP.md`). Version/status claims reflect information gathered up to this research session (Sept 2026) and should be re-checked periodically — software moves fast.

## Middleware

### ROS 2
- **Purpose:** robotics middleware — pub/sub messaging, TF, lifecycle management, tooling.
- **Current distro landscape (verified against docs.ros.org, Sept 2026):** **Jazzy Jalisco** is the current LTS (supported to ~2029, targets Ubuntu 24.04). **Humble Hawksbill** is an older LTS (supported to ~2027, targets Ubuntu 22.04) with the widest third-party package availability historically (many SLAM/perception wrappers were built/tested on Humble first). **Kilted Kaiju** (May 2025) and the newer **Lyrical Luth** are non-LTS, shorter-support releases with the newest features.
- **Recommendation logic (CANDIDATE, not decided):** Humble has the most mature third-party ecosystem for the specific packages this project needs (ORB-SLAM3 ROS2 wrappers, RTAB-Map, Nav2 plugins) at time of writing, but is aging out of support. Jazzy is the safer long-term choice but requires verifying each candidate package's Jazzy support before committing — **this verification is a required Phase 0 task, not an assumption.**
- License: Apache 2.0. Actively maintained by Open Robotics / Open Source Robotics Foundation.
- Alternatives: ROS 1 (end-of-life, do not use for a new 2026 project), proprietary robot SDKs (not appropriate for an open, auditable SIH submission).

### Nav2
- **Purpose:** path planning (global + local), costmaps, recovery behaviors, controller servers for ROS 2 robots.
- **Maturity:** high — default navigation stack for ROS 2, large user base, active development.
- **Strengths:** pluggable planners/controllers, well-documented, integrates with standard costmap layers (static, obstacle, inflation), simulation-tested.
- **Weaknesses:** costmap-based planning is fundamentally 2D/2.5D — traversability nuance (soft mud vs. hard dirt, both "clear" in a binary costmap) requires a custom costmap layer or plugin, which the team would need to build (this is a real engineering task, not a checkbox).
- **Integration difficulty:** low-to-moderate for standard use; moderate-to-high if building a custom traversability-aware costmap layer.
- **Relevance to PS26126:** high — almost certainly the planning/control backbone regardless of other choices.
- **Alternatives:** custom planner (not recommended — reinventing a solved problem), MoveIt2 (wrong tool — that's for manipulators, not mobile base navigation).

## Simulation

### Gazebo (Harmonic / newer "Ionic" per Kilted Kaiju docs)
- **Purpose:** physics simulation of robot + sensors + environment.
- **Maturity:** high; the new Gazebo (formerly "Ignition," now unified under the "Gazebo" name — Fortress/Harmonic/Ionic release line) is the modern, maintained successor to "Gazebo Classic," which is deprecated.
- **Strengths:** tight ROS 2 integration (`ros_gz` bridge), good sensor plugin ecosystem (cameras, depth, IMU, LiDAR), outdoor terrain support via heightmaps.
- **Weaknesses:** photorealism and vegetation/terrain material fidelity are limited compared to game engines — sim-to-real gap for vision-based perception is a known, non-trivial risk (see `RESEARCH_GAPS.md`).
- **Relevance:** high — needed for Phase 0/1 rapid iteration without hardware risk.
- **Alternatives:** Webots (simpler, good docs, weaker ROS2/Nav2 ecosystem integration than Gazebo currently), Unity/Unreal + ROS-TCP bridge (much better visual fidelity for vision-model testing, but far higher setup cost and weaker native Nav2 integration) — **CANDIDATE for perception-specific sim-to-real experiments, not primary sim**, NVIDIA Isaac Sim (best-in-class sensor realism and increasingly ROS 2-integrated, but heavier hardware/GPU requirement — evaluate against team's available compute before committing).

## Visual SLAM / Odometry

### ORB-SLAM3
- **Purpose:** feature-based visual/visual-inertial SLAM (monocular, stereo, RGB-D).
- **Maturity:** widely cited academic reference implementation; GPLv3 licensed (a **real constraint** — check compatibility with your project's intended license before depending on it for anything beyond research/demo use).
- **Strengths:** strong loop closure, multi-map capability, well-documented in literature.
- **Weaknesses:** feature-based methods struggle in low-texture, repetitive outdoor scenes (grass, dirt, sky) — exactly the terrain this PS targets. Not natively a ROS 2 package; requires a community wrapper, which varies in maintenance quality — **verify current wrapper status before committing.**
- **Relevance:** high as a baseline/benchmark; uncertain as the production choice given the texture problem above.

### RTAB-Map
- **Purpose:** RGB-D/stereo graph-based SLAM with a first-class, actively maintained **ROS 2 package**.
- **Strengths:** native ROS 2 support (a real integration advantage over ORB-SLAM3), appearance-based loop closure, works with RGB-D or stereo, has direct Nav2 compatibility patterns documented by its maintainer.
- **Weaknesses:** still feature/appearance based — same fundamental low-texture-outdoor-terrain risk as ORB-SLAM3, though RTAB-Map's loop closure approach differs.
- **License:** BSD — more permissive than ORB-SLAM3's GPLv3, a real practical advantage.
- **Relevance:** currently the stronger CANDIDATE of the two purely on integration-risk and licensing grounds — **to be validated experimentally in Phase 3, not assumed.**

### Other candidates worth Phase 0 evaluation (not in the original list — added per "don't assume the listed tools are still best")
- **VINS-Fusion / OpenVINS** — visual-inertial odometry, often more robust to texture-poor scenes than pure visual SLAM when IMU is fused; worth a bake-off.
- **Direct/semi-direct methods (e.g., DSO-family)** — can be more robust to low texture than feature-based methods, at the cost of maturity/ROS2 tooling.
- Wheel odometry + IMU fusion (`robot_localization` package) as a **baseline/fallback**, not a novelty claim — cheap, robust, should be running from Phase 1 regardless of which visual SLAM is chosen, as a sanity-check and fallback signal.

## Terrain / Obstacle Perception

### YOLO segmentation variants (e.g., YOLOv8/v11-seg family)
- **Purpose:** fast instance/semantic segmentation, real-time capable on embedded GPUs.
- **Strengths:** strong real-time performance, large community, easy to fine-tune on custom/off-road datasets (RELLIS-3D, RUGD annotations are convertible).
- **Weaknesses:** license terms for the Ultralytics YOLO family have shifted over versions (AGPL-3.0 for some releases, commercial licensing for others) — **verify the exact license of whichever version/repo you use before committing**, this is a real, checkable constraint, not a formality.
- **Relevance:** high — realistic default for obstacle + coarse terrain-class detection given real-time constraints.

### FastSAM
- **Purpose:** near-real-time class-agnostic segmentation (a fast approximation of Segment Anything).
- **Strengths:** speed, no need for exhaustive class-labeled training data for generic "what is an object" segmentation.
- **Weaknesses:** class-agnostic — doesn't itself tell you "this is traversable grass vs. an obstacle" without a downstream classification step; less suited than YOLO-seg to the specific "terrain-class" need here.
- **Relevance:** medium — more useful as a generic obstacle-proposal generator than as the terrain-traversability solution.

### Other candidates worth evaluating
- **Lightweight semantic segmentation nets (e.g., BiSeNet, PIDNet, or a MobileNet/EfficientNet-backboned FCN)** trained directly on RELLIS-3D/RUGD classes — may outperform a repurposed detector for the specific traversability-mapping task, at lower latency.
- **Depth estimation (stereo depth, or monocular depth nets e.g. MiDaS-family)** as a complement to segmentation for obstacle *distance*, not just class — segmentation alone doesn't give range.

## Visualization

### Foxglove Studio
- **Purpose:** ROS 2-compatible visualization/debugging (topics, images, 3D scenes, plots) — works locally and (with the paid platform) in the cloud; the desktop app itself has historically had a free tier.
- **Strengths:** modern UI, good for demo recordings and judge-facing visualization (directly supports the "convincing demonstration" pattern noted in `SIH_WINNER_PATTERN_ANALYSIS.md`), works over a network link so a laptop can visualize what an embedded robot is doing.
- **Weaknesses:** license/pricing model has shifted over time for advanced features — verify current terms before depending on anything beyond the free desktop viewer for your submission.
- **Alternative:** RViz2 (free, ROS-native, less polished but zero licensing ambiguity) — **safer default for a competition deliverable**, with Foxglove as a nice-to-have for demo recording.

## ML framework

### PyTorch
- **Purpose:** training/inference framework for the perception models above.
- **Status:** industry-standard, actively maintained, BSD-licensed, first-class support from most segmentation/detection model repos including the YOLO family and typical off-road-segmentation baselines.
- **Relevance:** high, low-risk choice. No real alternative recommendation needed here — this is one of the few "candidate" list items with a genuinely low decision-risk.

## Cross-cutting decision principle
Every "final" technology choice in this table must pass through the **Phase 0/1 experiments in `ENGINEERING_ROADMAP.md`** before being written into `AGENTS.md` as a CONFIRMED CHOICE. Until then, all entries above remain CANDIDATE.
