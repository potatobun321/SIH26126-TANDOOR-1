#!/usr/bin/env bash
# view_all.sh — Launch both Gazebo Harmonic GUI and RViz2 simultaneously
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure WSLg graphics environment
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
if [ -d "/mnt/wslg/runtime-dir" ]; then
  export XDG_RUNTIME_DIR="/mnt/wslg/runtime-dir"
fi

echo "=== Launching Gazebo Harmonic 3D Client in background ==="
bash "$REPO_DIR/scripts/view_gz.sh" &
GZ_PID=$!

echo "=== Launching RViz2 Navigation Interface ==="
bash "$REPO_DIR/scripts/view_nav.sh" &
RVIZ_PID=$!

echo "Gazebo PID: $GZ_PID | RViz2 PID: $RVIZ_PID"
wait $GZ_PID $RVIZ_PID
