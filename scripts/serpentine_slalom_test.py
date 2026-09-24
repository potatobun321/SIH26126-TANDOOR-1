#!/usr/bin/env python3
"""
serpentine_slalom_test.py — High-Difficulty Serpentine Slalom Obstacle Weave
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Executes a continuous multi-obstacle S-curve slalom weaving alternatingly:
1. North flank past initial trail markers (2.0, +1.8)
2. Starboard cut across dynamic hazard zone (3.6, -1.8)
3. Port weave around central boulder (5.2, +2.0)
4. Starboard weave between boulder and tree trunk (7.2, -1.8)
5. Outpost frontier apex (9.0, +1.0)
6. Reverse serpentine recovery back to Base Camp (0.0, 0.0)
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
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from rosgraph_msgs.msg import Clock
from std_msgs.msg import Float32
from nav2_msgs.action import NavigateToPose

# Known Obstacle Coordinates
BOULDER_X = 5.0
BOULDER_Y = 0.35
BOULDER_RADIUS = 0.50

TREE_X = 8.5
TREE_Y = -3.0
TREE_RADIUS = 0.42

DYNAMIC_HAZARD_X = 3.4
DYNAMIC_HAZARD_PERIOD = 12.0
DYNAMIC_HAZARD_Y_MIN = 1.2
DYNAMIC_HAZARD_Y_MAX = 2.6
COLLISION_DISTANCE = 0.70  # 0.35m UGV + 0.35m hazard

SLALOM_WAYPOINTS = [
    {
        'name': 'Weave 1: North Trail Crest',
        'x': 2.0, 'y': 1.8, 'yaw': -1.15,
        'desc': 'Port slalom around start markers, setting up acute diagonal cut'
    },
    {
        'name': 'Weave 2: South Hazard Crossing',
        'x': 3.8, 'y': -1.8, 'yaw': 1.17,
        'desc': 'Acute diagonal cut across dynamic patrol corridor to South flank'
    },
    {
        'name': 'Weave 3: North Boulder Bypass',
        'x': 6.6, 'y': 1.1, 'yaw': -0.80,
        'desc': 'Approach North of boulder with safe 1.10m clearance from central boulder'
    },
    {
        'name': 'Weave 4: Tree/Boulder Corridor',
        'x': 7.0, 'y': -1.4, 'yaw': 0.99,
        'desc': 'Thread clearance corridor between central boulder and scrub tree'
    },
    {
        'name': 'Weave 5: Deep Frontier Apex',
        'x': 9.0, 'y': 1.0, 'yaw': 3.14,
        'desc': 'Slalom apex beyond tree perimeter; initiating return snake'
    },
    {
        'name': 'Weave 6: South Corridor Return',
        'x': 4.5, 'y': -1.2, 'yaw': 3.14,
        'desc': 'Return through south corridor with clear direct line-of-sight to Base Camp'
    },
    {
        'name': 'Weave 7: Base Camp Home Closure',
        'x': 0.0, 'y': 0.0, 'yaw': 3.14,
        'desc': 'Final home closure back to Origin Base Camp'
    }
]


class SerpentineSlalomHarness(Node):
    def __init__(self, args):
        super().__init__('serpentine_slalom_harness')
        self.args = args

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.current_speed = 0.0
        self.has_odom = False

        self.sim_time = 0.0
        self.has_clock = False

        self.leg_path_length = 0.0
        self.last_x = None
        self.last_y = None

        self.min_boulder_clearance = float('inf')
        self.min_tree_clearance = float('inf')
        self.min_hazard_clearance = float('inf')
        self.collision_detected = False

        self.fps_samples = []
        self.latency_samples = []

        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.create_subscription(Clock, '/clock', self._clock_callback, 10)
        self.create_subscription(Float32, '/perception/fps', self._fps_callback, 10)
        self.create_subscription(Float32, '/perception/latency_ms', self._latency_callback, 10)

        self.get_logger().info("Serpentine Slalom Harness initialized.")

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

        if self.last_x is not None and self.last_y is not None:
            step_dist = math.hypot(self.current_x - self.last_x, self.current_y - self.last_y)
            if step_dist < 1.0:
                self.leg_path_length += step_dist

        self.last_x = self.current_x
        self.last_y = self.current_y

        # Boulder Clearance
        dist_boulder = math.hypot(self.current_x - BOULDER_X, self.current_y - BOULDER_Y) - BOULDER_RADIUS
        if dist_boulder < self.min_boulder_clearance:
            self.min_boulder_clearance = dist_boulder

        # Tree Clearance
        dist_tree = math.hypot(self.current_x - TREE_X, self.current_y - TREE_Y) - TREE_RADIUS
        if dist_tree < self.min_tree_clearance:
            self.min_tree_clearance = dist_tree

        # Dynamic Hazard Clearance
        hazard_y = self.get_hazard_y(self.sim_time)
        dist_hazard = math.hypot(self.current_x - DYNAMIC_HAZARD_X, self.current_y - hazard_y) - COLLISION_DISTANCE
        if dist_hazard < self.min_hazard_clearance:
            self.min_hazard_clearance = dist_hazard

        if dist_boulder < 0.0 or dist_tree < 0.0 or dist_hazard < -0.15:
            self.collision_detected = True

    def _fps_callback(self, msg: Float32):
        if msg.data > 0:
            self.fps_samples.append(msg.data)

    def _latency_callback(self, msg: Float32):
        if msg.data > 0:
            self.latency_samples.append(msg.data)

    @staticmethod
    def get_hazard_y(t: float) -> float:
        tau = t % DYNAMIC_HAZARD_PERIOD
        half = DYNAMIC_HAZARD_PERIOD / 2.0
        span = DYNAMIC_HAZARD_Y_MAX - DYNAMIC_HAZARD_Y_MIN
        if tau <= half:
            return DYNAMIC_HAZARD_Y_MIN + (tau / half) * span
        else:
            return DYNAMIC_HAZARD_Y_MAX - ((tau - half) / half) * span

    def execute_slalom_leg(self, wp, index, total):
        print("\n" + "-"*70)
        print(f"[*] SLALOM LEG {index}/{total}: {wp['name']}")
        print(f"    Target: ({wp['x']:.2f}, {wp['y']:.2f}) | Yaw: {wp['yaw']:.2f} rad")
        print(f"    Tactical Mission: {wp['desc']}")
        print("-"*70)

        self.leg_path_length = 0.0
        self.last_x = self.current_x
        self.last_y = self.current_y
        self.min_boulder_clearance = float('inf')
        self.min_tree_clearance = float('inf')
        self.min_hazard_clearance = float('inf')
        self.fps_samples.clear()
        self.latency_samples.clear()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(wp['x'])
        goal_msg.pose.pose.position.y = float(wp['y'])
        goal_msg.pose.pose.position.z = 0.0

        yaw = wp['yaw']
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        goal_handle = None
        for attempt in range(8):
            send_future = self._action_client.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(self, send_future)
            gh = send_future.result()
            if gh and gh.accepted:
                goal_handle = gh
                break
            print(f"[*] Nav2 lifecycle activating (attempt {attempt+1}/8)... waiting 2.0s")
            time.sleep(2.0)

        if not goal_handle or not goal_handle.accepted:
            print(f"[!] Goal rejected for {wp['name']}!")
            return False, 0.0, 0.0, 0.0, 0.0

        res_future = goal_handle.get_result_async()
        t_start = time.time()
        sim_start = self.sim_time
        timeout_sim = self.args.leg_timeout

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if res_future.done():
                status = res_future.result().status
                succeeded = (status == GoalStatus.STATUS_SUCCEEDED)
                t_elapsed = time.time() - t_start
                sim_elapsed = self.sim_time - sim_start
                rad_err = math.hypot(self.current_x - wp['x'], self.current_y - wp['y'])

                print(f"[+] Status: {'SUCCEEDED' if succeeded else f'FAILED ({status})'} in {t_elapsed:.2f}s (sim: {sim_elapsed:.2f}s)")
                print(f"    Final Pose: ({self.current_x:.2f}, {self.current_y:.2f}) | Error: {rad_err:.3f}m | Path: {self.leg_path_length:.2f}m")
                print(f"    Min Clearances -> Boulder: {self.min_boulder_clearance:.2f}m | Tree: {self.min_tree_clearance:.2f}m | Hazard: {self.min_hazard_clearance:.2f}m")
                return succeeded, t_elapsed, rad_err, self.leg_path_length, self.min_hazard_clearance

            # Check timeout in simulation seconds (physics time)
            if (self.sim_time - sim_start) > timeout_sim:
                print(f"[!] Leg timed out after {timeout_sim}s of sim time!")
                cancel_future = goal_handle.cancel_goal_async()
                rclpy.spin_until_future_complete(self, cancel_future)
                return False, time.time() - t_start, math.hypot(self.current_x - wp['x'], self.current_y - wp['y']), self.leg_path_length, self.min_hazard_clearance


def main():
    parser = argparse.ArgumentParser(description="Serpentine Slalom Obstacle Weave")
    parser.add_argument('--leg_timeout', type=float, default=90.0, help="Max time per weave leg (s)")
    parser.add_argument('--output_dir', type=str, default="eval", help="Log output directory")
    args = parser.parse_args()

    rclpy.init()
    node = SerpentineSlalomHarness(args)

    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    print("\n" + "="*75)
    print(" SIH26126 — HIGH-DIFFICULTY SERPENTINE SLALOM OBSTACLE WEAVE")
    print(" Team: Tikka Techies | Bharat Electronics Limited (BEL)")
    print("="*75)

    print("[*] Synchronizing with sensors & Nav2 action server...")
    if not node._action_client.wait_for_server(timeout_sec=30.0):
        print("[!] ERROR: Nav2 Action Server not available!")
        sys.exit(1)

    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.has_odom and node.has_clock:
            break
        time.sleep(0.05)

    print(f"[*] Initial UGV Position: ({node.current_x:.2f}, {node.current_y:.2f}) | Yaw: {node.current_yaw:.2f} rad")
    print(f"[*] Starting 6-Weave Serpentine Slalom across boulder, tree, markers, and dynamic hazard...")

    total_start = time.time()
    leg_results = []
    total_path = 0.0

    for i, wp in enumerate(SLALOM_WAYPOINTS, start=1):
        succ, duration, err, dist, min_haz = node.execute_slalom_leg(wp, i, len(SLALOM_WAYPOINTS))
        total_path += dist
        leg_results.append({
            'index': i,
            'name': wp['name'],
            'success': succ,
            'duration_s': round(duration, 2),
            'target_x': wp['x'],
            'target_y': wp['y'],
            'final_x': round(node.current_x, 3),
            'final_y': round(node.current_y, 3),
            'radial_error_m': round(err, 3),
            'path_length_m': round(dist, 2),
            'min_boulder_clearance_m': round(node.min_boulder_clearance, 2),
            'min_tree_clearance_m': round(node.min_tree_clearance, 2),
            'min_hazard_clearance_m': round(min_haz, 2)
        })

    total_duration = time.time() - total_start
    all_success = all(r['success'] for r in leg_results)
    success_rate = (sum(1 for r in leg_results if r['success']) / len(leg_results)) * 100.0
    mean_err = statistics.mean(r['radial_error_m'] for r in leg_results)

    print("\n" + "="*75)
    print(" SERPENTINE SLALOM BENCHMARK SUMMARY")
    print("="*75)
    print(f" Overall Mission Outcome   : {'PERFECT (100% SLALOM COMPLETE)' if all_success else f'{success_rate:.1f}% COMPLETE'}")
    print(f" Successful Weave Legs     : {sum(1 for r in leg_results if r['success'])} / {len(leg_results)}")
    print(f" Total Traversed Distance  : {total_path:.2f} m")
    print(f" Total Slalom Duration     : {total_duration:.2f} s")
    print(f" Mean Radial Positioning   : {mean_err:.3f} m")
    print(f" Total Collision Events    : {'ZERO (0 Collisions)' if not node.collision_detected else 'COLLISION OCCURRED'}")
    print("="*75)

    print("\nLEG BREAKDOWN:")
    print(f"{'#':<3} | {'Weave Name':<28} | {'Status':<9} | {'Time (s)':<8} | {'Path (m)':<8} | {'Error (m)':<9} | {'Min Clr (m)':<11}")
    print("-" * 88)
    for r in leg_results:
        min_clr = min(r['min_boulder_clearance_m'], r['min_tree_clearance_m'], r['min_hazard_clearance_m'])
        print(f"{r['index']:<3} | {r['name']:<28} | {'SUCCESS' if r['success'] else 'FAILED':<9} | {r['duration_s']:<8.2f} | {r['path_length_m']:<8.2f} | {r['radial_error_m']:<9.3f} | {min_clr:<11.2f}")
    print("="*75)

    # Save to JSON and CSV
    os.makedirs(args.output_dir, exist_ok=True)
    stamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(args.output_dir, f"serpentine_slalom_summary_{stamp_str}.json")
    with open(summary_path, 'w') as f:
        json.dump({
            'timestamp': datetime.datetime.now().isoformat(),
            'total_success': all_success,
            'success_rate_pct': success_rate,
            'total_duration_s': total_duration,
            'total_path_m': total_path,
            'mean_radial_error_m': mean_err,
            'collision_detected': node.collision_detected,
            'legs': leg_results
        }, f, indent=2)

    print(f"\n[+] Full Slalom benchmark logged to: {summary_path}")
    rclpy.shutdown()


if __name__ == '__main__':
    main()
