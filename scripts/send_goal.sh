#!/usr/bin/env bash
# send_goal.sh — Send an autonomous navigation goal to the UGV
set -e

X_GOAL=${1:-7.0}
Y_GOAL=${2:-0.0}

Q_Z="0.0"
Q_W="1.0"

if [ "$#" -ge 3 ]; then
  YAW_VAL="$3"
  Q_Z=$(python3 -c "import math; print(round(math.sin(float($YAW_VAL)/2.0), 4))")
  Q_W=$(python3 -c "import math; print(round(math.cos(float($YAW_VAL)/2.0), 4))")
elif [ "$(echo "$X_GOAL <= 1.0" | bc -l)" -eq 1 ]; then
  # Return journey toward origin: naturally face travel direction (yaw = pi)
  Q_Z="1.0"
  Q_W="0.0"
fi

echo "=== SIH26126 Autonomous Navigation ==="
echo "Point A: (0.0, 0.0) | Obstacle (Boulder): (5.0, 0.2)"
echo "Target Goal: X = $X_GOAL, Y = $Y_GOAL (Heading Quat: z=$Q_Z, w=$Q_W)"
echo "Sending goal to /navigate_to_pose action server..."

source /opt/ros/jazzy/setup.bash
source /mnt/c/Users/GIGA/Desktop/sih2026/install/setup.bash

ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: 'map'}, pose: {position: {x: $X_GOAL, y: $Y_GOAL, z: 0.0}, orientation: {z: $Q_Z, w: $Q_W}}}}"
