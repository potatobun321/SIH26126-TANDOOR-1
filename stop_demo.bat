@echo off
title SIH 2026 UGV - Clean Demonstration Teardown (Tikka Techies)
color 0C

echo ===============================================================================
echo   TEARING DOWN SIH26126 UGV AUTONOMY & SIMULATION STACK
echo ===============================================================================
echo.
echo [*] Terminating ROS 2 nodes, Gazebo Harmonic, and Web Mission Control...
wsl -d Ubuntu-24.04 bash -c "killall -9 gz sim ruby ros2 python3 parameter_bridge 2>/dev/null" >nul 2>&1
timeout /t 1 /nobreak >nul

echo [*] Resetting WSL2 kernel environment...
wsl --shutdown >nul 2>&1
timeout /t 1 /nobreak >nul

echo.
echo ===============================================================================
echo   [OK] ALL PROCESSES TERMINATED CLEANLY.
echo   All CPU cores and memory reclaimed. Safe to restart or sleep system.
echo ===============================================================================
echo.
pause
