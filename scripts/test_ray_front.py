#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
import numpy as np

def main():
    rclpy.init()
    node = Node('ray_test')
    scan_msg = None
    grid_msg = None
    def scb(msg): nonlocal scan_msg; scan_msg = msg
    def gcb(msg): nonlocal grid_msg; grid_msg = msg
    node.create_subscription(LaserScan, '/scan', scb, 10)
    node.create_subscription(OccupancyGrid, '/perception/traversability_grid', gcb, 10)

    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        if scan_msg and grid_msg: break

    angles = scan_msg.angle_min + np.arange(len(scan_msg.ranges)) * scan_msg.angle_increment
    ranges = np.array(scan_msg.ranges)

    grid = grid_msg
    data = np.array(grid.data, dtype=np.int8).reshape((grid.info.height, grid.info.width))
    res = grid.info.resolution
    origin_x = grid.info.origin.position.x
    origin_y = grid.info.origin.position.y

    obs_gy, obs_gx = np.where(data >= 70)
    print(f'Total obstacle cells in grid: {len(obs_gy)}')

    # Group by angular azimuth bins of 1 degree
    ray_bins = {}
    for gy, gx in zip(obs_gy, obs_gx):
        lx = origin_x + (gx + 0.5) * res
        ly = origin_y + (gy + 0.5) * res
        dx = lx - 0.32
        dy = ly
        dist = np.hypot(dx, dy)
        deg_bin = int(round(np.degrees(np.arctan2(dy, dx))))
        if deg_bin not in ray_bins:
            ray_bins[deg_bin] = []
        ray_bins[deg_bin].append((dist, lx, ly))

    print(f'Distinct angular rays: {len(ray_bins)}')
    front_errors = []
    for deg_bin, pts in sorted(ray_bins.items()):
        front_dist = min(p[0] for p in pts)
        rad = np.radians(deg_bin)
        b_idx = int(np.argmin(np.abs(angles - rad)))
        laser_dist = ranges[b_idx]

        if scan_msg.range_min < laser_dist < scan_msg.range_max:
            err = abs(front_dist - laser_dist)
            front_errors.append((err, front_dist, laser_dist, deg_bin))
            print(f'Angle {deg_bin:+3d} deg: Front IPM={front_dist:.2f}m | Laser={laser_dist:.2f}m | Err={err*100.0:4.1f} cm')

    if front_errors:
        err_vals = [e[0] for e in front_errors]
        print('-'*60)
        print(f'Front Boundary MAE: {np.mean(err_vals):.3f}m ({np.mean(err_vals)*100.0:.1f} cm)')
        print(f'Median Error:       {np.median(err_vals):.3f}m ({np.median(err_vals)*100.0:.1f} cm)')

    rclpy.shutdown()

if __name__ == '__main__':
    main()
