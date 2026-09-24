---
name: eval-benchmarker
description: Helper skill to structure and log quantitative robotics experiments (mIoU, latency, ATE drift, A->B navigation success) into the eval directory per SIH26126 protocols.
---

# Eval Benchmarker Skill

Use this skill when recording evaluation results, comparing baseline performance across development phases, or formatting quantitative evidence for the SIH presentation deck.

## 1. Metric Families
Always log against one of the four established metric families:
- **Perception:** mIoU (mean Intersection over Union), FPS, inference latency (ms), precision/recall.
- **Localization:** Absolute Trajectory Error (ATE RMSE in meters), Relative Pose Error (RPE), drift per 100m, tracking failure count.
- **Navigation:** A→B traversal success rate (%), mean traversal time (s), collision rate, minimum obstacle clearance (m).
- **System:** Latency end-to-end (sensor to motor), CPU utilization (%), GPU VRAM footprint (MB).

## 2. Benchmark Logging Workflow
1. When an experiment finishes, create or append an entry in `eval/experiments.md` using the exact format in `AGENTS.md` Section 8:
   ```markdown
   ### EXP-YYYYMMDD-XX: [Brief Title]
   - **Date:** YYYY-MM-DD
   - **Phase:** Phase [1-8]
   - **Objective:** [Goal]
   - **Environment:** [Gazebo world / Heightmap / Lighting]
   - **Configuration:** [Model / Algorithm]
   - **Hardware:** [Host CPU / GPU]
   - **Metrics:**
     | Metric | Measured Value | Baseline | Delta |
     |---|---|---|---|
     | Traversal Success | 95% | 80% | +15% |
     | ATE RMSE | 0.18m | 0.42m | -0.24m |
   - **Failure Cases:** [Notes on edge cases]
   - **Takeaway:** [Next engineering decision]
   ```
2. When preparing for presentation slides, synthesize these tables into high-density metric summary callouts.
