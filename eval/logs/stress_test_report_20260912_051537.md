# SIH 2026 Multi-Waypoint Autonomous Stress Test Report

- **Timestamp:** 20260912_051537
- **Team:** Tikka Techies | SIH26126 (BEL)
- **Total Circuit Waypoints:** 5
- **Waypoints Reached Successfully:** 5/5 (**100.0% Success Rate**)
- **Total Circuit Traversal Distance:** 22.50 m
- **Total Circuit Duration:** 95.43 s

## 1. Waypoint-by-Waypoint Telemetry

| # | Waypoint Name | Status | Transit Time (s) | Target (x, y) | Final (x, y) | Positioning Error (m) | Path Length (m) | Min Boulder Clearance (m) | AI FPS | AI Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **WP1: South Flank (4.0, -1.8)** | `SUCCEEDED` | 10.82s | (4.00, -1.80) | (3.97, -1.46) | 0.342m | 4.04m | 1.84m | 16.9 | 30.7ms |
| 2 | **WP2: North-East Outpost (7.5, 1.2)** | `SUCCEEDED` | 31.20s | (7.50, 1.20) | (7.14, 0.61) | 0.690m | 5.25m | 1.77m | 17.6 | 32.7ms |
| 3 | **WP3: Deep Frontier (9.5, -0.5)** | `SUCCEEDED` | 9.94s | (9.50, -0.50) | (9.17, -0.57) | 0.337m | 2.56m | 2.17m | 18.6 | 31.9ms |
| 4 | **WP4: North Ridge Rally (3.5, 2.0)** | `SUCCEEDED` | 22.20s | (3.50, 2.00) | (3.84, 1.97) | 0.338m | 6.64m | 1.73m | 19.0 | 32.7ms |
| 5 | **WP5: Base Camp Home (0.0, 0.0)** | `SUCCEEDED` | 11.25s | (0.00, 0.00) | (0.27, 0.21) | 0.342m | 4.01m | 2.12m | 19.9 | 34.0ms |

## 2. Robustness Summary

- **All 5 Waypoints Succeeded:** True
- **Average Positioning Error:** 0.410 m
- **Average Perception FPS:** 18.4 FPS
- **Average Perception Latency:** 32.4 ms
- **Minimum Clearance to Any Hazard:** 1.73 m (Zero contact)
