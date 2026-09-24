#!/usr/bin/env bash
# view_nav.sh — Launch RViz2 pre-configured for UGV navigation visualization
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$REPO_DIR/install/setup.bash"

# Ensure WSLg graphics environment
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
if [ -d "/mnt/wslg/runtime-dir" ]; then
  export XDG_RUNTIME_DIR="/mnt/wslg/runtime-dir"
fi

RVIZ_CONFIG="$REPO_DIR/src/ugv_nav2/config/view_navigation.rviz"

echo "=== Launching RViz2 with UGV Navigation & AI Perception Profile ==="
rviz2 -d "$RVIZ_CONFIG"
