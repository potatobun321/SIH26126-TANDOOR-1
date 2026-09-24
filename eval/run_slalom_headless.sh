#!/usr/bin/env bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

killall -9 gz sim ruby ros2 python3 parameter_bridge 2>/dev/null || true
sleep 2

echo "[*] Launching headless autonomy stack..."
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True > /tmp/sim_launch.log 2>&1 &
LAUNCH_PID=$!
echo "[*] Launch PID: $LAUNCH_PID. Waiting 20s for Nav2 activation..."
sleep 20

echo "[*] Executing Serpentine Slalom Automated Test..."
python3 scripts/serpentine_slalom_test.py
RESULT=$?

kill -9 $LAUNCH_PID 2>/dev/null || true
killall -9 gz sim ruby ros2 python3 parameter_bridge 2>/dev/null || true

echo "[*] Slalom test complete with exit code $RESULT."
exit $RESULT
