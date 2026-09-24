@echo off
title SIH 2026 UGV - Gazebo Harmonic & RViz2 Native GUIs
echo ===================================================================
echo   SIH 2026 - Problem Statement SIH26126 (BEL)
echo   Team: Tikka Techies - Vision-Based Autonomous Outdoor UGV
echo ===================================================================
echo.
echo Launching Gazebo Harmonic 3D Simulation Client...
start "Gazebo 3D GUI" wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/GIGA/Desktop/sih2026 && bash scripts/view_gz.sh"

echo Launching RViz2 Navigation & Tactical HUD GUI...
start "RViz2 GUI" wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/GIGA/Desktop/sih2026 && bash scripts/view_nav.sh"

echo.
echo Both GUIs launched! Both windows will appear on your desktop via WSLg.
echo You can close this console window at any time.
