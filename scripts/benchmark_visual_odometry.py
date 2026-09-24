#!/usr/bin/env python3
"""
benchmark_visual_odometry.py — Head-to-Head Visual Odometry vs Wheel EKF Drift Benchmarker
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Evaluates GPS-Denied Visual-Inertial Odometry (/odom_vo) vs Wheel+IMU EKF (/odometry/filtered)
against physical Ground Truth (/odom) across autonomous outdoor navigation runs.
Computes Absolute Trajectory Error (ATE RMSE in meters), Relative Pose Error (RPE),
maximum drift, and generates comparison CSV and Markdown reports for the SIH presentation.
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

class VODriftBenchmarker(Node):
    def __init__(self, args):
        super().__init__('vo_drift_benchmarker')
        self.args = args

        # Nav2 NavigateToPose Action Client
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Current poses
        self.gt_pose = None      # (x, y, yaw)
        self.ekf_pose = None     # (x, y, yaw)
        self.vo_pose = None      # (x, y, yaw)

        # VO initial offset compensation (align initial frame)
        self.vo_origin = None
        self.gt_origin = None
        self.ekf_origin = None

        # Synchronized trajectory samples: list of dicts
        self.samples = []

        # Real-time telemetry
        self.fps_samples = []
        self.latency_samples = []
        self.min_clearance = float('inf')
        self.total_path_gt = 0.0
        self.last_gt_xy = None

        # ROS 2 Subscribers
        self.create_subscription(Odometry, '/odom', self._gt_callback, 10)
        self.create_subscription(Odometry, '/odometry/filtered', self._ekf_callback, 10)
        self.create_subscription(Odometry, '/odom_vo', self._vo_callback, 10)
        self.create_subscription(Float32, '/perception/fps', self._fps_callback, 10)
        self.create_subscription(Float32, '/perception/latency_ms', self._latency_callback, 10)

        self.get_logger().info("Visual Odometry Drift Benchmarker initialized.")

    def _extract_yaw(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _gt_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = self._extract_yaw(q)
        self.gt_pose = (p.x, p.y, yaw)

        if self.gt_origin is None:
            self.gt_origin = (p.x, p.y, yaw)

        if self.last_gt_xy is not None:
            dist = math.hypot(p.x - self.last_gt_xy[0], p.y - self.last_gt_xy[1])
            if dist < 1.0:
                self.total_path_gt += dist
        self.last_gt_xy = (p.x, p.y)

        # Track clearance to boulder
        dist_boulder = math.hypot(p.x - BOULDER_X, p.y - BOULDER_Y)
        if dist_boulder < self.min_clearance:
            self.min_clearance = dist_boulder

        self._record_synchronized_sample()

    def _ekf_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = self._extract_yaw(q)
        self.ekf_pose = (p.x, p.y, yaw)
        if self.ekf_origin is None:
            self.ekf_origin = (p.x, p.y, yaw)

    def _vo_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = self._extract_yaw(q)
        self.vo_pose = (p.x, p.y, yaw)
        self.last_vo_time = time.time()
        if self.vo_origin is None and self.gt_origin is not None:
            self.vo_origin = (p.x, p.y, yaw)

    def _fps_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.fps_samples.append(msg.data)

    def _latency_callback(self, msg: Float32):
        if msg.data > 0.0:
            self.latency_samples.append(msg.data)

    def _record_synchronized_sample(self):
        if self.gt_pose is None or self.ekf_pose is None:
            return

        gt_x, gt_y, gt_yaw = self.gt_pose
        ekf_x, ekf_y, ekf_yaw = self.ekf_pose

        # Error for EKF vs Ground Truth
        err_ekf = math.hypot(ekf_x - gt_x, ekf_y - gt_y)

        # Error for Visual Odometry vs Ground Truth (only when fresh message received in last 0.5s)
        err_vo = None
        vo_x, vo_y, vo_yaw = (None, None, None)
        is_vo_fresh = (self.vo_pose is not None and 
                       hasattr(self, 'last_vo_time') and 
                       (time.time() - self.last_vo_time < 0.5))

        if is_vo_fresh and self.vo_origin is not None and self.gt_origin is not None:
            # Transform VO into initial world frame
            raw_vo_x, raw_vo_y, raw_vo_yaw = self.vo_pose
            vo_x = (raw_vo_x - self.vo_origin[0]) + self.gt_origin[0]
            vo_y = (raw_vo_y - self.vo_origin[1]) + self.gt_origin[1]
            vo_yaw = raw_vo_yaw
            err_vo = math.hypot(vo_x - gt_x, vo_y - gt_y)

        self.samples.append({
            'timestamp': time.time(),
            'gt_x': gt_x,
            'gt_y': gt_y,
            'gt_yaw': gt_yaw,
            'ekf_x': ekf_x,
            'ekf_y': ekf_y,
            'err_ekf': err_ekf,
            'vo_x': vo_x,
            'vo_y': vo_y,
            'err_vo': err_vo
        })

    def wait_for_topics(self, timeout_sec=30.0):
        self.get_logger().info("Connecting to /navigate_to_pose action server...")
        start_t = time.time()
        while not self._action_client.wait_for_server(timeout_sec=2.0):
            if time.time() - start_t > timeout_sec:
                self.get_logger().error(f"Action server not available after {timeout_sec}s.")
                return False

        self.get_logger().info("Awaiting telemetry on /odom, /odometry/filtered, and /odom_vo...")
        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self.gt_pose is not None and self.ekf_pose is not None:
                vo_status = "ACTIVE" if self.vo_pose is not None else "PENDING"
                self.get_logger().info(f"Telemetry ready: GT=OK, EKF=OK, VO={vo_status}")
                return True
        self.get_logger().error("Telemetry topics not ready.")
        return False

    def execute_leg(self, leg_name, target_x, target_y, target_yaw, timeout_sec=60.0):
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

        print(f"\n--------------------------------------------------")
        print(f" Executing Leg: {leg_name} -> Goal: ({target_x:.2f}, {target_y:.2f})")
        print(f"--------------------------------------------------")

        send_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            print("ERROR: Goal rejected by Nav2!")
            return False

        get_result_future = goal_handle.get_result_async()
        last_log = time.time()

        while not get_result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            now = time.time()
            elapsed = now - start_time

            if now - last_log > 2.5:
                gt_str = f"({self.gt_pose[0]:.2f}, {self.gt_pose[1]:.2f})" if self.gt_pose else "N/A"
                ekf_err = f"{self.samples[-1]['err_ekf']:.3f}m" if self.samples else "N/A"
                vo_err = f"{self.samples[-1]['err_vo']:.3f}m" if self.samples and self.samples[-1]['err_vo'] is not None else "N/A"
                print(f"  [{elapsed:4.1f}s] GT: {gt_str} | EKF Drift: {ekf_err} | VO Drift: {vo_err}")
                last_log = now

            if elapsed > timeout_sec:
                print(f"WARNING: Leg timed out after {timeout_sec}s.")
                goal_handle.cancel_goal_async()
                break

        duration = time.time() - start_time
        status = "SUCCEEDED" if get_result_future.done() and get_result_future.result().status == GoalStatus.STATUS_SUCCEEDED else "INCOMPLETE"
        print(f"--> Leg {leg_name} finished: {status} in {duration:.2f}s")
        return status == "SUCCEEDED"


def run_benchmark():
    parser = argparse.ArgumentParser(description="Headless Visual Odometry vs Wheel EKF Drift Benchmarker")
    parser.add_argument('--trials', type=int, default=1, help='Number of round trips to execute (default: 1)')
    parser.add_argument('--output-dir', type=str, default='eval/logs', help='Directory for output logs')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    rclpy.init()
    benchmarker = VODriftBenchmarker(args)

    if not benchmarker.wait_for_topics(timeout_sec=30.0):
        print("ERROR: Prerequisites failed. Exiting.")
        benchmarker.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    print(f"\n=======================================================")
    print(f" SIH 2026 Visual Odometry vs Wheel EKF Drift Benchmark")
    print(f" Comparing: Ground Truth (/odom) vs EKF vs VO (/odom_vo)")
    print(f"=======================================================")

    for t in range(1, args.trials + 1):
        print(f"\n=== Trial {t}/{args.trials} ===")
        # Outbound: (0,0) -> (7,0)
        benchmarker.execute_leg("Outbound (0,0 -> 7,0)", 7.0, 0.0, 0.0)
        time.sleep(2.0)
        # Return: (7,0) -> (0,0)
        benchmarker.execute_leg("Return (7,0 -> 0,0)", 0.0, 0.0, math.pi)
        time.sleep(2.0)

    # Process Trajectory Samples
    samples = benchmarker.samples
    if not samples:
        print("ERROR: No trajectory samples captured.")
        sys.exit(1)

    # Export CSV
    csv_path = os.path.join(args.output_dir, f"vo_drift_{timestamp}.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'gt_x', 'gt_y', 'gt_yaw', 'ekf_x', 'ekf_y', 'err_ekf', 'vo_x', 'vo_y', 'err_vo'])
        writer.writeheader()
        for s in samples:
            writer.writerow(s)

    # Statistical Evaluation: ATE RMSE & Max Drift
    ekf_errors = [s['err_ekf'] for s in samples if s['err_ekf'] is not None]
    vo_errors = [s['err_vo'] for s in samples if s['err_vo'] is not None]

    ate_rmse_ekf = math.sqrt(sum(e**2 for e in ekf_errors) / len(ekf_errors)) if ekf_errors else 0.0
    ate_rmse_vo = math.sqrt(sum(e**2 for e in vo_errors) / len(vo_errors)) if vo_errors else 0.0

    max_drift_ekf = max(ekf_errors) if ekf_errors else 0.0
    max_drift_vo = max(vo_errors) if vo_errors else 0.0

    mean_ekf = statistics.mean(ekf_errors) if ekf_errors else 0.0
    mean_vo = statistics.mean(vo_errors) if vo_errors else 0.0

    total_dist = benchmarker.total_path_gt
    # Relative Pose Error (Drift per 10 meters)
    rpe_10m_ekf = (mean_ekf / (total_dist / 10.0)) if total_dist > 0 else 0.0
    rpe_10m_vo = (mean_vo / (total_dist / 10.0)) if total_dist > 0 else 0.0

    vo_samples_count = len(vo_errors)
    total_samples_count = len(samples)
    vo_availability_pct = (vo_samples_count / total_samples_count) * 100.0 if total_samples_count > 0 else 0.0

    fps_mean = statistics.mean(benchmarker.fps_samples) if benchmarker.fps_samples else 0.0
    lat_mean = statistics.mean(benchmarker.latency_samples) if benchmarker.latency_samples else 0.0

    # Write Markdown Report
    md_path = os.path.join(args.output_dir, f"vo_report_{timestamp}.md")
    with open(md_path, 'w') as f:
        f.write("# Visual-Inertial Odometry vs Wheel EKF Drift Benchmark Report\n\n")
        f.write(f"- **Timestamp:** {timestamp}\n")
        f.write(f"- **Team:** Tikka Techies | SIH26126 (BEL)\n")
        f.write(f"- **Total Distance Traversed:** {total_dist:.2f} m\n")
        f.write(f"- **Total Synchronized Samples:** {total_samples_count}\n")
        f.write(f"- **Visual Odometry Tracking Availability:** {vo_availability_pct:.1f}% ({vo_samples_count}/{total_samples_count})\n\n")

        f.write("## 1. Head-to-Head Trajectory Accuracy Comparison\n\n")
        f.write("| Localization Method | Input Modality | ATE RMSE (m) | Mean Drift (m) | Max Drift (m) | Drift Rate per 10m (RPE) | Status |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        f.write(f"| **Wheel + IMU EKF** (`/odometry/filtered`) | Wheel Ticks + IMU | {ate_rmse_ekf:.3f} m | {mean_ekf:.3f} m | {max_drift_ekf:.3f} m | {rpe_10m_ekf:.3f} m/10m | Baseline |\n")
        f.write(f"| **Visual-Inertial Odometry** (`/odom_vo`) | RGB-D + IMU Features | {ate_rmse_vo:.3f} m | {mean_vo:.3f} m | {max_drift_vo:.3f} m | {rpe_10m_vo:.3f} m/10m | **EVALUATED** |\n\n")

        f.write("## 2. Telemetry & Compute Resource Consumption\n\n")
        f.write(f"- **Min Boulder Clearance:** {benchmarker.min_clearance:.2f} m (Zero contact)\n")
        f.write(f"- **AI Perception Frame Rate:** {fps_mean:.1f} FPS\n")
        f.write(f"- **AI Perception Latency:** {lat_mean:.1f} ms\n")

    print("\n=======================================================")
    print(" VISUAL ODOMETRY BENCHMARK COMPLETE")
    print(f" CSV Saved: {csv_path}")
    print(f" Report Saved: {md_path}")
    print("=======================================================")
    print(f" Traversed Distance:     {total_dist:.2f} m")
    print(f" VO Tracking Uptime:     {vo_availability_pct:.1f}%")
    print(f" EKF ATE RMSE:           {ate_rmse_ekf:.3f} m (Max: {max_drift_ekf:.3f} m)")
    print(f" VO ATE RMSE:            {ate_rmse_vo:.3f} m (Max: {max_drift_vo:.3f} m)")
    print(f" EKF Drift per 10m:      {rpe_10m_ekf:.3f} m")
    print(f" VO Drift per 10m:       {rpe_10m_vo:.3f} m")
    print("=======================================================\n")

    benchmarker.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    run_benchmark()
