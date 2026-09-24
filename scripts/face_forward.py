#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math, time

class FaceForward(Node):
    def __init__(self):
        super().__init__('face_forward')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.current_yaw = None

    def odom_cb(self, msg):
        q = msg.pose.pose.orientation
        # Compute yaw from quaternion
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

def main():
    rclpy.init()
    node = FaceForward()
    print("Aligning UGV heading to 0.0 rad (facing forward towards obstacle field)...")

    # Wait for first odom
    for _ in range(50):
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.current_yaw is not None:
            break

    target_yaw = 0.0
    rate_sleep = 0.05
    for _ in range(200):
        rclpy.spin_once(node, timeout_sec=0.05)
        if node.current_yaw is None:
            continue

        err = target_yaw - node.current_yaw
        # Normalize error to [-pi, pi]
        while err > math.pi: err -= 2 * math.pi
        while err < -math.pi: err += 2 * math.pi

        if abs(err) < 0.03:
            print(f"Aligned! Final yaw = {math.degrees(node.current_yaw):.2f} deg")
            # Stop
            stop_msg = Twist()
            node.pub.publish(stop_msg)
            break

        cmd = Twist()
        cmd.angular.z = max(-0.6, min(0.6, 1.2 * err))
        node.pub.publish(cmd)
        time.sleep(rate_sleep)

    # Final stop command
    for _ in range(5):
        node.pub.publish(Twist())
        time.sleep(0.05)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
