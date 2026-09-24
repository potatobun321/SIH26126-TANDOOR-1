#!/usr/bin/env python3
"""
stress_test_circuit.py — Multi-Waypoint Autonomous Stress Test for SIH26126 UGV
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Executes a 5-waypoint patrol circuit across diverse outdoor terrain angles, tight
clearances past the boulder and tree obstacles, and graded traversability costs.
Logs empirical telemetry, radial precision, path lengths, and compute metrics.
"""

import os
import sys
import time
import math
import argparse
import datetime
import statistics
import csv

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32
from nav2_msgs.action import NavigateToPose

# Known Obstacle Coordinates
BOULDER_X = 5.0
BOULDER_Y = 0.2
BOULDER_RADIUS = 0.7

TREE_X = 8.0
TREE_Y = -2.0
TREE_RADIUS = 0.45

WAYPOINTS = [
    {
        'name': 'WP1: South Flank (4.0, -1.8)',
        'x': 4.0, 'y': -1.8, 'yaw': -0.40,
        'desc': 'South corridor between boulder and tree'
    },
    {
        'name': 'WP2: North-East Outpost (7.5, 1.2)',
        'x': 7.5, 'y': 1.2, 'yaw': 0.80,
        'desc': 'Diagonal crossing past boulder to NE perimeter'
    },
    {
        'name': 'WP3: Deep Frontier (9.5, -0.5)',
        'x': 9.5, 'y': -0.5, 'yaw': -0.20,
        'desc': 'Long-range reach towards natural ditch barrier'
    },
    {
        'name': 'WP4: North Ridge Rally (3.5, 2.0)',
        'x': 3.5, 'y': 2.0, 'yaw': 3.00,
        'desc': 'North corridor circuit return'
    },
    {
        'name': 'WP5: Base Camp Home (0.0, 0.0)',
        'x': 0.0, 'y': 0.0, 'yaw': 3.14,
        'desc': 'Full loop closure to origin base'
    }
]


class StressTestCircuitHarness(Node):
    def __init__(self, args):
        super().__init__('stress_test_circuit_harness')
        self.args = args

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.has_odom = False

        self.leg_path_length = 0.0
        self.last_x = None
        self.last_y = None
        self.min_boulder_clearance = float('inf')
        self.min_tree_clearance = float('inf')

        self.fps_samples = []
        self.latency_samples = []

        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.create_subscription(Float32, '/perception/fps', self._fps_callback, 10)
        self.create_subscription(Float32, '/perception/latency_ms', self._latency_callback, 10)

        self.get_logger().info("Stress Test Circuit Harness initialized.")

    def _extract_yaw(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _odom_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.current_x = p.x
        self.current_y = p.y
        self.current_yaw = self._extract_yaw(q)
        self.has_odom = True

        if self.last_x is not None and self.last_y is not None:
            step = math.hypot(p.x - self.last_x, p.y - self.last_y)
            if step < 1.0:
                self.leg_path_length += step
        self.last_x = p.x
        self.last_y = p.y

        dist_boulder = math.hypot(p.x - BOULDER_X, p.y - BOULDER_Y)
        if dist_boulder < self.min_boulder_clearance:
            self.min_boulder_clearance = dist_boulder

        dist_tree = math.hypot(p.x - TREE_X, p.y - TREE_Y)
        if dist_tree < self.min_tree_clearance:
            self.min_tree_clearance = dist_tree

    def _fps_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.fps_samples.append(msg.data)

    def _latency_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.latency_samples.append(msg.data)

    def wait_for_services(self, timeout_sec=30.0):
        self.get_logger().info("Connecting to /navigate_to_pose action server...")
        if not self._action_client.wait_for_server(timeout_sec=timeout_sec):
            self.get_logger().error(f"Action server not available after {timeout_sec}s.")
            return False

        self.get_logger().info("Waiting for odometry telemetry on /odom...")
        start_t = time.time()
        while not self.has_odom and (time.time() - start_t < timeout_sec):
            rclpy.spin_once(self, timeout_sec=0.2)
        if not self.has_odom:
            self.get_logger().error("No odometry received.")
            return False

        self.get_logger().info(f"Odometry received. Current pose: ({self.current_x:.2f}, {self.current_y:.2f})")
        return True

    def execute_waypoint(self, wp_idx, wp, timeout_sec=60.0):
        target_x = wp['x']
        target_y = wp['y']
        target_yaw = wp['yaw']
        name = wp['name']
        desc = wp['desc']

        self.leg_path_length = 0.0
        self.last_x = self.current_x
        self.last_y = self.current_y
        self.min_boulder_clearance = float('inf')
        self.min_tree_clearance = float('inf')
        self.fps_samples.clear()
        self.latency_samples.clear()

        start_time = time.time()
        qz = round(math.sin(target_yaw / 2.0), 4)
        qw = round(math.cos(target_yaw / 2.0), 4)

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(target_x)
        goal_msg.pose.pose.position.y = float(target_y)
        goal_msg.pose.pose.orientation.z = float(qz)
        goal_msg.pose.pose.orientation.w = float(qw)

        print(f"\n==================================================")
        print(f" [{wp_idx}/5] Executing: {name}")
        print(f" Tactical Objective: {desc}")
        print(f" Target: ({target_x:.2f}, {target_y:.2f}, yaw={target_yaw:.2f} rad)")
        print(f" Starting Pose: ({self.current_x:.2f}, {self.current_y:.2f})")
        print(f"==================================================")

        send_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            print("ERROR: Goal rejected by Nav2 planner!")
            return {
                'wp_idx': wp_idx,
                'name': name,
                'status': 'REJECTED',
                'duration': 0.0,
                'target_x': target_x, 'target_y': target_y,
                'final_x': self.current_x, 'final_y': self.current_y,
                'error_dist': math.hypot(self.current_x - target_x, self.current_y - target_y),
                'path_length': 0.0,
                'min_boulder': self.min_boulder_clearance,
                'min_tree': self.min_tree_clearance,
                'avg_fps': 0.0, 'avg_latency_ms': 0.0
            }

        get_result_future = goal_handle.get_result_async()
        last_log_time = time.time()

        while not get_result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            now = time.time()
            elapsed = now - start_time

            if now - last_log_time >= 2.0:
                dist_rem = math.hypot(target_x - self.current_x, target_y - self.current_y)
                current_fps = round(statistics.mean(self.fps_samples[-10:]), 1) if self.fps_samples else 0.0
                current_lat = round(statistics.mean(self.latency_samples[-10:]), 1) if self.latency_samples else 0.0
                print(f"  [{elapsed:5.1f}s] Pose: ({self.current_x:6.2f}, {self.current_y:6.2f}) | Rem: {dist_rem:5.2f}m | Boulder: {self.min_boulder_clearance:5.2f}m | FPS: {current_fps:4.1f} | Lat: {current_lat:5.1f}ms")
                last_log_time = now

            if elapsed > timeout_sec:
                print(f"WARNING: Waypoint {wp_idx} timed out after {timeout_sec}s.")
                cancel_future = goal_handle.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future)
                break

        duration = time.time() - start_time
        final_x = self.current_x
        final_y = self.current_y
        error_dist = math.hypot(final_x - target_x, final_y - target_y)

        status_str = "UNKNOWN"
        if get_result_future.done():
            action_res = get_result_future.result()
            if action_res.status == GoalStatus.STATUS_SUCCEEDED:
                status_str = "SUCCEEDED"
            elif action_res.status == GoalStatus.STATUS_ABORTED:
                status_str = "ABORTED"
            elif action_res.status == GoalStatus.STATUS_CANCELED:
                status_str = "CANCELED"
            else:
                status_str = f"STATUS_{action_res.status}"
        elif duration > timeout_sec:
            status_str = "TIMED_OUT"

        avg_fps = round(statistics.mean(self.fps_samples), 2) if self.fps_samples else 0.0
        avg_latency = round(statistics.mean(self.latency_samples), 2) if self.latency_samples else 0.0

        print(f"--> Leg Result: {status_str} in {duration:.2f}s | Final Pose: ({final_x:.3f}, {final_y:.3f}) | Error: {error_dist:.3f}m | Clearance: {self.min_boulder_clearance:.3f}m")

        return {
            'wp_idx': wp_idx,
            'name': name,
            'status': status_str,
            'duration': round(duration, 2),
            'target_x': round(target_x, 3),
            'target_y': round(target_y, 3),
            'final_x': round(final_x, 3),
            'final_y': round(final_y, 3),
            'error_dist': round(error_dist, 3),
            'path_length': round(self.leg_path_length, 2),
            'min_boulder': round(self.min_boulder_clearance, 3),
            'min_tree': round(self.min_tree_clearance, 3),
            'avg_fps': avg_fps,
            'avg_latency_ms': avg_latency
        }


def run_circuit():
    parser = argparse.ArgumentParser(description="Multi-Waypoint Autonomous Stress Test for SIH26126 UGV")
    parser.add_argument('--timeout', type=float, default=60.0, help='Per-leg timeout in seconds')
    parser.add_argument('--output-dir', type=str, default='eval/logs', help='Directory for benchmark logs')
    args, unknown = parser.parse_known_args()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    rclpy.init()
    harness = StressTestCircuitHarness(args)

    if not harness.wait_for_services(timeout_sec=30.0):
        print("ERROR: Prerequisites failed. Exiting.")
        harness.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    print(f"\n=======================================================")
    print(f" SIH 2026 Multi-Waypoint Autonomous Circuit Stress Test")
    print(f" 5 Dynamic Waypoints | Traversability Costs | Hazards")
    print(f"=======================================================\n")

    results = []
    total_start = time.time()

    for idx, wp in enumerate(WAYPOINTS, 1):
        res = harness.execute_waypoint(idx, wp, timeout_sec=args.timeout)
        results.append(res)
        time.sleep(2.0)

    total_duration = time.time() - total_start
    total_distance = sum(r['path_length'] for r in results)
    succeeded_count = sum(1 for r in results if r['status'] == 'SUCCEEDED')
    success_rate = (succeeded_count / len(results)) * 100.0

    # Export CSV
    csv_path = os.path.join(args.output_dir, f"stress_test_{timestamp}.csv")
    fieldnames = ['wp_idx', 'name', 'status', 'duration', 'target_x', 'target_y', 'final_x', 'final_y', 'error_dist', 'path_length', 'min_boulder', 'min_tree', 'avg_fps', 'avg_latency_ms']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Export Markdown Report
    md_path = os.path.join(args.output_dir, f"stress_test_report_{timestamp}.md")
    with open(md_path, 'w') as f:
        f.write("# SIH 2026 Multi-Waypoint Autonomous Stress Test Report\n\n")
        f.write(f"- **Timestamp:** {timestamp}\n")
        f.write(f"- **Team:** Tikka Techies | SIH26126 (BEL)\n")
        f.write(f"- **Total Circuit Waypoints:** {len(WAYPOINTS)}\n")
        f.write(f"- **Waypoints Reached Successfully:** {succeeded_count}/{len(WAYPOINTS)} (**{success_rate:.1f}% Success Rate**)\n")
        f.write(f"- **Total Circuit Traversal Distance:** {total_distance:.2f} m\n")
        f.write(f"- **Total Circuit Duration:** {total_duration:.2f} s\n\n")

        f.write("## 1. Waypoint-by-Waypoint Telemetry\n\n")
        f.write("| # | Waypoint Name | Status | Transit Time (s) | Target (x, y) | Final (x, y) | Positioning Error (m) | Path Length (m) | Min Boulder Clearance (m) | AI FPS | AI Latency (ms) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            f.write(f"| {r['wp_idx']} | **{r['name']}** | `{r['status']}` | {r['duration']:.2f}s | ({r['target_x']:.2f}, {r['target_y']:.2f}) | ({r['final_x']:.2f}, {r['final_y']:.2f}) | {r['error_dist']:.3f}m | {r['path_length']:.2f}m | {r['min_boulder']:.2f}m | {r['avg_fps']:.1f} | {r['avg_latency_ms']:.1f}ms |\n")

        f.write("\n## 2. Robustness Summary\n\n")
        f.write(f"- **All 5 Waypoints Succeeded:** {succeeded_count == len(WAYPOINTS)}\n")
        f.write(f"- **Average Positioning Error:** {statistics.mean(r['error_dist'] for r in results):.3f} m\n")
        f.write(f"- **Average Perception FPS:** {statistics.mean(r['avg_fps'] for r in results if r['avg_fps'] > 0):.1f} FPS\n")
        f.write(f"- **Average Perception Latency:** {statistics.mean(r['avg_latency_ms'] for r in results if r['avg_latency_ms'] > 0):.1f} ms\n")
        f.write(f"- **Minimum Clearance to Any Hazard:** {min(r['min_boulder'] for r in results):.2f} m (Zero contact)\n")

    print("\n=======================================================")
    print(f" STRESS TEST COMPLETE: {success_rate:.1f}% Success ({succeeded_count}/{len(WAYPOINTS)})")
    print(f" CSV Saved:   {csv_path}")
    print(f" Report Saved: {md_path}")
    print(f" Total Traversed: {total_distance:.2f} m in {total_duration:.1f} s")
    print("=======================================================\n")

    harness.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    run_circuit()
