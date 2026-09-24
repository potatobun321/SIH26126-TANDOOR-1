#!/usr/bin/env bash
# run_sim.sh — Build and Launch the SIH26126 Phase 1 Vertical Slice
set -e

HEADLESS="False"
for arg in "$@"; do
  if [ "$arg" == "--headless" ] || [ "$arg" == "-s" ]; then
    HEADLESS="True"
  fi
done

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Sourcing ROS 2 Jazzy ==="
source /opt/ros/jazzy/setup.bash

echo "=== Sourcing workspace overlay ==="
source install/setup.bash

echo "=== Launching Phase 1 Outdoor Vertical Slice (Headless=$HEADLESS) ==="
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=$HEADLESS
