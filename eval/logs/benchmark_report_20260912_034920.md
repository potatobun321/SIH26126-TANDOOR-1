# SIH 2026 Autonomous Navigation Benchmark Report

- **Timestamp:** 20260912_034920
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Trials Completed:** 1 (2 total legs)
- **Navigation Success Rate:** **100.0%** (2/2)

## 1. Statistical Aggregates (Mean ± Std Dev)

| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |
|---|---|---|---|
| **Navigation** | Outbound Transit Time ($t_{out}$) | 17.85 s | [17.85s - 17.85s] |
| **Navigation** | Return Transit Time ($t_{ret}$) | 23.57 s | [23.57s - 23.57s] |
| **Navigation** | Total Round-Trip Time | 41.42 s | [41.42s - 41.42s] |
| **Precision** | Outbound Radial Error at B ($\Delta_B$) | 0.33 m | [0.331m - 0.331m] |
| **Precision** | Return Radial Error at Origin ($\Delta_A$) | 0.33 m | [0.332m - 0.332m] |
| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | 1.30 ± 0.24 (min: 1.13, max: 1.47) m | [1.131m - 1.470m] |
| **Perception** | Real-Time Segmentation FPS | 29.28 ± 0.42 (min: 28.98, max: 29.58) FPS | [29.0 - 29.6] |
| **Perception** | End-to-End Inference Latency | 9.46 ± 0.51 (min: 9.10, max: 9.82) ms | [9.1ms - 9.8ms] |

## 2. Granular Per-Run Telemetry

| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Outbound (A->B) | **SUCCEEDED** | 17.85 | (6.75, -0.22) | 0.331 | 7.77 | 1.47 | 29.0 | 9.8 |
| 1 | Return (B->A) | **SUCCEEDED** | 23.57 | (0.23, 0.24) | 0.332 | 8.69 | 1.13 | 29.6 | 9.1 |
