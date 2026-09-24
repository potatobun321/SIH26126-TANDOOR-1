#!/usr/bin/env bash
set -e

echo "[*] Cleaning up any stale processes..."
killall -9 gz sim ruby ros2 python3 parameter_bridge 2>/dev/null || true
sleep 2

cd /mnt/c/Users/GIGA/Desktop/sih2026
source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "[*] Launching UGV simulation and autonomy stack (headless)..."
ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True &
STACK_PID=$!

cleanup() {
    echo "[*] Tearing down test stack (PID $STACK_PID)..."
    kill -9 $STACK_PID 2>/dev/null || true
    killall -9 gz sim ruby ros2 python3 parameter_bridge 2>/dev/null || true
}
trap cleanup EXIT

echo "[*] Waiting 16s for Nav2 lifecycle managers to transition to ACTIVE..."
sleep 16

echo "[*] Executing Point A -> B automated navigation test..."
python3 eval/test_nav_ab.py
echo "[*] Point A -> B test finished successfully!"
