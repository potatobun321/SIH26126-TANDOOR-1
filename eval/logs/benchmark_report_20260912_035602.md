# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_035602
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 1 (2 total legs)
- **Navigation Success Rate:** **100.0%** (2/2)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 21.01 s | [21.01s - 21.01s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | 18.60 s | [18.60s - 18.60s] |
| **Navigation** | Total Round-Trip Time | 39.61 s | [39.61s - 39.61s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.34 m | [0.338m - 0.338m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | 0.34 m | [0.337m - 0.337m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 1.36 ± 0.14 (min: 1.26, max: 1.46) m | [1.264m - 1.457m] |
| **Perception** | Real-Time Segmentation FPS | 27.38 ± 0.92 (min: 26.73, max: 28.03) FPS | [26.7 - 28.0] |
| **Perception** | End-to-End Inference Latency | 17.91 ± 0.83 (min: 17.33, max: 18.50) ms | [17.3ms - 18.5ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 21.01 | (6.84, -0.30) | 0.338 | 7.30 | 1.46 | 28.0 | 18.5 |
| 1 | Return (B->A) | **SUCCEEDED** | 18.60 | (0.30, -0.15) | 0.337 | 7.49 | 1.26 | 26.7 | 17.3 |
