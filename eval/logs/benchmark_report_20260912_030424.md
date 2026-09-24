# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_030424
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 3 (6 total legs)
- **Navigation Success Rate:** **33.3%** (2/6)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 15.46 s | [15.46s - 15.46s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | 13.50 s | [13.50s - 13.50s] |
| **Navigation** | Total Round-Trip Time | N/A s | [0.00s - 0.00s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.16 m | [0.160m - 0.160m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | 0.29 m | [0.294m - 0.294m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 3.26 ± 1.39 (min: 1.91, max: 4.76) m | [1.911m - 4.763m] |
| **Perception** | Real-Time Segmentation FPS | 29.86 ± 0.36 (min: 29.43, max: 30.50) FPS | [29.4 - 30.5] |
| **Perception** | End-to-End Inference Latency | 9.24 ± 0.29 (min: 8.87, max: 9.47) ms | [8.9ms - 9.5ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 15.46 | (6.97, 0.16) | 0.160 | 8.91 | 1.91 | 29.4 | 9.5 |
| 1 | Return (B->A) | **TIMED_OUT** | 60.01 | (7.02, 4.71) | 8.451 | 4.93 | 1.95 | 29.8 | 8.9 |
| 2 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (6.74, 3.76) | 3.770 | 1.26 | 3.96 | 30.0 | 8.9 |
| 2 | Return (B->A) | **SUCCEEDED** | 13.50 | (0.23, 0.18) | 0.294 | 7.67 | 2.22 | 29.8 | 9.5 |
| 3 | Outbound (A->B) | **TIMED_OUT** | 60.01 | (0.24, 1.68) | 6.968 | 2.62 | 4.76 | 29.6 | 9.3 |
| 3 | Return (B->A) | **TIMED_OUT** | 60.01 | (0.24, -0.14) | 0.274 | 6.14 | 4.76 | 30.5 | 9.5 |
