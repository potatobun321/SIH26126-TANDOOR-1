#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2, os, sys
import numpy as np

class FrameGrabber(Node):
    def __init__(self):
        super().__init__('grabber')
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.cb, 10)
        self.bridge = CvBridge()
        self.frame = None

    def cb(self, msg):
        self.frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

def main():
    rclpy.init()
    node = FrameGrabber()
    for _ in range(50):
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.frame is not None:
            out_path = '/mnt/c/Users/GIGA/Desktop/sih2026/data/sample_sim_frame.png'
            cv2.imwrite(out_path, node.frame)
            print(f'Successfully grabbed frame shape {node.frame.shape} -> {out_path}')
            break
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
