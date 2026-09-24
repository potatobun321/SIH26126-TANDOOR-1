#!/usr/bin/env bash
# setup_ros2_jazzy.sh — Automated Setup for ROS 2 Jazzy & Gazebo Harmonic on Ubuntu 24.04 (Noble)
set -e

echo "=== Tikka Techies | SIH26126 Environment Setup ==="
echo "Target: Ubuntu 24.04 LTS (Noble Numbat) -> ROS 2 Jazzy + Gazebo Harmonic + Nav2"

# 1. Update and install base utilities
sudo apt update && sudo apt install -y \
  software-properties-common \
  curl \
  gnupg \
  lsb-release \
  build-essential \
  cmake \
  git \
  python3-pip

# 2. Enable Ubuntu Universe repository
sudo add-apt-repository universe -y

# 3. Add ROS 2 GPG Key and Official Repository
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. Update package index now that ROS 2 repo is added
sudo apt update

# 5. Install Colcon build tools, Rosdep, and ROS 2 Jazzy Desktop
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  ros-jazzy-desktop

# 6. Install Gazebo Harmonic and ROS-Gazebo Bridge
sudo apt install -y \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-interfaces

# 7. Install Nav2, EKF Localization, and Perception utilities
sudo apt install -y \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-robot-localization \
  ros-jazzy-image-transport \
  ros-jazzy-cv-bridge \
  ros-jazzy-foxglove-bridge

# 8. Initialize rosdep
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update

# 9. Add ROS 2 sourcing to bashrc
if ! grep -q "source /opt/ros/jazzy/setup.bash" ~/.bashrc; then
  echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
  echo "export GZ_VERSION=harmonic" >> ~/.bashrc
fi

echo "=== Setup Complete! ROS 2 Jazzy + Gazebo Harmonic + Nav2 installed successfully. ==="
