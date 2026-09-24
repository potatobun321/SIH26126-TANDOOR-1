import rclpy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2

rclpy.init()
node = rclpy.create_node("debug_slope")
bridge = CvBridge()

def cb(msg):
    depth = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
    print("Depth shape:", depth.shape, "dtype:", depth.dtype)
    print("Depth min:", np.nanmin(depth), "max:", np.nanmax(depth), "mean:", np.nanmean(depth))
    
    # Check model resolution
    input_w, input_h = 320, 240
    depth_small = cv2.resize(depth, (input_w, input_h), interpolation=cv2.INTER_NEAREST)
    valid = np.isfinite(depth_small) & (depth_small > 0.25) & (depth_small < 15.0)
    print("Valid depth ratio:", np.mean(valid))
    
    # Check ground region (v > 84)
    ground_valid = valid[84:, :]
    print("Ground valid depth ratio:", np.mean(ground_valid))
    
    rclpy.shutdown()

sub = node.create_subscription(Image, "/camera/depth/image_raw", cb, 10)
rclpy.spin(node)
