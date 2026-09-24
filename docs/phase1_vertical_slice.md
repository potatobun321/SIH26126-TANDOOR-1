# Phase 1 Vertical Slice Guide

## 1. Objective
Establish the simplest working end-to-end autonomous navigation pipeline in Gazebo simulation before adding complex visual perception models or visual SLAM.

> **Exit Criterion:** The UGV spawns in an outdoor Gazebo world, receives an autonomous navigation goal, plans a path around a static obstacle, and reaches Point B without manual intervention.

---

## 2. Directory & File Reference

```text
sim/
├── models/ugv/ugv.urdf         # 4-wheel UGV with camera, IMU, and DiffDrive plugins
└── worlds/outdoor_terrain.sdf  # Ground plane, sunlight, and 3 outdoor obstacles

src/
├── ugv_description/            # URDF packaging & robot state publisher
├── ugv_bringup/
│   ├── config/ros_gz_bridge.yaml
│   ├── launch/sim_bringup.launch.py
│   └── launch/outdoor_vertical_slice.launch.py  # Master launch file
├── ugv_localization/
│   ├── config/ekf.yaml
│   └── launch/localization.launch.py
└── ugv_nav2/
    ├── config/nav2_params.yaml
    └── launch/navigation.launch.py
```

---

## 3. Step-by-Step Execution

### Step 1: Compile the ROS 2 Workspace
Inside Ubuntu WSL2:
```bash
cd /mnt/c/Users/GIGA/Desktop/sih2026
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Step 2: Launch the Complete Stack
Run the convenience launch script (supports `--headless` or GUI mode):
```bash
# In Windows PowerShell:
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/run_sim.sh

# Or headless (low CPU/GPU footprint):
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/run_sim.sh --headless
```
This automatically launches:
1. Gazebo Harmonic with `outdoor_terrain.sdf`
2. Spawns `outdoor_ugv` at coordinates $(0.0, 0.0, 0.3)$
3. Starts `robot_state_publisher`
4. Starts `ros_gz_bridge`
5. Starts `depthimage_to_laserscan` (vision-based obstacle perception)
6. Initializes the `robot_localization` EKF filter (`use_sim_time: true`)
7. Boots the Nav2 navigation stack (6 active lifecycle nodes)

### Step 3: Send a Navigation Goal (Point A -> Point B)
Open a second terminal and execute the goal script:
```bash
# Navigate to Point B past the boulder obstacle:
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/send_goal.sh 7.0 0.0

# Or navigate back to origin (Point A):
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/send_goal.sh 0.0 0.0
```

> **Note on coordinates:** In `outdoor_terrain.sdf`, a boulder obstacle is placed at $(5.0, 0.2)$. Point B at $(7.0, 0.0)$ commands the UGV to navigate *past* the boulder. Sending $(5.0, 0.0)$ places the target directly inside the boulder geometry.

### Step 4 (Optional): Visual Monitoring via RViz2
In a separate terminal:
```bash
wsl -d Ubuntu-24.04 /mnt/c/Users/GIGA/Desktop/sih2026/scripts/view_nav.sh
```

---

## 4. Verification & Validation Checklist

Verify the running system using the following commands:

1. **TF Tree Verification:**
   ```bash
   ros2 run tf2_tools view_frames
   ```
   *Expected:* Clean transform continuity from `odom` -> `base_footprint` -> `base_link` -> `camera_link` / `imu_link`.

2. **Sensor Topic Publishing Rates:**
   ```bash
   ros2 topic hz /camera/image_raw
   ros2 topic hz /camera/depth/image_raw
   ros2 topic hz /imu
   ros2 topic hz /odom
   ```
   *Expected:* Camera: ~30 Hz, IMU: ~100 Hz, Odometry: ~50 Hz.

3. **Autonomous Actuation:**
   Monitor `/cmd_vel` during goal traversal:
   ```bash
   ros2 topic echo /cmd_vel
   ```
   *Expected:* Non-zero linear and angular velocities commanding the UGV around the obstacle.
