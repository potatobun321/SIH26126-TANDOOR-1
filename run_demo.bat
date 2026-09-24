@echo off
title SIH 2026 UGV - Live Demonstration Launcher (Tikka Techies)
color 0B

echo ===============================================================================
echo   SMART INDIA HACKATHON 2026 - PROBLEM STATEMENT SIH26126 (BEL)
echo   TEAM: TIKKA TECHIES ^| GOVERNMENT ENGINEERING COLLEGE, JAIPUR
echo   SYSTEM: VISION-BASED AUTONOMOUS NAVIGATION FOR OUTDOOR UGV (GPS-DENIED)
echo ===============================================================================
echo.
echo [*] Step 1/4: Resetting WSL2 environment to eliminate stale processes and memory leaks...
wsl -d Ubuntu-24.04 -u root bash -c "killall -9 gz ruby python3 ros2 parameter_bridge 2>/dev/null || true" >nul 2>&1
timeout /t 1 /nobreak >nul
wsl --shutdown >nul 2>&1
timeout /t 2 /nobreak >nul
wsl -d Ubuntu-24.04 -u root echo [OK] Pristine WSL2 Linux Kernel Ready.

echo.
echo [*] Step 2/4: Launching Gazebo Harmonic ^& ROS 2 Autonomy Stack...
start "SIH26126 ROS2 Autonomy Stack" wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/GIGA/Desktop/sih2026 && source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 launch ugv_bringup outdoor_vertical_slice.launch.py headless:=True"

echo Waiting 10 seconds for Gazebo physics and Nav2 lifecycle managers to configure...
timeout /t 10 /nobreak >nul

echo.
echo [*] Step 3/4: Launching Threaded Tactical Mission Control Server...
start "SIH26126 Web Mission Control" wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/GIGA/Desktop/sih2026 && source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3 scripts/web_mission_control.py"

echo Waiting 2 seconds for server binding on port 8080...
timeout /t 2 /nobreak >nul

echo.
echo [*] Step 4/4: Opening Tactical Mission Control in default browser...
start http://localhost:8080

echo.
echo ===============================================================================
echo                      LIVE DEMONSTRATION READY!
echo ===============================================================================
echo   Console URL   : http://localhost:8080
echo.
echo   INTERACTIVE CONTROLS:
echo     - 2D MAP CLICK : Click anywhere on the 2D tactical map to send a waypoint!
echo     - [1]          : Traverse Laterite Trail (Point A -^> B around boulder)
echo     - [2]          : Execute Serpentine Slalom Weave (7 Waypoints)
echo     - [R]          : Return to Base Origin (0,0)
echo     - [SPACE]      : EMERGENCY ALL-STOP (Zero velocity)
echo     - HUD TOGGLE   : Click "HUD STREAM: ACTIVE" to pause camera for max FPS
echo     - TEARDOWN     : Run stop_demo.bat to shut down all processes cleanly
echo ===============================================================================
echo.
pause
