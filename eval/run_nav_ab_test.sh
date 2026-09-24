#!/usr/bin/env bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

killall -9 gz sim ros2 python3 2>/dev/null
sleep 1

echo "[*] Launching headless autonomy stack..."
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True > /tmp/sim_launch.log 2>&1 &
LAUNCH_PID=$!
echo "[*] Launch PID: $LAUNCH_PID. Waiting 14s for Nav2 activation..."
sleep 14

echo "[*] Executing Point A to B Automated Test..."
python3 eval/test_nav_ab.py
RESULT=$?

kill -9 $LAUNCH_PID 2>/dev/null
killall -9 gz sim ros2 python3 2>/dev/null

echo "[*] Test run complete with exit code $RESULT."
exit $RESULT
