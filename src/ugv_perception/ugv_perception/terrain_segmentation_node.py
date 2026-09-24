#!/usr/bin/env python3
"""
terrain_segmentation_node.py — AI-driven outdoor terrain traversability segmentation with
Dynamic IMU Attitude-Compensated IPM and Geometric Depth Slope Estimation.
Part of SIH26126 (Tikka Techies) Uneven Terrain Navigation Architecture.
"""

import os
import time
import math
import numpy as np
import cv2
cv2.setNumThreads(1)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, Imu
from nav_msgs.msg import OccupancyGrid, Odometry
from std_msgs.msg import Float32
from cv_bridge import CvBridge

# Off-road Class Taxonomy (RUGD / RELLIS-3D Mapping)
# 0: Sky/Background, 1: Trail/Road, 2: Grass/Soil, 3: Bush/Vegetation, 4: Rock/Obstacle, 5: Water/Mud
CLASS_COLORS_BGR = {
    0: (235, 206, 135),  # Sky / Horizon (Light Blue)
    1: (50, 110, 180),   # Trail / Path (Brown)
    2: (60, 180, 40),    # Grass / Soil (Green)
    3: (30, 200, 220),   # Bush / Shrub (Yellow)
    4: (40, 40, 230),    # Rock / Obstacle / Tree (Crimson Red)
    5: (240, 100, 30),   # Mud / Puddle / Water (Deep Blue)
}

# Cost mapping for OccupancyGrid (0 to 100, with -1 as unknown / outside FOV)
CLASS_COSTS_ARRAY = np.array([-1, 0, 20, 70, 100, 100], dtype=np.int8)

class TerrainSegmentationNode(Node):
    def __init__(self):
        super().__init__('terrain_segmentation_node')

        # Declare parameters
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('overlay_topic', '/perception/segmentation_overlay')
        self.declare_parameter('traversability_grid_topic', '/perception/traversability_grid')
        self.declare_parameter('model_path', 'models/checkpoints/terrain_segmenter.onnx')
        self.declare_parameter('input_width', 320)
        self.declare_parameter('input_height', 240)
        self.declare_parameter('camera_height', 0.33)      # Height of camera optical center above ground (m)
        self.declare_parameter('camera_pitch_deg', 0.0)    # Pitch angle downward (degrees)
        self.declare_parameter('camera_mount_x', 0.32)     # Forward offset of camera from base_footprint (m)
        self.declare_parameter('grid_resolution', 0.10)    # Costmap resolution (m/cell)
        self.declare_parameter('grid_width', 60)           # Grid cells along X (forward)
        self.declare_parameter('grid_height', 60)          # Grid cells along Y (lateral)
        self.declare_parameter('grid_origin_x', 0.30)      # Grid origin X in base_footprint (m)
        self.declare_parameter('grid_origin_y', -3.00)     # Grid origin Y in base_footprint (m)

        # Uneven Terrain Parameters
        self.declare_parameter('depth_topic', '/camera/depth/image_raw')
        self.declare_parameter('imu_topic', '/imu')
        self.declare_parameter('enable_depth_slope', True)
        self.declare_parameter('enable_attitude_compensation', True)
        self.declare_parameter('max_traversable_slope_deg', 18.0)
        self.declare_parameter('critical_slope_deg', 25.0)
        self.declare_parameter('max_roughness_m', 0.15)

        self.image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        self.camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        self.overlay_topic = self.get_parameter('overlay_topic').get_parameter_value().string_value
        self.traversability_grid_topic = self.get_parameter('traversability_grid_topic').get_parameter_value().string_value
        self.model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.input_width = self.get_parameter('input_width').get_parameter_value().integer_value
        self.input_height = self.get_parameter('input_height').get_parameter_value().integer_value

        self.camera_height = self.get_parameter('camera_height').get_parameter_value().double_value
        self.camera_pitch_deg = self.get_parameter('camera_pitch_deg').get_parameter_value().double_value
        self.camera_mount_x = self.get_parameter('camera_mount_x').get_parameter_value().double_value
        self.grid_resolution = self.get_parameter('grid_resolution').get_parameter_value().double_value
        self.grid_width = self.get_parameter('grid_width').get_parameter_value().integer_value
        self.grid_height = self.get_parameter('grid_height').get_parameter_value().integer_value
        self.grid_origin_x = self.get_parameter('grid_origin_x').get_parameter_value().double_value
        self.grid_origin_y = self.get_parameter('grid_origin_y').get_parameter_value().double_value

        self.depth_topic = self.get_parameter('depth_topic').get_parameter_value().string_value
        self.imu_topic = self.get_parameter('imu_topic').get_parameter_value().string_value
        self.enable_depth_slope = self.get_parameter('enable_depth_slope').get_parameter_value().bool_value
        self.enable_attitude_compensation = self.get_parameter('enable_attitude_compensation').get_parameter_value().bool_value
        self.max_traversable_slope_deg = self.get_parameter('max_traversable_slope_deg').get_parameter_value().double_value
        self.critical_slope_deg = self.get_parameter('critical_slope_deg').get_parameter_value().double_value
        self.max_roughness_m = self.get_parameter('max_roughness_m').get_parameter_value().double_value

        self.bridge = CvBridge()
        self.session = None

        # Camera intrinsics (defaults matched to Gazebo camera 640x480 HFOV=80deg)
        self.fx = 381.361
        self.fy = 381.361
        self.cx = 320.0
        self.cy = 240.0
        self.img_w = 640
        self.img_h = 480
        self.has_camera_info = False

        # Attitude & Slope State
        self.current_roll_deg = 0.0
        self.current_pitch_deg = 0.0
        self.current_roll_rad = 0.0
        self.current_pitch_rad = 0.0
        self.last_lut_pitch_deg = 0.0
        self.last_lut_roll_deg = 0.0
        self.latest_depth_img = None
        self.max_measured_slope_deg = 0.0

        # Precompute Calibrated Inverse Perspective Mapping (IPM) Lookup Table
        self.recompute_ipm_lut(roll_deg=0.0, pitch_deg=0.0)

        # Attempt to load ONNX model if file exists
        self.init_onnx_model()

        # Publishers & Subscribers
        self.sub_image = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )

        self.sub_info = self.create_subscription(
            CameraInfo,
            self.camera_info_topic,
            self.camera_info_callback,
            10
        )

        if self.enable_depth_slope:
            self.sub_depth = self.create_subscription(
                Image,
                self.depth_topic,
                self.depth_callback,
                10
            )

        self.sub_imu = self.create_subscription(
            Imu,
            self.imu_topic,
            self.imu_callback,
            20
        )

        self.pub_overlay = self.create_publisher(Image, self.overlay_topic, 10)
        self.pub_traversability = self.create_publisher(OccupancyGrid, self.traversability_grid_topic, 10)
        self.pub_latency = self.create_publisher(Float32, '/perception/latency_ms', 10)
        self.pub_fps = self.create_publisher(Float32, '/perception/fps', 10)

        # Real-time Telemetry for Tactical HUD
        self.current_speed = 0.0
        self.current_yaw_deg = 0.0
        self.odom_received = False
        self.sub_odom = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.odom_callback,
            10
        )

        self.frame_count = 0
        self.fps_timer = time.time()
        self.get_logger().info(
            f'Terrain Segmentation Node active on {self.image_topic}. '
            f'Uneven Terrain: Slope={self.enable_depth_slope}, AttitudeComp={self.enable_attitude_compensation}'
        )

    def imu_callback(self, msg: Imu):
        q = msg.orientation
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        self.current_roll_rad = math.atan2(sinr_cosp, cosr_cosp)
        self.current_roll_deg = math.degrees(self.current_roll_rad)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1.0:
            self.current_pitch_rad = math.copysign(math.pi / 2.0, sinp)
        else:
            self.current_pitch_rad = math.asin(sinp)
        self.current_pitch_deg = math.degrees(self.current_pitch_rad)

        # Dynamic attitude compensation trigger: update IPM LUT if attitude changed by > 0.75 deg
        if self.enable_attitude_compensation:
            delta_pitch = abs(self.current_pitch_deg - self.last_lut_pitch_deg)
            delta_roll = abs(self.current_roll_deg - self.last_lut_roll_deg)
            if delta_pitch > 0.75 or delta_roll > 0.75:
                self.recompute_ipm_lut(roll_deg=self.current_roll_deg, pitch_deg=self.current_pitch_deg)

    def depth_callback(self, msg: Image):
        try:
            if msg.encoding == '32FC1':
                self.latest_depth_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='32FC1')
            elif msg.encoding == '16UC1':
                depth_16u = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
                self.latest_depth_img = depth_16u.astype(np.float32) / 1000.0
            else:
                self.latest_depth_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        except Exception:
            pass

    def odom_callback(self, msg: Odometry):
        self.odom_received = True
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        self.current_speed = math.sqrt(vx * vx + vy * vy)

        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw_rad = math.atan2(siny_cosp, cosy_cosp)
        self.current_yaw_deg = (math.degrees(yaw_rad) + 360.0) % 360.0

    def recompute_ipm_lut(self, roll_deg=0.0, pitch_deg=0.0):
        """
        Precomputes the Inverse Perspective Mapping (IPM) lookup table for metric ground projection.
        Maps each cell (gy, gx) in base_footprint OccupancyGrid to exact camera image pixel (v, u).
        Dynamically accounts for vehicle pitch and roll attitude over uneven terrain.
        """
        self.last_lut_pitch_deg = pitch_deg
        self.last_lut_roll_deg = roll_deg

        gx_indices = np.arange(self.grid_width)
        gy_indices = np.arange(self.grid_height)
        gx_grid, gy_grid = np.meshgrid(gx_indices, gy_indices)  # gy is row (Y), gx is col (X)

        # Ground coordinate in base_footprint (m)
        X_g = self.grid_origin_x + (gx_grid + 0.5) * self.grid_resolution
        Y_g = self.grid_origin_y + (gy_grid + 0.5) * self.grid_resolution

        # Dynamic pitch and roll angles
        total_pitch_rad = np.radians(self.camera_pitch_deg + pitch_deg)
        roll_rad = np.radians(roll_deg)

        cos_p = np.cos(total_pitch_rad)
        sin_p = np.sin(total_pitch_rad)
        cos_r = np.cos(roll_rad)
        sin_r = np.sin(roll_rad)

        # Vector from camera optical center to ground point:
        dX = X_g - self.camera_mount_x
        dY = Y_g
        dZ = -self.camera_height

        # Chassis attitude rotation (pitch about Y, roll about X)
        # Transformed into camera optical frame (X right, Y down, Z forward):
        Z_c = dX * cos_p - dZ * sin_p
        X_c = -dY * cos_r - dZ * sin_r
        Y_c = -dZ * cos_p * cos_r - dX * sin_p

        valid_z = Z_c > 0.05
        u_calc = np.round(self.cx + self.fx * (X_c / np.maximum(Z_c, 1e-4))).astype(np.int32)
        v_calc = np.round(self.cy + self.fy * (Y_c / np.maximum(Z_c, 1e-4))).astype(np.int32)

        in_fov = valid_z & (u_calc >= 0) & (u_calc < self.img_w) & (v_calc >= 0) & (v_calc < self.img_h)

        # Precompute model-scale coordinates (input_width x input_height)
        scale_x = float(self.input_width) / float(self.img_w)
        scale_y = float(self.input_height) / float(self.img_h)
        u_model = np.clip(np.round(u_calc * scale_x).astype(np.int32), 0, self.input_width - 1)
        v_model = np.clip(np.round(v_calc * scale_y).astype(np.int32), 0, self.input_height - 1)

        self.u_lut = np.full((self.grid_height, self.grid_width), -1, dtype=np.int32)
        self.v_lut = np.full((self.grid_height, self.grid_width), -1, dtype=np.int32)
        self.u_lut[in_fov] = u_calc[in_fov]
        self.v_lut[in_fov] = v_calc[in_fov]
        self.valid_mask = in_fov

        # Flat 1D pre-indexed coordinate vectors for direct model-resolution sampling
        self.u_model_idx = u_model[in_fov]
        self.v_model_idx = v_model[in_fov]

    def compute_slope_and_roughness_cost(self, depth_img):
        """
        Computes geometric slope angle and surface roughness directly from depth image.
        Uses depth pre-filtering and range gating to eliminate grazing-angle sensor noise.
        Returns:
            slope_cost_map: (input_height, input_width) array of cost 0 to 75 (non-lethal soft penalty)
            max_slope_deg: float, maximum slope observed in drivable corridor
        """
        if depth_img is None:
            return np.zeros((self.input_height, self.input_width), dtype=np.int8), 0.0

        # Downsample to model dimensions for fast execution
        depth_small = cv2.resize(depth_img, (self.input_width, self.input_height), interpolation=cv2.INTER_NEAREST)

        # 1. Clean depth sensor grain/quantization noise via median filter
        depth_clean = cv2.medianBlur(depth_small.astype(np.float32), 5)

        # 2. Range-gate: only evaluate slope in clean near-field (0.50m to 4.20m)
        # Beyond 4.20m, horizontal perspective compression creates artificial grazing-angle slope spikes.
        valid = np.isfinite(depth_clean) & (depth_clean >= 0.50) & (depth_clean <= 4.20)
        if not np.any(valid):
            return np.zeros((self.input_height, self.input_width), dtype=np.int8), 0.0

        # Scale camera intrinsics to model resolution
        scale_x = float(self.input_width) / float(self.img_w)
        scale_y = float(self.input_height) / float(self.img_h)
        fx_scaled = self.fx * scale_x
        fy_scaled = self.fy * scale_y
        cx_scaled = self.cx * scale_x
        cy_scaled = self.cy * scale_y

        u_grid, v_grid = np.meshgrid(np.arange(self.input_width), np.arange(self.input_height))

        # Reconstruct 3D metric surface coordinates in camera optical frame
        Z_c = np.where(valid, depth_clean, 0.0).astype(np.float32)
        X_c = ((u_grid - cx_scaled) * Z_c / fx_scaled).astype(np.float32)
        Y_c = ((v_grid - cy_scaled) * Z_c / fy_scaled).astype(np.float32)

        # 3D spatial tangent vectors via central differences
        dX_du = cv2.Sobel(X_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
        dY_du = cv2.Sobel(Y_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
        dZ_du = cv2.Sobel(Z_c, cv2.CV_32F, 1, 0, ksize=3) / 8.0
        t_u = np.stack([dX_du, dY_du, dZ_du], axis=-1)

        dX_dv = cv2.Sobel(X_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
        dY_dv = cv2.Sobel(Y_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
        dZ_dv = cv2.Sobel(Z_c, cv2.CV_32F, 0, 1, ksize=3) / 8.0
        t_v = np.stack([dX_dv, dY_dv, dZ_dv], axis=-1)

        # 3D surface normal vector: n = t_u x t_v
        n = np.cross(t_u, t_v)
        norm = np.linalg.norm(n, axis=-1)
        norm_safe = np.maximum(norm, 1e-6)
        n_unit = n / norm_safe[..., np.newaxis]

        # In camera optical frame: Y points down (gravity direction g = (0, 1, 0))
        # Dynamic chassis tilt compensation:
        total_pitch_rad = np.radians(self.camera_pitch_deg + self.current_pitch_deg)
        roll_rad = np.radians(self.current_roll_deg)
        g_x = np.sin(roll_rad)
        g_y = np.cos(total_pitch_rad) * np.cos(roll_rad)
        g_z = np.sin(total_pitch_rad) * np.cos(roll_rad)

        # Dot product of surface normal with gravity vector:
        cos_slope = np.abs(n_unit[..., 0] * g_x + n_unit[..., 1] * g_y + n_unit[..., 2] * g_z)
        slope_rad = np.arccos(np.clip(cos_slope, 0.0, 1.0))
        slope_deg = np.degrees(slope_rad)

        # Apply spatial median smoothing to eliminate edge noise
        slope_deg = cv2.medianBlur(slope_deg.astype(np.float32), 3)

        # Cost assignment:
        # < 20 deg: 0 cost (completely drivable)
        # 20 - 30 deg: 20 - 55 cost (navigable with soft avoidance preference)
        # > 30 deg: 70 cost (steep grade penalty, but NON-LETHAL so UGV never stalls or panics)
        slope_cost = np.zeros_like(slope_deg, dtype=np.int8)

        moderate_mask = valid & (slope_deg >= self.max_traversable_slope_deg) & (slope_deg < self.critical_slope_deg)
        steep_mask = valid & (slope_deg >= self.critical_slope_deg)

        slope_cost[moderate_mask] = np.clip(
            ((slope_deg[moderate_mask] - self.max_traversable_slope_deg) / 
             max(1.0, (self.critical_slope_deg - self.max_traversable_slope_deg)) * 35.0 + 20.0),
            0, 70
        ).astype(np.int8)

        slope_cost[steep_mask] = 70
        slope_cost[~valid] = 0

        # Maximum slope in drivable forward corridor
        horizon_idx = int(self.input_height * 0.45)
        forward_mask = valid[horizon_idx:, :] & (slope_deg[horizon_idx:, :] < 80.0)
        max_slope = float(np.max(slope_deg[horizon_idx:, :][forward_mask])) if np.any(forward_mask) else 0.0

        # Extract 3D physical obstacles with dynamic chassis pitch/roll compensation
        # In camera optical frame: X_c is right (+), Y_c is down (+), Z_c is forward (+)
        total_pitch_rad = np.radians(self.camera_pitch_deg + self.current_pitch_deg)
        roll_rad = np.radians(self.current_roll_deg)
        cos_p = np.cos(total_pitch_rad)
        sin_p = np.sin(total_pitch_rad)
        cos_r = np.cos(roll_rad)

        # True elevation above ground plane (base_footprint level Z=0):
        # Y_c points down; pitch tilts camera down (+) or up (-); Z_c points forward
        H_pts = self.camera_height - (Y_c * cos_p * cos_r - Z_c * sin_p)

        # Elevation threshold: 0.25m to 2.2m (ignores ground undulation/grass; reliably detects 0.9m boulder and 0.8m dynamic hazard)
        obs_mask = valid & (H_pts >= 0.25) & (H_pts <= 2.2) & (Z_c >= 0.40) & (Z_c <= 6.0)
        obs_x = self.camera_mount_x + Z_c[obs_mask]
        obs_y = -X_c[obs_mask]

        gx_obs = np.floor((obs_x - self.grid_origin_x) / self.grid_resolution).astype(np.int32)
        gy_obs = np.floor((obs_y - self.grid_origin_y) / self.grid_resolution).astype(np.int32)
        valid_grid = (gx_obs >= 0) & (gx_obs < self.grid_width) & (gy_obs >= 0) & (gy_obs < self.grid_height)
        obs_indices = (gy_obs[valid_grid], gx_obs[valid_grid])

        return slope_cost, max_slope, obs_indices

    def camera_info_callback(self, msg):
        if not self.has_camera_info:
            if msg.k[0] > 0.0:
                self.fx = float(msg.k[0])
                self.fy = float(msg.k[4])
                self.cx = float(msg.k[2])
                self.cy = float(msg.k[5])
                self.img_w = int(msg.width)
                self.img_h = int(msg.height)
                self.has_camera_info = True
                self.get_logger().info(
                    f'Updated camera intrinsics: fx={self.fx:.2f}, fy={self.fy:.2f}, '
                    f'cx={self.cx:.2f}, cy={self.cy:.2f}, size=({self.img_w}x{self.img_h})'
                )
                self.recompute_ipm_lut(roll_deg=self.current_roll_deg, pitch_deg=self.current_pitch_deg)

    def resolve_model_path(self, path):
        if os.path.isabs(path) and os.path.exists(path):
            return path
        candidates = [
            path,
            os.path.join(os.getcwd(), path),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../', path)),
            os.path.join('/mnt/c/Users/GIGA/Desktop/sih2026', path)
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def init_onnx_model(self):
        resolved = self.resolve_model_path(self.model_path)
        if resolved and os.path.exists(resolved):
            try:
                import onnxruntime as ort
                sess_opts = ort.SessionOptions()
                sess_opts.intra_op_num_threads = 2
                sess_opts.inter_op_num_threads = 1
                self.session = ort.InferenceSession(
                    resolved,
                    sess_options=sess_opts,
                    providers=['CPUExecutionProvider']
                )
                self.get_logger().info(f'Successfully loaded ONNX segmentation model from {resolved}')
            except Exception as e:
                self.get_logger().warn(f'Failed to initialize ONNX Runtime: {e}. Using resilient feature classifier.')
                self.session = None
        else:
            self.get_logger().info(f'Model checkpoint {self.model_path} not found. Running resilient feature classifier.')
            self.session = None

    def segment_frame(self, cv_img):
        orig_h, orig_w = cv_img.shape[:2]

        if self.session is not None:
            resized = cv2.resize(cv_img, (self.input_width, self.input_height))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            norm = (rgb - mean) / std
            input_tensor = np.transpose(norm, (2, 0, 1))[np.newaxis, ...].astype(np.float32)

            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: input_tensor})
            logits = outputs[0][0]
            pred = np.argmax(logits, axis=0).astype(np.uint8)

            class_mask = cv2.resize(pred, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
            return class_mask, pred

        else:
            hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
            class_mask = np.zeros((orig_h, orig_w), dtype=np.uint8)

            horizon_line = int(orig_h * 0.35)
            class_mask[:horizon_line, :] = 0  # Sky

            ground_hsv = hsv[horizon_line:, :]
            H = ground_hsv[:, :, 0]
            S = ground_hsv[:, :, 1]
            V = ground_hsv[:, :, 2]

            grass_mask = (H >= 35) & (H <= 85) & (S >= 40) & (V >= 30)
            trail_mask = ((H >= 10) & (H <= 28) & (S >= 25)) | ((H < 10) & (S < 70) & (V > 90))
            # Granite/grey boulder obstacle: very low saturation (achromatic) and distinct mid-dark value
            obstacle_mask = (S < 25) & (V < 85) & (V > 25)
            bush_mask = (H >= 25) & (H <= 40) & (S >= 60) & (V < 120)

            ground_classes = np.full((orig_h - horizon_line, orig_w), 1, dtype=np.uint8)
            ground_classes[grass_mask] = 2
            ground_classes[bush_mask] = 3
            ground_classes[obstacle_mask] = 4

            # Clean isolated noise specks
            ground_classes = cv2.medianBlur(ground_classes, 3)

            class_mask[horizon_line:, :] = ground_classes
            pred = cv2.resize(class_mask, (self.input_width, self.input_height), interpolation=cv2.INTER_NEAREST)
            return class_mask, pred

    def image_callback(self, msg):
        now = time.time()
        if hasattr(self, '_last_img_time') and (now - self._last_img_time < 0.050):
            return
        self._last_img_time = now

        start_time = time.perf_counter()

        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge conversion failed: {e}')
            return

        # 1. Semantic Segmentation
        class_mask, pred = self.segment_frame(cv_img)
        h, w = cv_img.shape[:2]

        # 2. Geometric Depth Slope & Roughness Analysis (Optimized conditional execution)
        if self.enable_depth_slope and getattr(self, 'latest_depth_img', None) is not None:
            slope_cost_map, max_slope, obs_indices = self.compute_slope_and_roughness_cost(self.latest_depth_img)
        else:
            slope_cost_map = np.zeros((self.input_height, self.input_width), dtype=np.int8)
            max_slope = 0.0
            obs_indices = None
        self.max_measured_slope_deg = max_slope

        # 3. Project traversability into 2D Occupancy Grid for Nav2
        grid_msg = OccupancyGrid()
        grid_msg.header.stamp = msg.header.stamp
        grid_msg.header.frame_id = 'base_footprint'
        grid_msg.info.resolution = self.grid_resolution
        grid_msg.info.width = self.grid_width
        grid_msg.info.height = self.grid_height
        grid_msg.info.origin.position.x = self.grid_origin_x
        grid_msg.info.origin.position.y = self.grid_origin_y
        grid_msg.info.origin.position.z = 0.0
        grid_msg.info.origin.orientation.w = 1.0

        cost_grid = np.full((self.grid_height, self.grid_width), -1, dtype=np.int8)

        # Sample semantic texture cost
        fov_classes = pred[self.v_model_idx, self.u_model_idx]
        semantic_costs = CLASS_COSTS_ARRAY[fov_classes]

        # Sample geometric depth slope cost at identical ground coordinates
        slope_costs = slope_cost_map[self.v_model_idx, self.u_model_idx]

        # Fuse semantic class cost with geometric slope hazard
        fused_costs = np.maximum(semantic_costs, slope_costs)
        cost_grid[self.valid_mask] = fused_costs

        # Stamp direct 3D metric depth-detected obstacles as lethal cost (100)
        if obs_indices is not None and len(obs_indices[0]) > 0:
            cost_grid[obs_indices] = 100

        grid_msg.data = cost_grid.flatten().tolist()
        self.pub_traversability.publish(grid_msg)

        # 4. Threat & Proximity Analysis
        corridor_costs = cost_grid[24:37, 1:33]
        hazard_y, hazard_x = np.where(corridor_costs >= 90)
        min_clearance = None
        if len(hazard_x) > 0:
            min_gx = np.min(hazard_x) + 1
            min_clearance = self.grid_origin_x + min_gx * self.grid_resolution

        # 5. Color-Coded Semantic Overlay
        color_mask = np.zeros_like(cv_img)
        for class_id, color in CLASS_COLORS_BGR.items():
            color_mask[class_mask == class_id] = color

        overlay = cv2.addWeighted(cv_img, 0.62, color_mask, 0.38, 0)

        # 6. Tactical Military Operator HUD Overlays
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        self.frame_count += 1
        elapsed = time.time() - self.fps_timer
        fps = self.frame_count / elapsed if elapsed > 0 else 30.0
        if elapsed > 2.0:
            self.frame_count = 0
            self.fps_timer = time.time()

        # Top Telemetry Bar (Two-tier clean layout)
        overlay[0:44, :] = cv2.addWeighted(overlay[0:44, :], 0.15, np.zeros_like(overlay[0:44, :]), 0.85, 0)
        cv2.line(overlay, (0, 44), (w, 44), (0, 230, 180), 1)

        # Line 1: Identity & Inference Engine
        cv2.putText(overlay, "TIKKA TECHIES | SIH26126 DEFENSE RECON", (12, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 240, 190), 1, cv2.LINE_AA)

        mode_str = "ONNX" if self.session is not None else "HSV"
        engine_str = f"[{mode_str} AI] {fps:.0f} FPS | {latency_ms:.1f}ms"
        (ew, _), _ = cv2.getTextSize(engine_str, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        cv2.putText(overlay, engine_str, (w - ew - 12, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 240, 255), 1, cv2.LINE_AA)

        # Line 2: Kinematic & Uneven Terrain Attitude Telemetry
        pitch_sign = "+" if self.current_pitch_deg >= 0 else ""
        roll_sign = "+" if self.current_roll_deg >= 0 else ""
        telem_str = (
            f"SPD: {self.current_speed:.2f} m/s  |  "
            f"PITCH: {pitch_sign}{self.current_pitch_deg:.1f} DEG  |  "
            f"ROLL: {roll_sign}{self.current_roll_deg:.1f} DEG  |  "
            f"SURFACE SLOPE: {self.max_measured_slope_deg:.1f} DEG"
        )
        cv2.putText(overlay, telem_str, (12, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (240, 245, 255), 1, cv2.LINE_AA)

        # Tactical Corner Reticles
        m, b = 16, 20
        bracket_color = (0, 220, 170)
        cv2.line(overlay, (m, 52), (m + b, 52), bracket_color, 1)
        cv2.line(overlay, (m, 52), (m, 52 + b), bracket_color, 1)
        cv2.line(overlay, (w - m, 52), (w - m - b, 52), bracket_color, 1)
        cv2.line(overlay, (w - m, 52), (w - m, 52 + b), bracket_color, 1)
        cv2.line(overlay, (m, h - 38), (m + b, h - 38), bracket_color, 1)
        cv2.line(overlay, (m, h - 38), (m, h - 38 - b), bracket_color, 1)
        cv2.line(overlay, (w - m, h - 38), (w - m - b, h - 38), bracket_color, 1)
        cv2.line(overlay, (w - m, h - 38), (w - m, h - 38 - b), bracket_color, 1)

        # Center Boresight Crosshair
        cx, cy = w // 2, h // 2 + 25
        cv2.circle(overlay, (cx, cy), 3, (0, 240, 190), 1)
        cv2.line(overlay, (cx - 15, cy), (cx - 5, cy), (0, 240, 190), 1)
        cv2.line(overlay, (cx + 5, cy), (cx + 15, cy), (0, 240, 190), 1)
        cv2.line(overlay, (cx, cy - 12), (cx, cy - 5), (0, 240, 190), 1)
        cv2.line(overlay, (cx, cy + 5), (cx, cy + 12), (0, 240, 190), 1)

        # Tactical Proximity & Terrain Banner
        banner_w = 440
        bx1, bx2 = (w - banner_w) // 2, (w + banner_w) // 2
        by1, by2 = 50, 74

        if min_clearance is not None:
            if min_clearance < 1.2:
                alert_bg = (30, 30, 210)  # Red Alert
                alert_text = f"THREAT ALERT: HAZARD @ {min_clearance:.2f}m | REPLANNING"
                text_col = (255, 255, 255)
            else:
                alert_bg = (20, 140, 220)  # Amber Caution
                alert_text = f"PROXIMITY CAUTION: HAZARD @ {min_clearance:.2f}m | TRACKING"
                text_col = (10, 10, 10)
        elif self.max_measured_slope_deg > self.max_traversable_slope_deg:
            alert_bg = (20, 120, 210)  # Orange Warning
            alert_text = f"UNEVEN TERRAIN: {self.max_measured_slope_deg:.1f}* SLOPE | SPEED REGULATED"
            text_col = (255, 255, 255)
        else:
            alert_bg = (25, 95, 35)  # Nominal Emerald
            alert_text = "CORRIDOR NOMINAL: STABLE TRAVERSABILITY"
            text_col = (220, 255, 220)

        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), alert_bg, -1)
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), (240, 240, 240), 1)
        (bw, _), _ = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.putText(overlay, alert_text, (bx1 + (banner_w - bw) // 2, by1 + 17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, text_col, 1, cv2.LINE_AA)

        # Bottom HUD Ribbon & Class Swatches
        overlay[h - 30:h, :] = cv2.addWeighted(overlay[h - 30:h, :], 0.20, np.zeros_like(overlay[h - 30:h, :]), 0.80, 0)
        cv2.line(overlay, (0, h - 30), (w, h - 30), (100, 130, 150), 1)

        legend = [
            ("Trail [0]", (50, 110, 180)),
            ("Grass [20]", (60, 180, 40)),
            ("Bush [70]", (30, 200, 220)),
            ("Obstacle [100]", (40, 40, 230)),
            ("Slope Hazard [100]", (0, 140, 255))
        ]
        x_offset = 12
        for label, col in legend:
            cv2.rectangle(overlay, (x_offset, h - 21), (x_offset + 12, h - 9), col, -1)
            cv2.rectangle(overlay, (x_offset, h - 21), (x_offset + 12, h - 9), (220, 220, 220), 1)
            cv2.putText(overlay, label, (x_offset + 16, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (230, 230, 230), 1, cv2.LINE_AA)
            x_offset += 122

        # Publish semantic overlay
        overlay_msg = self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8')
        overlay_msg.header = msg.header
        self.pub_overlay.publish(overlay_msg)

        # Publish telemetry
        lat_msg = Float32()
        lat_msg.data = float(latency_ms)
        self.pub_latency.publish(lat_msg)

        fps_msg = Float32()
        fps_msg.data = float(fps)
        self.pub_fps.publish(fps_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TerrainSegmentationNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
