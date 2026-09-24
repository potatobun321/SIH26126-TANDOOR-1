#!/usr/bin/env bash
# view_gz.sh — Launch Gazebo Harmonic 3D GUI client connecting to running simulation
set -e

# Ensure WSLg graphics environment
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
if [ -d "/mnt/wslg/runtime-dir" ]; then
  export XDG_RUNTIME_DIR="/mnt/wslg/runtime-dir"
fi

source /opt/ros/jazzy/setup.bash

echo "=== Connecting Gazebo GUI Client to Running Simulation ==="
gz sim -g
