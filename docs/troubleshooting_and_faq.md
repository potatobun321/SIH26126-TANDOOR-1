# Troubleshooting & Frequently Asked Questions (FAQ)

Practical solutions for development, simulation, and environment issues on Windows 11 / WSL2.

---

## 1. WSL2 Password & Sudo Permissions

### How was the password issue resolved?
Your WSL2 environment has been pre-configured with **passwordless sudo** for user `giga`.
- **Default Username:** `giga`
- **Default Password:** `giga` (if an interactive utility ever requests it)
- **Passwordless Sudo:** Enabled via `/etc/sudoers.d/giga-nopasswd`.

### How to reset a forgotten WSL password in the future?
From Windows PowerShell (Administrator or standard):
```powershell
wsl -d Ubuntu-24.04 -u root bash -c "echo '<username>:<new_password>' | chpasswd"
```

---

## 2. Display & GUI Issues (WSLg)

### Issue: Gazebo or RViz2 window does not appear on Windows desktop
1. Verify WSLg display variable inside Ubuntu:
   ```bash
   echo $DISPLAY
   ```
   *Expected:* `:0`.
2. Test a minimal graphical application:
   ```bash
   sudo apt install -y x11-apps
   xeyes
   ```
3. If windows fail to open, update the Windows WSL subsystem:
   ```powershell
   wsl --update
   wsl --shutdown
   ```

---

## 3. Gazebo Harmonic & ros_gz_bridge

### Issue: `gz sim` fails with rendering error or crashes on startup
- Ensure OGRE2 rendering is specified:
  ```bash
  export GZ_RENDERING_ENGINE=ogre2
  ```
- If running headless or in low-resource mode, add `-s` (server-only):
  ```bash
  gz sim -s -r outdoor_terrain.sdf
  ```

### Issue: ROS 2 topics not receiving data from Gazebo
- Check if the bridge is running:
  ```bash
  ros2 topic list
  ros2 topic hz /camera/image_raw
  ```
- Verify Gazebo internal topics directly:
  ```bash
  gz topic -l
  gz topic -e -t /camera/image
  ```
- Ensure simulation time is synchronized across all ROS 2 nodes by setting `use_sim_time: True` in launch files.

---

## 4. Colcon Build & Workspace Issues

### Issue: `colcon build` fails with missing package dependencies
- Run rosdep update and install missing dependencies:
  ```bash
  cd /mnt/c/Users/GIGA/Desktop/sih2026
  rosdep install --from-paths src --ignore-src -r -y
  ```

### Issue: Packages not found after building
- Always source the local workspace overlay in every new terminal:
  ```bash
  source /opt/ros/jazzy/setup.bash
  source /mnt/c/Users/GIGA/Desktop/sih2026/install/setup.bash
  ```
