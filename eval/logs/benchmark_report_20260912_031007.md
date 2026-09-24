# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_031007
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 3 (6 total legs)
- **Navigation Success Rate:** **16.7%** (1/6)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 13.15 s | [13.15s - 13.15s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | N/A s | [0.00s - 0.00s] |
| **Navigation** | Total Round-Trip Time | N/A s | [0.00s - 0.00s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.33 m | [0.332m - 0.332m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | N/A m | [0.000m - 0.000m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 2.02 ± 0.06 (min: 1.92, max: 2.07) m | [1.921m - 2.069m] |
| **Perception** | Real-Time Segmentation FPS | 29.93 ± 1.18 (min: 29.31, max: 32.34) FPS | [29.3 - 32.3] |
| **Perception** | End-to-End Inference Latency | 9.97 ± 0.43 (min: 9.62, max: 10.72) ms | [9.6ms - 10.7ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 13.15 | (6.96, 0.33) | 0.332 | 8.87 | 1.92 | 29.3 | 10.7 |
| 1 | Return (B->A) | **TIMED_OUT** | 60.01 | (6.99, -0.37) | 7.001 | 5.14 | 1.96 | 29.4 | 9.7 |
| 2 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (7.00, -0.70) | 0.703 | 4.89 | 2.07 | 29.6 | 9.6 |
| 2 | Return (B->A) | **TIMED_OUT** | 60.01 | (6.99, -0.37) | 7.001 | 4.89 | 2.04 | 29.4 | 9.9 |
| 3 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (7.00, -0.70) | 0.702 | 4.89 | 2.07 | 29.6 | 9.7 |
| 3 | Return (B->A) | **TIMED_OUT** | 60.01 | (6.99, -0.37) | 7.000 | 4.89 | 2.04 | 32.3 | 10.2 |
