# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_031911
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 3 (6 total legs)
- **Navigation Success Rate:** **100.0%** (6/6)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 13.27 ± 0.42 (min: 12.80, max: 13.60) s | [12.80s - 13.60s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | 14.03 ± 0.40 (min: 13.80, max: 14.50) s | [13.80s - 14.50s] |
| **Navigation** | Total Round-Trip Time | 27.30 ± 0.10 (min: 27.21, max: 27.40) s | [27.21s - 27.40s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.33 ± 0.01 (min: 0.32, max: 0.34) m | [0.322m - 0.339m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | 0.33 ± 0.00 (min: 0.33, max: 0.34) m | [0.329m - 0.335m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 1.82 ± 0.02 (min: 1.80, max: 1.84) m | [1.796m - 1.844m] |
| **Perception** | Real-Time Segmentation FPS | 29.66 ± 0.08 (min: 29.56, max: 29.78) FPS | [29.6 - 29.8] |
| **Perception** | End-to-End Inference Latency | 9.20 ± 0.24 (min: 8.88, max: 9.53) ms | [8.9ms - 9.5ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 12.80 | (6.86, 0.29) | 0.327 | 8.78 | 1.84 | 29.6 | 9.4 |
| 1 | Return (B->A) | **SUCCEEDED** | 14.50 | (0.25, 0.22) | 0.332 | 8.71 | 1.84 | 29.8 | 8.9 |
| 2 | Outbound (A->B) | **SUCCEEDED** | 13.41 | (6.77, -0.23) | 0.322 | 8.31 | 1.80 | 29.6 | 9.5 |
| 2 | Return (B->A) | **SUCCEEDED** | 13.80 | (0.25, -0.21) | 0.329 | 8.19 | 1.82 | 29.7 | 9.2 |
| 3 | Outbound (A->B) | **SUCCEEDED** | 13.60 | (6.77, -0.25) | 0.339 | 8.09 | 1.81 | 29.6 | 9.0 |
| 3 | Return (B->A) | **SUCCEEDED** | 13.80 | (0.25, -0.22) | 0.335 | 8.10 | 1.82 | 29.6 | 9.2 |
