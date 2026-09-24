#!/usr/bin/env python3
"""
run_automated_eval.py — Headless Automated Evaluation & Benchmark Harness
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Automates repeated autonomous navigation trials (A -> B -> A), logs empirical metrics
(transit time, arrival error, path length, obstacle clearance, perception FPS/latency)
to CSV and Markdown, and computes statistical distributions (mean, std dev) for the
SIH presentation deck.
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

BOULDER_X = 5.0
BOULDER_Y = 0.2

class AutomatedEvalHarness(Node):
    def __init__(self, args):
        super().__init__('automated_eval_harness')
        self.args = args

        # Nav2 NavigateToPose Action Client
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Telemetry state
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.odom_received = False

        # Leg-specific tracking
        self.leg_trajectory = []
        self.leg_path_length = 0.0
        self.last_odom_x = None
        self.last_odom_y = None
        self.min_clearance = float('inf')

        # Perception telemetry sampling
        self.fps_samples = []
        self.latency_samples = []

        # ROS 2 Subscribers
        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.create_subscription(Float32, '/perception/fps', self._fps_callback, 10)
        self.create_subscription(Float32, '/perception/latency_ms', self._latency_callback, 10)

        self.get_logger().info("Automated Evaluation Harness initialized.")

    def _odom_callback(self, msg: Odometry):
        pos = msg.pose.pose.position
        self.current_x = pos.x
        self.current_y = pos.y
        self.odom_received = True

        # Calculate incremental path distance
        if self.last_odom_x is not None and self.last_odom_y is not None:
            dx = pos.x - self.last_odom_x
            dy = pos.y - self.last_odom_y
            dist = math.hypot(dx, dy)
            if dist < 1.0: # filter teleport jumps
                self.leg_path_length += dist

        self.last_odom_x = pos.x
        self.last_odom_y = pos.y

        # Track minimum clearance to boulder at (5.0, 0.2)
        dist_boulder = math.hypot(pos.x - BOULDER_X, pos.y - BOULDER_Y)
        if dist_boulder < self.min_clearance:
            self.min_clearance = dist_boulder

        self.leg_trajectory.append((pos.x, pos.y))

    def _fps_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.fps_samples.append(msg.data)

    def _latency_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.latency_samples.append(msg.data)

    def reset_leg_tracking(self):
        self.leg_trajectory = []
        self.leg_path_length = 0.0
        self.last_odom_x = self.current_x if self.odom_received else None
        self.last_odom_y = self.current_y if self.odom_received else None
        self.min_clearance = float('inf')
        self.fps_samples = []
        self.latency_samples = []

    def wait_for_services(self, timeout_sec=30.0):
        self.get_logger().info("Waiting for /navigate_to_pose action server...")
        start_wait = time.time()
        while not self._action_client.wait_for_server(timeout_sec=2.0):
            if time.time() - start_wait > timeout_sec:
                self.get_logger().error(f"Action server /navigate_to_pose not available after {timeout_sec}s.")
                return False
            self.get_logger().info("Still waiting for /navigate_to_pose...")
        self.get_logger().info("Connected to /navigate_to_pose action server.")

        self.get_logger().info("Waiting for odometry telemetry on /odom...")
        start_wait = time.time()
        while not self.odom_received:
            rclpy.spin_once(self, timeout_sec=0.2)
            if time.time() - start_wait > timeout_sec:
                self.get_logger().error(f"No /odom messages received after {timeout_sec}s.")
                return False
        self.get_logger().info(f"Odometry received. Current pose: ({self.current_x:.2f}, {self.current_y:.2f})")
        return True

    def execute_nav_leg(self, trial_id, leg_name, target_x, target_y, target_yaw, timeout_sec=120.0):
        self.reset_leg_tracking()
        start_time = time.time()

        qz = round(math.sin(target_yaw / 2.0), 4)
        qw = round(math.cos(target_yaw / 2.0), 4)

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(target_x)
        goal_msg.pose.pose.position.y = float(target_y)
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.z = float(qz)
        goal_msg.pose.pose.orientation.w = float(qw)

        print(f"\n==================================================")
        print(f" Trial {trial_id} | Leg: {leg_name}")
        print(f" Starting Pose: ({self.current_x:.3f}, {self.current_y:.3f})")
        print(f" Target Goal:   ({target_x:.3f}, {target_y:.3f}, yaw={target_yaw:.2f} rad)")
        print(f"==================================================")

        send_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error(f"Goal was rejected by Nav2!")
            return {
                'trial_id': trial_id,
                'leg': leg_name,
                'status': 'REJECTED',
                'duration': round(time.time() - start_time, 2),
                'target_x': target_x,
                'target_y': target_y,
                'final_x': self.current_x,
                'final_y': self.current_y,
                'error_dist': round(math.hypot(self.current_x - target_x, self.current_y - target_y), 3),
                'path_length': round(self.leg_path_length, 2),
                'min_clearance': round(self.min_clearance, 3),
                'avg_fps': 0.0,
                'avg_latency_ms': 0.0
            }

        get_result_future = goal_handle.get_result_async()
        last_log_time = time.time()

        while not get_result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            now = time.time()
            elapsed = now - start_time

            if now - last_log_time > 2.0:
                dist_rem = math.hypot(target_x - self.current_x, target_y - self.current_y)
                current_fps = round(statistics.mean(self.fps_samples[-10:]), 1) if self.fps_samples else 0.0
                current_lat = round(statistics.mean(self.latency_samples[-10:]), 1) if self.latency_samples else 0.0
                print(f"  [{elapsed:5.1f}s] Pose: ({self.current_x:6.2f}, {self.current_y:6.2f}) | Rem: {dist_rem:5.2f}m | Obstacle Dist: {self.min_clearance:5.2f}m | FPS: {current_fps:4.1f} | Lat: {current_lat:5.1f}ms")
                last_log_time = now

            if elapsed > timeout_sec:
                self.get_logger().error(f"Navigation timed out after {timeout_sec}s!")
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

        print(f"--> Leg Result: {status_str} in {duration:.2f}s | Final Pose: ({final_x:.3f}, {final_y:.3f}) | Error: {error_dist:.3f}m | Clearance: {self.min_clearance:.3f}m")

        return {
            'trial_id': trial_id,
            'leg': leg_name,
            'status': status_str,
            'duration': round(duration, 2),
            'target_x': round(target_x, 3),
            'target_y': round(target_y, 3),
            'final_x': round(final_x, 3),
            'final_y': round(final_y, 3),
            'error_dist': round(error_dist, 3),
            'path_length': round(self.leg_path_length, 2),
            'min_clearance': round(self.min_clearance, 3),
            'avg_fps': avg_fps,
            'avg_latency_ms': avg_latency
        }


def format_stat(values):
    if not values:
        return "N/A"
    mean_val = statistics.mean(values)
    if len(values) > 1:
        stdev_val = statistics.stdev(values)
        return f"{mean_val:.2f} ± {stdev_val:.2f} (min: {min(values):.2f}, max: {max(values):.2f})"
    return f"{mean_val:.2f}"


def run_benchmark():
    parser = argparse.ArgumentParser(description="Headless Automated Evaluation Runner for SIH26126 UGV")
    parser.add_argument('--trials', type=int, default=3, help='Number of full round-trip trials (default: 3)')
    parser.add_argument('--outbound-x', type=float, default=7.0, help='Outbound target X coordinate')
    parser.add_argument('--outbound-y', type=float, default=0.0, help='Outbound target Y coordinate')
    parser.add_argument('--outbound-yaw', type=float, default=0.0, help='Outbound target yaw (rad)')
    parser.add_argument('--return-x', type=float, default=0.0, help='Return target X coordinate')
    parser.add_argument('--return-y', type=float, default=0.0, help='Return target Y coordinate')
    parser.add_argument('--return-yaw', type=float, default=math.pi, help='Return target yaw (rad)')
    parser.add_argument('--timeout', type=float, default=60.0, help='Per-leg timeout in seconds')
    parser.add_argument('--output-dir', type=str, default='eval/logs', help='Directory for benchmark logs')

    args, unknown = parser.parse_known_args()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    rclpy.init()
    harness = AutomatedEvalHarness(args)

    if not harness.wait_for_services(timeout_sec=30.0):
        print("ERROR: Prerequisite services not ready. Exiting.")
        harness.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    all_results = []
    print(f"\n=======================================================")
    print(f" Starting SIH 2026 Automated Benchmark: {args.trials} Trials")
    print(f" Outbound: ({args.outbound_x}, {args.outbound_y}) | Return: ({args.return_x}, {args.return_y})")
    print(f" Natural Boulder Hazard at (5.0, 0.2, r=0.7m)")
    print(f"=======================================================\n")

    for trial in range(1, args.trials + 1):
        # 1. Outbound Leg (0,0) -> (7,0)
        res_out = harness.execute_nav_leg(
            trial_id=trial,
            leg_name="Outbound (A->B)",
            target_x=args.outbound_x,
            target_y=args.outbound_y,
            target_yaw=args.outbound_yaw,
            timeout_sec=args.timeout
        )
        all_results.append(res_out)

        # Settle buffer between legs
        time.sleep(2.0)

        # 2. Return Leg (7,0) -> (0,0)
        res_ret = harness.execute_nav_leg(
            trial_id=trial,
            leg_name="Return (B->A)",
            target_x=args.return_x,
            target_y=args.return_y,
            target_yaw=args.return_yaw,
            timeout_sec=args.timeout
        )
        all_results.append(res_ret)

        time.sleep(2.0)

    # Export to CSV
    csv_file = os.path.join(args.output_dir, f"benchmark_runs_{timestamp}.csv")
    fieldnames = ['trial_id', 'leg', 'status', 'duration', 'target_x', 'target_y', 'final_x', 'final_y', 'error_dist', 'path_length', 'min_clearance', 'avg_fps', 'avg_latency_ms']
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)

    # Compute Statistical Summaries
    outbound_runs = [r for r in all_results if r['leg'] == "Outbound (A->B)"]
    return_runs = [r for r in all_results if r['leg'] == "Return (B->A)"]

    total_legs = len(all_results)
    succeeded_legs = sum(1 for r in all_results if r['status'] == 'SUCCEEDED')
    success_rate = (succeeded_legs / total_legs) * 100.0 if total_legs > 0 else 0.0

    out_times = [r['duration'] for r in outbound_runs if r['status'] == 'SUCCEEDED']
    ret_times = [r['duration'] for r in return_runs if r['status'] == 'SUCCEEDED']
    
    # Calculate roundtrip times per trial
    roundtrip_times = []
    for t in range(1, args.trials + 1):
        t_out = [r['duration'] for r in outbound_runs if r['trial_id'] == t and r['status'] == 'SUCCEEDED']
        t_ret = [r['duration'] for r in return_runs if r['trial_id'] == t and r['status'] == 'SUCCEEDED']
        if t_out and t_ret:
            roundtrip_times.append(t_out[0] + t_ret[0])

    out_errors = [r['error_dist'] for r in outbound_runs if r['status'] == 'SUCCEEDED']
    ret_errors = [r['error_dist'] for r in return_runs if r['status'] == 'SUCCEEDED']
    clearances = [r['min_clearance'] for r in all_results if r['min_clearance'] < float('inf')]
    fps_vals = [r['avg_fps'] for r in all_results if r['avg_fps'] > 0.0]
    latency_vals = [r['avg_latency_ms'] for r in all_results if r['avg_latency_ms'] > 0.0]

    # Generate Markdown Report
    md_file = os.path.join(args.output_dir, f"benchmark_report_{timestamp}.md")
    with open(md_file, 'w') as f:
        f.write(f"# SIH 2026 Autonomous Navigation Benchmark Report\n\n")
        f.write(f"- **Timestamp:** {timestamp}\n")
        f.write(f"- **Team:** Tikka Techies | SIH26126 (BEL)\n")
        f.write(f"- **Trials Completed:** {args.trials} ({total_legs} total legs)\n")
        f.write(f"- **Navigation Success Rate:** **{success_rate:.1f}%** ({succeeded_legs}/{total_legs})\n\n")
        f.write(f"## 1. Statistical Aggregates (Mean ± Std Dev)\n\n")
        f.write(f"| Metric Family | Metric Name | Measured Distribution (μ ± σ) | Range [Min - Max] |\n")
        f.write(f"|---|---|---|---|\n")
        f.write(f"| **Navigation** | Outbound Transit Time ($t_{{out}}$) | {format_stat(out_times)} s | [{min(out_times) if out_times else 0:.2f}s - {max(out_times) if out_times else 0:.2f}s] |\n")
        f.write(f"| **Navigation** | Return Transit Time ($t_{{ret}}$) | {format_stat(ret_times)} s | [{min(ret_times) if ret_times else 0:.2f}s - {max(ret_times) if ret_times else 0:.2f}s] |\n")
        f.write(f"| **Navigation** | Total Round-Trip Time | {format_stat(roundtrip_times)} s | [{min(roundtrip_times) if roundtrip_times else 0:.2f}s - {max(roundtrip_times) if roundtrip_times else 0:.2f}s] |\n")
        f.write(f"| **Precision** | Outbound Radial Error at B ($\\Delta_B$) | {format_stat(out_errors)} m | [{min(out_errors) if out_errors else 0:.3f}m - {max(out_errors) if out_errors else 0:.3f}m] |\n")
        f.write(f"| **Precision** | Return Radial Error at Origin ($\\Delta_A$) | {format_stat(ret_errors)} m | [{min(ret_errors) if ret_errors else 0:.3f}m - {max(ret_errors) if ret_errors else 0:.3f}m] |\n")
        f.write(f"| **Safety** | Min Boulder Clearance ($r=0.7$m @ $5.0,0.2$) | {format_stat(clearances)} m | [{min(clearances) if clearances else 0:.3f}m - {max(clearances) if clearances else 0:.3f}m] |\n")
        f.write(f"| **Perception** | Real-Time Segmentation FPS | {format_stat(fps_vals)} FPS | [{min(fps_vals) if fps_vals else 0:.1f} - {max(fps_vals) if fps_vals else 0:.1f}] |\n")
        f.write(f"| **Perception** | End-to-End Inference Latency | {format_stat(latency_vals)} ms | [{min(latency_vals) if latency_vals else 0:.1f}ms - {max(latency_vals) if latency_vals else 0:.1f}ms] |\n\n")

        f.write(f"## 2. Granular Per-Run Telemetry\n\n")
        f.write(f"| Trial | Leg | Status | Duration (s) | Final Pose (x, y) | Radial Error (m) | Path Length (m) | Min Clearance (m) | AI FPS | AI Latency (ms) |\n")
        f.write(f"|---|---|---|---|---|---|---|---|---|---|\n")
        for r in all_results:
            f.write(f"| {r['trial_id']} | {r['leg']} | **{r['status']}** | {r['duration']:.2f} | ({r['final_x']:.2f}, {r['final_y']:.2f}) | {r['error_dist']:.3f} | {r['path_length']:.2f} | {r['min_clearance']:.2f} | {r['avg_fps']:.1f} | {r['avg_latency_ms']:.1f} |\n")

    print("\n=======================================================")
    print(f" BENCHMARK COMPLETE: {success_rate:.1f}% Success Rate ({succeeded_legs}/{total_legs})")
    print(f" CSV Saved: {csv_file}")
    print(f" Markdown Report Saved: {md_file}")
    print(f"=======================================================")
    print(f" Outbound Transit Time:  {format_stat(out_times)} s")
    print(f" Return Transit Time:    {format_stat(ret_times)} s")
    print(f" Total Round-Trip Time:  {format_stat(roundtrip_times)} s")
    print(f" Outbound Goal Error:    {format_stat(out_errors)} m")
    print(f" Return Goal Error:      {format_stat(ret_errors)} m")
    print(f" Min Boulder Clearance:  {format_stat(clearances)} m")
    print(f" Perception FPS:         {format_stat(fps_vals)} FPS")
    print(f" Perception Latency:     {format_stat(latency_vals)} ms")
    print("=======================================================\n")

    harness.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    run_benchmark()
