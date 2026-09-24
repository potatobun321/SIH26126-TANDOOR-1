#!/usr/bin/env python3
"""
benchmark_dynamic_obstacle.py — Dynamic Obstacle Avoidance Benchmark for SIH26126 UGV
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Evaluates real-time collision avoidance, reactive deceleration, and dynamic clearance
against a moving patrol hazard crossing the primary trail at x = 3.2m.
"""

import os
import sys
import time
import math
import argparse
import datetime
import statistics
import json
import csv

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rosgraph_msgs.msg import Clock
from std_msgs.msg import Float32
from nav2_msgs.action import NavigateToPose

# Hazard Definition (Matches sim/worlds/outdoor_terrain.sdf)
HAZARD_X = 3.2
HAZARD_Y_MIN = -2.2
HAZARD_Y_MAX = 2.2
HAZARD_PERIOD = 14.0  # 7.0s forward, 7.0s backward
HAZARD_RADIUS = 0.35
ROBOT_RADIUS = 0.35
COLLISION_DISTANCE = HAZARD_RADIUS + ROBOT_RADIUS  # 0.70m center-to-center


class DynamicObstacleBenchmark(Node):
    def __init__(self, target_x=7.0, target_y=0.0):
        super().__init__('benchmark_dynamic_obstacle')
        self.target_x = target_x
        self.target_y = target_y

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.current_speed = 0.0
        self.has_odom = False

        self.sim_time = 0.0
        self.has_clock = False

        self.min_scan_forward = float('inf')
        self.last_cmd_vel = Twist()

        # Telemetry History
        self.telemetry = []
        self.min_clearance_center = float('inf')
        self.min_clearance_surface = float('inf')
        self.collision_detected = False
        self.collision_events = 0

        self.deceleration_events = 0
        self.yield_time_total = 0.0
        self.is_yielding = False
        self.yield_start_time = 0.0

        # Subscriptions
        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.create_subscription(Clock, '/clock', self._clock_callback, 10)
        self.create_subscription(LaserScan, '/scan', self._scan_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self._cmd_vel_callback, 10)

        self.get_logger().info("Dynamic Obstacle Benchmark Harness initialized.")

    def _clock_callback(self, msg: Clock):
        self.sim_time = msg.clock.sec + msg.clock.nanosec * 1e-9
        self.has_clock = True

    def _extract_yaw(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _odom_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        v = msg.twist.twist.linear

        self.current_x = p.x
        self.current_y = p.y
        self.current_yaw = self._extract_yaw(q)
        self.current_speed = math.hypot(v.x, v.y)
        self.has_odom = True

        # Compute ground-truth hazard position at current sim_time
        hazard_y = self.get_hazard_y(self.sim_time)
        dist_center = math.hypot(self.current_x - HAZARD_X, self.current_y - hazard_y)
        dist_surface = dist_center - COLLISION_DISTANCE

        if dist_center < self.min_clearance_center:
            self.min_clearance_center = dist_center
            self.min_clearance_surface = dist_surface

        if dist_center < COLLISION_DISTANCE:
            self.collision_detected = True
            self.collision_events += 1

        # Check for yielding / dynamic deceleration in the interaction zone (x in [1.5, 4.5])
        in_interaction_zone = (1.5 <= self.current_x <= 4.5)
        if in_interaction_zone:
            if self.current_speed < 0.10 and not self.is_yielding:
                self.is_yielding = True
                self.yield_start_time = self.sim_time
                self.deceleration_events += 1
            elif self.current_speed >= 0.15 and self.is_yielding:
                self.is_yielding = False
                if self.yield_start_time > 0:
                    self.yield_time_total += (self.sim_time - self.yield_start_time)

        # Log sample
        self.telemetry.append({
            'sim_time': round(self.sim_time, 3),
            'robot_x': round(self.current_x, 3),
            'robot_y': round(self.current_y, 3),
            'speed': round(self.current_speed, 3),
            'hazard_y': round(hazard_y, 3),
            'dist_center': round(dist_center, 3),
            'dist_surface': round(dist_surface, 3),
            'min_scan_fwd': round(self.min_scan_forward, 3)
        })

    def _scan_callback(self, msg: LaserScan):
        # Forward cone: +/- 45 deg
        angles = [msg.angle_min + i * msg.angle_increment for i in range(len(msg.ranges))]
        forward_ranges = [
            r for r, a in zip(msg.ranges, angles)
            if abs(a) < math.radians(45) and msg.range_min < r < msg.range_max
        ]
        if forward_ranges:
            self.min_scan_forward = min(forward_ranges)

    def _cmd_vel_callback(self, msg: Twist):
        self.last_cmd_vel = msg

    @staticmethod
    def get_hazard_y(t: float) -> float:
        """Returns the y position of the dynamic obstacle at sim time t."""
        tau = t % HAZARD_PERIOD
        half_period = HAZARD_PERIOD / 2.0  # 7.0s
        span = HAZARD_Y_MAX - HAZARD_Y_MIN  # 4.4m
        if tau <= half_period:
            # Moving from MIN to MAX (-2.2 -> 2.2)
            frac = tau / half_period
            return HAZARD_Y_MIN + frac * span
        else:
            # Moving from MAX to MIN (2.2 -> -2.2)
            frac = (tau - half_period) / half_period
            return HAZARD_Y_MAX - frac * span

    def send_navigation_goal(self, gx: float, gy: float, timeout_sec: float = 60.0):
        self.get_logger().info(f"Waiting for 'navigate_to_pose' action server...")
        if not self._action_client.wait_for_server(timeout_sec=15.0):
            self.get_logger().error("Nav2 Action Server not available!")
            return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(gx)
        goal_msg.pose.pose.position.y = float(gy)
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0

        self.get_logger().info(f"Sending Goal: ({gx:.2f}, {gy:.2f}) crossing dynamic hazard at x={HAZARD_X}m...")
        send_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Navigation goal rejected!")
            return False

        self.get_logger().info("Goal accepted. Tracking evasive maneuvers...")
        res_future = goal_handle.get_result_async()

        start_time = time.time()
        start_sim_time = self.sim_time
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if res_future.done():
                result = res_future.result()
                status = result.status
                self.get_logger().info(f"Goal complete with status: {status}")
                return status == GoalStatus.STATUS_SUCCEEDED

            if (time.time() - start_time) > timeout_sec:
                self.get_logger().warn(f"Goal timed out after {timeout_sec}s!")
                cancel_future = goal_handle.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future)
                return False


def main():
    parser = argparse.ArgumentParser(description="Dynamic Obstacle Avoidance Benchmark")
    parser.add_argument('--target_x', type=float, default=7.0, help="Target X coordinate across trail")
    parser.add_argument('--target_y', type=float, default=0.0, help="Target Y coordinate across trail")
    parser.add_argument('--timeout', type=float, default=60.0, help="Max timeout seconds")
    parser.add_argument('--output_dir', type=str, default="eval", help="Directory to save log")
    args = parser.parse_args()

    rclpy.init()
    node = DynamicObstacleBenchmark(target_x=args.target_x, target_y=args.target_y)

    print("\n" + "="*70)
    print(" SIH26126 — PHASE 5: DYNAMIC OBSTACLE AVOIDANCE BENCHMARK")
    print(" Team: Tikka Techies | Bharat Electronics Limited (BEL)")
    print("="*70)

    # Wait for sensor sync
    print("[*] Synchronizing with /odom and /clock...")
    for _ in range(50):
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.has_odom and node.has_clock:
            break
        time.sleep(0.05)

    if not node.has_odom:
        print("[!] ERROR: No odometry received. Is Gazebo & Nav2 running?")
        sys.exit(1)

    print(f"[*] Initial UGV Pose: ({node.current_x:.2f}, {node.current_y:.2f}) | Sim Time: {node.sim_time:.2f}s")
    print(f"[*] Dynamic Hazard: Patrol along x={HAZARD_X}m between y=[{HAZARD_Y_MIN}, {HAZARD_Y_MAX}]m, Period={HAZARD_PERIOD}s")
    print(f"[*] Goal Target: ({args.target_x:.2f}, {args.target_y:.2f})")

    t_start = time.time()
    sim_t_start = node.sim_time
    success = node.send_navigation_goal(args.target_x, args.target_y, timeout_sec=args.timeout)
    t_end = time.time()
    sim_t_end = node.sim_time

    # Close any open yield interval
    if node.is_yielding and node.yield_start_time > 0:
        node.yield_time_total += (node.sim_time - node.yield_start_time)

    wall_duration = t_end - t_start
    sim_duration = sim_t_end - sim_t_start
    final_dist = math.hypot(node.current_x - args.target_x, node.current_y - args.target_y)

    print("\n" + "="*70)
    print(" BENCHMARK RESULTS — PHASE 5 DYNAMIC AVOIDANCE")
    print("="*70)
    print(f" Navigation Result          : {'SUCCESS (GOAL REACHED)' if success else 'FAILED / TIMEOUT'}")
    print(f" Final Position             : ({node.current_x:.3f}, {node.current_y:.3f}) [Target: ({args.target_x}, {args.target_y})]")
    print(f" Radial Target Accuracy     : {final_dist:.3f} m")
    print(f" Total Traversal Time       : {sim_duration:.2f} s (Wall: {wall_duration:.2f} s)")
    print(f" Min Clearance to Hazard    : {node.min_clearance_surface:.3f} m (Center: {node.min_clearance_center:.3f} m)")
    print(f" Collision Count            : {node.collision_events} (Collided: {node.collision_detected})")
    print(f" Reactive Yield/Stop Count  : {node.deceleration_events}")
    print(f" Total Yield/Wait Duration  : {node.yield_time_total:.2f} s")
    print("="*70)

    # Save summary and CSV telemetry
    os.makedirs(args.output_dir, exist_ok=True)
    stamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = os.path.join(args.output_dir, f"dynamic_obstacle_summary_{stamp_str}.json")
    csv_file = os.path.join(args.output_dir, f"dynamic_obstacle_telemetry_{stamp_str}.csv")

    summary_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'target_x': args.target_x,
        'target_y': args.target_y,
        'success': success,
        'final_x': node.current_x,
        'final_y': node.current_y,
        'radial_error_m': final_dist,
        'traversal_time_sim_s': sim_duration,
        'traversal_time_wall_s': wall_duration,
        'min_clearance_surface_m': node.min_clearance_surface,
        'min_clearance_center_m': node.min_clearance_center,
        'collision_detected': node.collision_detected,
        'collision_events': node.collision_events,
        'reactive_yield_count': node.deceleration_events,
        'yield_time_total_s': node.yield_time_total,
        'telemetry_samples': len(node.telemetry)
    }

    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"[+] Summary saved to: {summary_file}")

    if node.telemetry:
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=node.telemetry[0].keys())
            writer.writeheader()
            writer.writerows(node.telemetry)
        print(f"[+] High-rate telemetry ({len(node.telemetry)} samples) saved to: {csv_file}")

    rclpy.shutdown()


if __name__ == '__main__':
    main()
