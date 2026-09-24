#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid

class DiagnosticListener(Node):
    def __init__(self):
        super().__init__('diag_listener')
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.sub_costmap = self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self.costmap_cb, 10)
        self.scan_count = 0
        self.costmap_count = 0

    def scan_cb(self, msg):
        self.scan_count += 1
        valid = [r for r in msg.ranges if msg.range_min <= r <= msg.range_max]
        if self.scan_count % 10 == 1:
            print(f"[SCAN #{self.scan_count}] Valid: {len(valid)}/{len(msg.ranges)} | Min: {min(valid) if valid else None:.2f}m | Max: {max(valid) if valid else None:.2f}m")

    def costmap_cb(self, msg):
        self.costmap_count += 1
        lethal = sum(1 for c in msg.data if c >= 100)
        inflated = sum(1 for c in msg.data if 0 < c < 100)
        free = sum(1 for c in msg.data if c == 0)
        if self.costmap_count % 5 == 1:
            print(f"[COSTMAP #{self.costmap_count}] Lethal cells: {lethal} | Inflated cells: {inflated} | Free: {free}")

def main():
    rclpy.init()
    node = DiagnosticListener()
    print("Listening to /scan and /local_costmap/costmap...")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
