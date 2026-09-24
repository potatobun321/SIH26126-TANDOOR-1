# SIH 2026 Multi-Waypoint Autonomous Stress Test Report

- **Timestamp:** 20260912_035957
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Total Circuit Waypoints:** 5
- **Waypoints Reached Successfully:** 5/5 (**100.0% Success Rate**)
- **Total Circuit Traversal Distance:** 21.59 m
- **Total Circuit Duration:** 59.82 s

## 1. Waypoint-by-Waypoint Telemetry

| # | Waypoint Name | Status | Transit Time (s) | Target (x, y) | Final (x, y) | Positioning Error (m) | Path Length (m) | Min Boulder Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **WP1: South Flank (4.0, -1.8)** | `SUCCEEDED` | 10.85s | (4.00, -1.80) | (3.74, -1.59) | 0.334m | 3.95m | 2.19m | 23.3 | 16.5ms |
| 2 | **WP2: North-East Outpost (7.5, 1.2)** | `SUCCEEDED` | 9.35s | (7.50, 1.20) | (7.28, 0.95) | 0.330m | 4.95m | 1.56m | 24.1 | 16.3ms |
| 3 | **WP3: Deep Frontier (9.5, -0.5)** | `SUCCEEDED` | 6.50s | (9.50, -0.50) | (9.17, -0.43) | 0.336m | 2.44m | 2.37m | 24.0 | 15.4ms |
| 4 | **WP4: North Ridge Rally (3.5, 2.0)** | `SUCCEEDED` | 15.00s | (3.50, 2.00) | (3.81, 1.86) | 0.343m | 6.27m | 1.42m | 23.3 | 16.0ms |
| 5 | **WP5: Base Camp Home (0.0, 0.0)** | `SUCCEEDED` | 8.11s | (0.00, 0.00) | (0.27, 0.20) | 0.339m | 3.98m | 2.05m | 24.0 | 15.2ms |

## 2. Robustness Summary

- **All 5 Waypoints Succeeded:** True
- **Average Positioning Error:** 0.336 m
- **Average Perception FPS:** 23.7 FPS
- **Average Perception Latency:** 15.9 ms
- **Minimum Clearance to Any Hazard:** 1.42 m (Zero contact)
