#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np

def main():
    rclpy.init()
    node = Node('laser_check')
    scan = None
    def cb(msg): nonlocal scan; scan = msg
    node.create_subscription(LaserScan, '/scan', cb, 10)
    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        if scan: break

    angles = scan.angle_min + np.arange(len(scan.ranges)) * scan.angle_increment
    for deg in [-38.2, -30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0]:
        rad = np.radians(deg)
        idx = int(np.argmin(np.abs(angles - rad)))
        print(f"Angle {deg:5.1f} deg (beam {idx:3d}): range = {scan.ranges[idx]:.3f} m")

    rclpy.shutdown()

if __name__ == '__main__':
    main()
