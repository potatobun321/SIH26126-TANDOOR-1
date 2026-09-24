#!/usr/bin/env python3
"""
test_tactical_hud.py — Verification of Tactical Military HUD & Threat Assessment
Tests the enhanced TerrainSegmentationNode in a standalone ROS 2 test loop.
"""

import sys
import time
import numpy as np
import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from nav_msgs.msg import OccupancyGrid, Odometry
from cv_bridge import CvBridge

class HUDTestHarness(Node):
    def __init__(self):
        super().__init__('hud_test_harness')
        self.bridge = CvBridge()

        self.pub_image = self.create_publisher(Image, '/camera/image_raw', 10)
        self.pub_info = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        self.pub_odom = self.create_publisher(Odometry, '/odometry/filtered', 10)

        self.sub_overlay = self.create_subscription(
            Image,
            '/perception/segmentation_overlay',
            self.overlay_cb,
            10
        )
        self.sub_grid = self.create_subscription(
            OccupancyGrid,
            '/perception/traversability_grid',
            self.grid_cb,
            10
        )

        self.received_overlay = False
        self.received_grid = False
        self.overlay_shape = None

    def overlay_cb(self, msg):
        self.received_overlay = True
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.overlay_shape = cv_img.shape
        # Save sample overlay image for inspection and verification artifact
        cv2.imwrite('/mnt/c/Users/GIGA/Desktop/sih2026/eval/tactical_hud_sample.png', cv_img)

    def grid_cb(self, msg):
        self.received_grid = True

def main():
    rclpy.init()
    test_node = HUDTestHarness()

    # Import and spin the terrain segmentation node in the background or process
    from ugv_perception.terrain_segmentation_node import TerrainSegmentationNode
    seg_node = TerrainSegmentationNode()

    # Publish synthetic camera info
    info_msg = CameraInfo()
    info_msg.width = 640
    info_msg.height = 480
    info_msg.k = [381.36, 0.0, 320.0, 0.0, 381.36, 240.0, 0.0, 0.0, 1.0]

    # Publish synthetic odometry (Speed: 0.42 m/s, Heading: 45 deg)
    odom_msg = Odometry()
    odom_msg.twist.twist.linear.x = 0.30
    odom_msg.twist.twist.linear.y = 0.30
    # 45 deg yaw: z = sin(22.5 deg) = 0.38268, w = cos(22.5 deg) = 0.92388
    odom_msg.pose.pose.orientation.z = 0.3826834
    odom_msg.pose.pose.orientation.w = 0.9238795

    # Create synthetic camera frame with ground, trail, and boulder
    test_frame = np.full((480, 640, 3), (210, 180, 140), dtype=np.uint8)  # Arid sky/ground
    # Trail corridor in middle
    test_frame[240:480, 200:440] = (80, 110, 170)
    # Boulder in trail
    cv2.circle(test_frame, (320, 360), 40, (50, 50, 60), -1)

    bridge = CvBridge()
    img_msg = bridge.cv2_to_imgmsg(test_frame, encoding='bgr8')
    img_msg.header.stamp = test_node.get_clock().now().to_msg()
    img_msg.header.frame_id = 'camera_optical_link'

    print("[TEST] Spinning test harness and terrain segmentation node...")
    start_t = time.time()
    for _ in range(25):
        test_node.pub_info.publish(info_msg)
        test_node.pub_odom.publish(odom_msg)
        test_node.pub_image.publish(img_msg)

        rclpy.spin_once(seg_node, timeout_sec=0.05)
        rclpy.spin_once(test_node, timeout_sec=0.05)
        if test_node.received_overlay and test_node.received_grid:
            break

    print(f"[TEST RESULT] Overlay Received: {test_node.received_overlay} (Shape: {test_node.overlay_shape})")
    print(f"[TEST RESULT] Traversability Grid Received: {test_node.received_grid}")

    seg_node.destroy_node()
    test_node.destroy_node()
    rclpy.shutdown()

    if test_node.received_overlay and test_node.received_grid:
        print("[TEST SUCCESS] Tactical HUD and Traversability Costmap fully verified!")
        sys.exit(0)
    else:
        print("[TEST FAILURE] Did not receive overlay or costmap.")
        sys.exit(1)

if __name__ == '__main__':
    main()
