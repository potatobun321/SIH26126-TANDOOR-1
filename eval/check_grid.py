#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np

class CheckGrid(Node):
    def __init__(self):
        super().__init__('check_grid')
        self.sub = self.create_subscription(OccupancyGrid, '/perception/traversability_grid', self.cb, 10)
        self.received = False

    def cb(self, msg: OccupancyGrid):
        data = np.array(msg.data).reshape((msg.info.height, msg.info.width))
        print(f"Grid received: shape={data.shape}, min={data.min()}, max={data.max()}")
        unique, counts = np.unique(data, return_counts=True)
        for u, c in zip(unique, counts):
            print(f"  Value {u}: {c} cells")
        self.received = True

def main():
    rclpy.init()
    node = CheckGrid()
    start = node.get_clock().now()
    while rclpy.ok() and not node.received:
        rclpy.spin_once(node, timeout_sec=0.5)
        if (node.get_clock().now() - start).nanoseconds > 5e9:
            print("Timeout waiting for grid")
            break
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
