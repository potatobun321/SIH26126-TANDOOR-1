# Engineering Roadmap: Research → Implementation

## Critical principle (non-negotiable, write into AGENTS.md verbatim)
**Build one thin vertical slice first — camera → basic perception → localization → planner → controller → robot moves — before deepening any single subsystem.** Do not build six independent subsystems and attempt integration at the end. Every phase after Phase 1 deepens an already-integrated, already-running system; it never bolts together previously-isolated pieces for the first time.

## Evaluation of the originally proposed phase sequence
The originally proposed 9-phase sequence (Research → Baseline → Perception → SLAM → Planning → Dynamic Obstacles → Optimization → Sim-to-Real → Validation+Presentation) is **fundamentally sound** and already follows the "early vertical slice" principle correctly by putting a "Minimal End-to-End Baseline" at Phase 1. The main risk is not the phase *order* but a common failure mode inside each phase: teams silently let a phase balloon into "perfect the subsystem" instead of "reach the next integration checkpoint." Adjustments recommended below are refinements, not a re-ordering.

## Recommended phases

### Phase 0 — Research / Ground Truth (this document set)
Deliverables: this file set + the confirmed real PS26126 text + Phase 0 technology bake-off decisions (ROS 2 distro, sim engine, SLAM candidate shortlist). **Exit criterion:** the team can state, in one sentence each, what "done" looks like for Phases 1–8, and has picked a specific simulated environment/course to build against.

### Phase 1 — Minimal End-to-End Baseline (the vertical slice)
Simplest possible version of every layer, wired together, in simulation:
- Camera feed → trivial perception (even a hardcoded "everything is drivable" stub is acceptable here) → wheel-odometry-based localization (not visual SLAM yet) → Nav2 default planner → default controller → robot completes a short A→B run around a **simple** obstacle in a **simple** Gazebo world.
**Exit criterion:** the robot moves from A to B autonomously in sim, end-to-end, badly if necessary, but with every layer present and wired. This is the single most important milestone in the whole project — do not skip or shortcut it to "save time for perception," since it is what de-risks integration for every later phase.

### Phase 2 — Perception
Replace the perception stub with a real terrain-segmentation/obstacle-detection model (per `TECHNOLOGY_COMPARISON.md` candidates), initially pretrained on RUGD/RELLIS-3D. Feed its output into a simple traversability signal (even a basic drivable/non-drivable mask is fine at first). **Exit criterion:** the vertical slice from Phase 1 now avoids a previously-untested obstacle because perception told it to, not because it was hardcoded.

### Phase 3 — Localization / SLAM
Swap wheel-odometry-only localization for the chosen visual SLAM/odometry approach (per the Rank 3 benchmarking plan in `RESEARCH_GAPS.md`), keeping wheel+IMU fusion running in parallel as a fallback/sanity signal. **Exit criterion:** the vehicle completes the same A→B run relying on visual localization, with drift measured and logged.

### Phase 4 — Planning
Deepen planning: introduce the traversability-aware costmap layer (Rank 2 differentiation), tune global/local planner parameters for outdoor terrain, test on a harder simulated course. **Exit criterion:** vehicle demonstrably prefers lower-cost terrain over geometrically-shorter-but-higher-cost terrain.

### Phase 5 — Dynamic Obstacle Avoidance
Introduce moving obstacles into the simulated world; validate avoidance under both nominal and degraded-localization conditions. **Exit criterion:** measured avoidance success rate against a defined obstacle-injection test set.

### Phase 6 — Optimization (moved up in emphasis, not sequence, from the original list)
This phase should explicitly include the **Indian-terrain fine-tuning work (Rank 1 differentiation)** — collecting and using a small locally-captured dataset — alongside performance optimization (latency, FPS, resource usage on target hardware). Treat "optimization" as covering both compute efficiency and domain-accuracy improvement, since both are needed before claiming the system works on real Indian outdoor terrain.

### Phase 7 — Simulation-to-Real
Only attempted if physical hardware is available and Phases 1–6 are solid in simulation. **Exit criterion:** the same vertical-slice behavior demonstrated on physical hardware, even in a reduced/simplified test course, with an honest account of what degraded versus simulation.

### Phase 8 — Validation + Presentation
Consolidate metrics from every phase (see `AGENTS.md`'s evaluation principles), build the demonstration recording/live-run plan, and compress the research narrative into the 6-slide format per `SIH_2026_PRESENTATION_ANALYSIS.md`.

## Cross-phase rules
1. **Every phase must end with the vertical slice still running end-to-end.** A phase that "improves" one subsystem but breaks the integrated pipeline is not complete.
2. **Every phase produces at least one number**, not just a demo video — this directly targets the validation gap identified in `SIH_WINNER_PATTERN_ANALYSIS.md`.
3. If a phase is running long, the fallback is to **freeze that subsystem at its current (possibly weak) state and move on**, keeping the end-to-end slice intact, rather than blocking the whole project on perfecting one layer.
4. Architectural decisions made in a phase are recorded (per `AGENTS.md` rule 12), including decisions to *not* pursue a candidate technology, with the reason.
