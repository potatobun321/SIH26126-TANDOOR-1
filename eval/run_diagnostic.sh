#!/usr/bin/env bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Ensure clean state
killall -9 gz sim ros2 python3 2>/dev/null
sleep 1

echo "[*] Starting outdoor_vertical_slice stack..."
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True > /tmp/sim_launch.log 2>&1 &
LAUNCH_PID=$!
echo "[*] Launch PID: $LAUNCH_PID. Waiting 12 seconds for bringup..."
sleep 12

echo "[*] Running diagnostic listener for 5 seconds..."
python3 eval/debug_scan.py &
DIAG_PID=$!
sleep 6

kill -9 $DIAG_PID 2>/dev/null
kill -9 $LAUNCH_PID 2>/dev/null
killall -9 gz sim ros2 python3 2>/dev/null

echo "[*] Diagnostic complete. Recent launch log:"
tail -n 30 /tmp/sim_launch.log
