# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_025800
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 3 (6 total legs)
- **Navigation Success Rate:** **33.3%** (2/6)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 13.30 s | [13.30s - 13.30s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | 13.96 s | [13.96s - 13.96s] |
| **Navigation** | Total Round-Trip Time | N/A s | [0.00s - 0.00s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.32 m | [0.321m - 0.321m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | 1.53 m | [1.527m - 1.527m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 2.38 ± 1.08 (min: 1.36, max: 3.74) m | [1.357m - 3.739m] |
| **Perception** | Real-Time Segmentation FPS | 29.99 ± 0.38 (min: 29.62, max: 30.68) FPS | [29.6 - 30.7] |
| **Perception** | End-to-End Inference Latency | 8.57 ± 0.32 (min: 8.21, max: 9.06) ms | [8.2ms - 9.1ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 13.30 | (6.69, 0.10) | 0.321 | 8.58 | 1.36 | 29.7 | 9.1 |
| 1 | Return (B->A) | **TIMED_OUT** | 60.01 | (6.70, -3.20) | 7.429 | 4.72 | 1.70 | 29.9 | 8.4 |
| 2 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (5.53, -1.76) | 2.293 | 3.84 | 2.03 | 29.9 | 8.2 |
| 2 | Return (B->A) | **SUCCEEDED** | 13.96 | (1.26, -0.86) | 1.527 | 5.10 | 1.69 | 29.6 | 8.3 |
| 3 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (1.26, 0.70) | 5.781 | 2.93 | 3.74 | 30.1 | 8.6 |
| 3 | Return (B->A) | **TIMED_OUT** | 60.01 | (1.26, 0.38) | 1.317 | 1.64 | 3.74 | 30.7 | 8.8 |
