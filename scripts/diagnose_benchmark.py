#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
import numpy as np

def main():
    rclpy.init()
    node = Node('diag')
    scan_msg = None
    grid_msg = None

    def scb(msg): nonlocal scan_msg; scan_msg = msg
    def gcb(msg): nonlocal grid_msg; grid_msg = msg

    node.create_subscription(LaserScan, '/scan', scb, 10)
    node.create_subscription(OccupancyGrid, '/perception/traversability_grid', gcb, 10)

    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        if scan_msg is not None and grid_msg is not None:
            break

    print(f"Scan received: {scan_msg is not None}")
    if scan_msg:
        r = np.array(scan_msg.ranges)
        val = r[(r >= scan_msg.range_min) & (r <= scan_msg.range_max)]
        print(f"Laser total beams: {len(r)}, valid beams: {len(val)}, min range: {np.min(val) if len(val)>0 else 'None'}")
        
    print(f"Grid received: {grid_msg is not None}")
    if grid_msg:
        data = np.array(grid_msg.data, dtype=np.int8).reshape((grid_msg.info.height, grid_msg.info.width))
        unique, counts = np.unique(data, return_counts=True)
        print("Grid unique costs and counts:")
        for u, c in zip(unique, counts):
            print(f"  Cost {u}: {c} cells")

        # Find where obstacles (cost >= 70) appear
        obs_idx = np.where(data >= 70)
        if len(obs_idx[0]) > 0:
            print(f"Obstacle cells count: {len(obs_idx[0])}")
            for i in range(min(5, len(obs_idx[0]))):
                gy, gx = obs_idx[0][i], obs_idx[1][i]
                lx = grid_msg.info.origin.position.x + (gx + 0.5) * grid_msg.info.resolution
                ly = grid_msg.info.origin.position.y + (gy + 0.5) * grid_msg.info.resolution
                print(f"  Sample Obstacle: row gy={gy}, col gx={gx} -> lx={lx:.2f}m, ly={ly:.2f}m, cost={data[gy, gx]}")
        else:
            print("No cells with cost >= 70 in grid.")

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
