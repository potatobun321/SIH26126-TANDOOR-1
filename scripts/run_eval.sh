#!/usr/bin/env bash
# run_eval.sh — Headless Evaluation Runner wrapper for SIH26126
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=== Sourcing ROS 2 Jazzy ==="
source /opt/ros/jazzy/setup.bash

echo "=== Sourcing Workspace Overlay ==="
source install/setup.bash

echo "=== Starting Headless Evaluation Suite ==="
python3 scripts/run_automated_eval.py "$@"
