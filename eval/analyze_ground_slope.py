import rclpy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2

rclpy.init()
node = rclpy.create_node("test_correct_slope")
bridge = CvBridge()

def cb(msg):
    depth = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
    input_w, input_h = 320, 240
    depth_small = cv2.resize(depth, (input_w, input_h), interpolation=cv2.INTER_NEAREST)
    valid = np.isfinite(depth_small) & (depth_small > 0.25) & (depth_small < 15.0)

    # Scale camera intrinsics
    scale_x = float(input_w) / 640.0
    scale_y = float(input_h) / 480.0
    fx = 381.361 * scale_x
    fy = 381.361 * scale_y
    cx = 320.0 * scale_x
    cy = 240.0 * scale_y

    u_grid, v_grid = np.meshgrid(np.arange(input_w), np.arange(input_h))
    
    # 3D coordinates in optical frame
    Z_c = np.where(valid, depth_small, 0.0).astype(np.float32)
    X_c = ((u_grid - cx) * Z_c / fx).astype(np.float32)
    Y_c = ((v_grid - cy) * Z_c / fy).astype(np.float32)

    # 3D spatial tangent vectors via central differences
    # Vector along u (horizontal tangent): dP/du = (dX/du, dY/du, dZ/du)
    dX_du = cv2.Sobel(X_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    dY_du = cv2.Sobel(Y_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    dZ_du = cv2.Sobel(Z_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    t_u = np.stack([dX_du, dY_du, dZ_du], axis=-1)

    # Vector along v (vertical tangent): dP/dv = (dX/dv, dY/dv, dZ/dv)
    dX_dv = cv2.Sobel(X_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    dY_dv = cv2.Sobel(Y_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    dZ_dv = cv2.Sobel(Z_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    t_v = np.stack([dX_dv, dY_dv, dZ_dv], axis=-1)

    # Surface normal: n = t_u x t_v
    n = np.cross(t_u, t_v)
    norm = np.linalg.norm(n, axis=-1)
    norm_safe = np.maximum(norm, 1e-6)
    
    # Unit normal
    n_unit = n / norm_safe[..., np.newaxis]

    # In optical frame, gravity points DOWN: g = (0, 1, 0)
    # Ground normal points UP: (0, -1, 0)
    # Slope inclination angle relative to horizontal plane:
    # cos(slope) = |n_y|
    cos_slope = np.abs(n_unit[..., 1])
    slope_rad = np.arccos(np.clip(cos_slope, 0.0, 1.0))
    slope_deg = np.degrees(slope_rad)

    # Mask out non-valid depth regions
    slope_deg[~valid] = 0.0

    print("--- CORRECT 3D SURFACE NORMAL SLOPE ---")
    print("Row 150 (Ground 2.0m ahead): slope =", slope_deg[150, 160], "deg")
    print("Row 180 (Ground 1.0m ahead): slope =", slope_deg[180, 160], "deg")
    print("Row 220 (Ground 0.6m ahead): slope =", slope_deg[220, 160], "deg")
    print("Mean slope on ground plane (v in 140..220):", np.mean(slope_deg[140:220, 80:240]), "deg")

    rclpy.shutdown()

sub = node.create_subscription(Image, "/camera/depth/image_raw", cb, 10)
rclpy.spin(node)
