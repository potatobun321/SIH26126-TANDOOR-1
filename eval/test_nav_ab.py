#!/usr/bin/env python3
import time
import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry

BOULDER_X = 5.0
BOULDER_Y = 0.35
BOULDER_RADIUS = 0.50

class TestNavABRoundTrip(Node):
    def __init__(self):
        super().__init__('test_nav_ab_harness')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.sub_odom = self.create_subscription(Odometry, '/odometry/filtered', self.odom_cb, 10)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_spd = 0.0
        self.min_boulder_clearance = 999.0

    def odom_cb(self, msg: Odometry):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        self.current_spd = math.hypot(vx, vy)
        
        # Track clearance to boulder obstacle surface
        boulder_center_dist = math.hypot(self.current_x - BOULDER_X, self.current_y - BOULDER_Y)
        clearance = boulder_center_dist - BOULDER_RADIUS - 0.42 # account for vehicle half-width
        if clearance < self.min_boulder_clearance:
            self.min_boulder_clearance = clearance

    def navigate_to(self, target_x, target_y, target_yaw, leg_name, timeout_s=45.0):
        print(f"\n[*] Starting {leg_name} -> Target: ({target_x:.1f}, {target_y:.1f})")
        qz = float(math.sin(target_yaw / 2.0))
        qw = float(math.cos(target_yaw / 2.0))

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(target_x)
        goal_msg.pose.pose.position.y = float(target_y)
        goal_msg.pose.pose.orientation.z = qz
        goal_msg.pose.pose.orientation.w = qw

        send_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            print(f"[ERROR] {leg_name} goal was rejected by Nav2!")
            return False

        print(f"[+] {leg_name} ACCEPTED by Nav2. Navigating...")
        start_time = time.time()
        result_future = goal_handle.get_result_async()

        last_print = time.time()
        while rclpy.ok() and not result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            now = time.time()
            if now - last_print > 1.5:
                dist = math.hypot(target_x - self.current_x, target_y - self.current_y)
                print(f"  [T+{(now - start_time):.1f}s] Pos: ({self.current_x:.2f}, {self.current_y:.2f}) | Spd: {self.current_spd:.2f} m/s | Remaining: {dist:.2f} m | Min Boulder Clr: {self.min_boulder_clearance:.2f} m")
                last_print = now

            if now - start_time > timeout_s:
                print(f"[TIMEOUT] Exceeded {timeout_s}s!")
                break

        if result_future.done():
            status = result_future.result().status
            duration = time.time() - start_time
            dist_final = math.hypot(target_x - self.current_x, target_y - self.current_y)
            print(f"[{leg_name} COMPLETED] Status={status} | Duration={duration:.1f}s | Final Error={dist_final:.2f}m")
            if (status == GoalStatus.STATUS_SUCCEEDED or dist_final < 0.45) and self.min_boulder_clearance > 0.0:
                print(f"[SUCCESS] Reached target with positive clearance ({self.min_boulder_clearance:.2f}m)!")
                return True
            else:
                print(f"[FAILED] Leg failed! status={status}, dist={dist_final:.2f}m, clearance={self.min_boulder_clearance:.2f}m")
                return False
        return False

    def run(self):
        print("[*] Waiting for /navigate_to_pose action server...")
        if not self._action_client.wait_for_server(timeout_sec=15.0):
            print("[ERROR] Action server not available!")
            return False

        # Leg 1: Outbound A -> B  (Point B at x=7.5, y=-0.5 so approach stays in south corridor)
        ok_leg1 = self.navigate_to(7.5, -0.5, 0.0, "Leg 1: Point A -> B (Outbound)", timeout_s=90.0)
        if not ok_leg1:
            return False

        time.sleep(1.5)

        # Leg 2a: Diagonal escape SW — clear of boulder (N edge y=+0.85, inflation to y=+1.5)
        #          and tree NEW position at (8.5,-3.0), which is irrelevant at x=6, y=-1.
        ok_leg2a = self.navigate_to(6.0, -1.0, 2.60, "Leg 2a: Diagonal South-West Escape", timeout_s=60.0)
        if not ok_leg2a:
            return False

        time.sleep(0.5)

        # Leg 2b: Continue West in south corridor (boulder S-edge at y=-0.15; y=-1.5 is clear)
        ok_leg2b = self.navigate_to(3.0, -1.5, 3.14159, "Leg 2b: West via South Corridor", timeout_s=60.0)
        if not ok_leg2b:
            return False

        time.sleep(0.5)

        # Leg 2c: Return to Origin Base Camp
        ok_leg2c = self.navigate_to(0.0, 0.0, 3.14159, "Leg 2c: Return to Base Camp Home", timeout_s=60.0)
        if not ok_leg2c:
            return False

        print("\n=======================================================")
        print(">>> ROUND-TRIP MISSION SUCCESS: ZERO COLLISIONS! <<<")
        print(f"Minimum Boulder Clearance Maintained: {self.min_boulder_clearance:.2f} m")
        print("=======================================================\n")
        return True

def main():
    rclpy.init()
    tester = TestNavABRoundTrip()
    success = tester.run()
    tester.destroy_node()
    rclpy.shutdown()
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())

