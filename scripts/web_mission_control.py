#!/usr/bin/env python3
"""
web_mission_control.py — High-Efficiency Minimalist Tactical Console & 2D Vector Map
Part of SIH 2026 Problem Statement SIH26126 (Tikka Techies)
Multi-threaded HTTP daemon on port 8080.
Provides real-time interactive 2D tactical map, live HUD video, telemetry, and waypoint dispatch.
"""

import os
import sys
import time
import math
import json
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import numpy as np
import cv2

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import Float32
from cv_bridge import CvBridge
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus

# Canonical 7-Leg Serpentine Slalom Course (North/South Weave Around Hazards)
# Obstacle geometry reference:
#   Boulder: (5.0, 0.35) r=0.5m  — south edge y=-0.15, north edge y=+0.85
#   Tree:    (8.0, -2.0) r=0.42m — north edge y=-1.58, south edge y=-2.42
#   Robot circumscribed radius: 0.616m.  Min clearance: 0.65m (inflation_radius)
SLALOM_WAYPOINTS = [
    {'x': 2.0, 'y':  1.8, 'yaw': -1.15, 'name': 'Weave 1/7: North Trail Crest'},
    {'x': 3.8, 'y': -1.8, 'yaw':  1.17, 'name': 'Weave 2/7: South Hazard Crossing'},
    {'x': 6.6, 'y':  1.1, 'yaw': -0.80, 'name': 'Weave 3/7: North Boulder Bypass'},
    {'x': 7.0, 'y': -1.4, 'yaw':  0.99, 'name': 'Weave 4/7: Tree/Boulder Corridor'},
    {'x': 9.0, 'y':  1.0, 'yaw':  3.14, 'name': 'Weave 5/7: Deep Frontier Apex'},
    {'x': 4.5, 'y': -1.2, 'yaw':  3.14, 'name': 'Weave 6/7: South Corridor Return'},
    {'x': 0.0, 'y':  0.0, 'yaw':  3.14, 'name': 'Weave 7/7: Base Camp Home Closure'}
]

# Global Shared State
dashboard_state = {
    'latest_jpeg': None,
    'pos_x': 0.0,
    'pos_y': 0.0,
    'speed': 0.0,
    'heading_deg': 0.0,
    'target_x': None,
    'target_y': None,
    'distance_to_goal': 0.0,
    'trail': [],
    'planned_path': [],
    'course_waypoints': [],
    'slalom_active': False,
    'fps': 29.5,
    'latency_ms': 3.8,
    'mission_status': 'SYSTEM READY',
    'active_goal': 'NONE',
    'logs': [
        f"[{time.strftime('%H:%M:%S')}] Console initialized on port 8080",
        f"[{time.strftime('%H:%M:%S')}] Tactical Map & Calibrated IPM Online"
    ]
}
state_lock = threading.Lock()
frame_condition = threading.Condition(state_lock)
ros_node_instance = None

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SIH26126 Tactical Autonomy Console | Tikka Techies</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #000000;
      --surface: #0a0a0a;
      --surface-elevated: #111111;
      --border: #222222;
      --border-subtle: #181818;
      --text: #ededed;
      --text-muted: #888888;
      --text-subtle: #555555;
      --accent: #ffffff;
      --cyan: #38bdf8;
      --emerald: #22c55e;
      --amber: #f59e0b;
      --rose: #ef4444;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 13px;
      line-height: 1.4;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
    }

    /* Minimal Top Navigation */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 0.6rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand-section {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
    }
    .brand-title {
      font-weight: 700;
      font-size: 0.88rem;
      letter-spacing: 0.05em;
      color: #fff;
    }
    .brand-tag {
      font-family: var(--font-mono);
      font-size: 0.68rem;
      color: var(--text-muted);
      border-left: 1px solid var(--border);
      padding-left: 0.75rem;
    }

    .top-stats {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .stat-val { color: var(--text); font-weight: 600; }

    .status-pill {
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 600;
      padding: 0.15rem 0.55rem;
      border-radius: 4px;
      letter-spacing: 0.03em;
    }
    .status-ready { background: #12281a; color: var(--emerald); border: 1px solid #1c4d28; }
    .status-active { background: #0c2338; color: var(--cyan); border: 1px solid #15456b; }
    .status-alert { background: #331114; color: var(--rose); border: 1px solid #631c23; }

    /* Main Workspace */
    .workspace {
      flex: 1;
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
      padding: 1.25rem;
      display: grid;
      grid-template-columns: 1.35fr 1fr;
      gap: 1.25rem;
    }
    @media (max-width: 1100px) {
      .workspace { grid-template-columns: 1fr; }
    }

    /* Pane Container */
    .pane {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .pane-header {
      padding: 0.6rem 1rem;
      background: var(--surface-elevated);
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--text-muted);
      letter-spacing: 0.04em;
    }
    .pane-header span.title {
      font-weight: 600;
      color: var(--text);
    }

    /* 2D Interactive Vector Map Canvas */
    .canvas-container {
      position: relative;
      background: #050505;
      width: 100%;
      aspect-ratio: 16 / 10;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: crosshair;
    }
    #map-canvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .canvas-hud {
      position: absolute;
      bottom: 10px;
      left: 12px;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      color: rgba(255, 255, 255, 0.6);
      background: rgba(0, 0, 0, 0.7);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      pointer-events: none;
    }

    /* Video Frame */
    .video-container {
      position: relative;
      background: #000;
      width: 100%;
      aspect-ratio: 4 / 3;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #video-feed {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .video-toggle {
      background: rgba(0, 0, 0, 0.7);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.65rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      cursor: pointer;
    }
    .video-toggle:hover { color: #fff; border-color: #555; }

    /* Telemetry Grid */
    .telem-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      border-top: 1px solid var(--border);
      background: var(--border-subtle);
      gap: 1px;
    }
    .telem-card {
      background: var(--surface);
      padding: 0.65rem 0.85rem;
    }
    .telem-lbl {
      font-family: var(--font-mono);
      font-size: 0.64rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .telem-val {
      font-family: var(--font-mono);
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      margin-top: 0.15rem;
    }
    .telem-unit {
      font-size: 0.68rem;
      font-weight: 400;
      color: var(--text-muted);
      margin-left: 0.15rem;
    }

    /* Action Command Deck */
    .action-deck {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      padding: 0.85rem;
    }
    .action-btn {
      appearance: none;
      border: 1px solid var(--border);
      background: var(--surface-elevated);
      color: var(--text);
      padding: 0.65rem 0.9rem;
      border-radius: 5px;
      font-family: var(--font-sans);
      font-size: 0.82rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: background 0.1s ease, border-color 0.1s ease;
      user-select: none;
    }
    .action-btn:hover {
      background: #191919;
      border-color: #444;
    }
    .action-btn:active {
      transform: translateY(1px);
    }
    .key-badge {
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 700;
      background: #222;
      color: var(--cyan);
      padding: 0.15rem 0.4rem;
      border-radius: 3px;
      margin-right: 0.65rem;
      border: 1px solid #333;
    }
    .action-btn-primary {
      border-color: rgba(56, 189, 248, 0.35);
    }
    .action-btn-primary:hover {
      border-color: var(--cyan);
      background: rgba(56, 189, 248, 0.08);
    }
    .action-btn-danger {
      border-color: rgba(239, 68, 68, 0.4);
    }
    .action-btn-danger .key-badge {
      color: var(--rose);
      border-color: rgba(239, 68, 68, 0.3);
    }
    .action-btn-danger:hover {
      background: rgba(239, 68, 68, 0.12);
      border-color: var(--rose);
    }

    /* Terminal Stream */
    .log-stream {
      background: #050505;
      padding: 0.65rem 0.85rem;
      font-family: var(--font-mono);
      font-size: 0.70rem;
      height: 110px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      color: #999;
      border-top: 1px solid var(--border);
    }
    .log-entry { line-height: 1.4; }
    .log-entry::before { content: "› "; color: var(--cyan); font-weight: bold; }

    /* Footer */
    footer {
      border-top: 1px solid var(--border);
      padding: 0.5rem 1.5rem;
      display: flex;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      color: var(--text-subtle);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand-section">
      <div class="live-dot"></div>
      <div class="brand-title">TIKKA TECHIES &bull; SIH26126</div>
      <div class="brand-tag">AUTONOMOUS UGV MISSION CONTROL (BEL)</div>
    </div>
    <div class="top-stats">
      <div>FPS: <span class="stat-val" id="stat-fps">29.5</span></div>
      <div>LATENCY: <span class="stat-val" id="stat-lat">3.8 ms</span></div>
      <div>TARGET: <span class="stat-val" id="stat-target">NONE</span></div>
      <div id="stat-status" class="status-pill status-ready">READY</div>
    </div>
  </header>

  <main class="workspace">
    <!-- Left Pane: 2D Tactical Vector Map -->
    <div class="pane">
      <div class="pane-header">
        <span class="title">2D TACTICAL VECTOR MAP & TRAJECTORY</span>
        <span>CLICK ANYWHERE TO DISPATCH GOAL</span>
      </div>

      <div class="canvas-container" id="canvas-wrapper">
        <canvas id="map-canvas"></canvas>
        <div class="canvas-hud" id="canvas-hud">UGV: (+0.00, +0.00) | GOAL: NONE</div>
      </div>

      <div class="telem-row">
        <div class="telem-card">
          <div class="telem-lbl">X Position</div>
          <div class="telem-val"><span id="val-x">0.00</span><span class="telem-unit">m</span></div>
        </div>
        <div class="telem-card">
          <div class="telem-lbl">Y Position</div>
          <div class="telem-val"><span id="val-y">0.00</span><span class="telem-unit">m</span></div>
        </div>
        <div class="telem-card">
          <div class="telem-lbl">Velocity</div>
          <div class="telem-val"><span id="val-spd">0.00</span><span class="telem-unit">m/s</span></div>
        </div>
        <div class="telem-card">
          <div class="telem-lbl">Heading</div>
          <div class="telem-val"><span id="val-hdg">000</span><span class="telem-unit">°</span></div>
        </div>
      </div>
    </div>

    <!-- Right Pane: Live Optical HUD & Command Deck -->
    <div style="display: flex; flex-direction: column; gap: 1.25rem;">
      <div class="pane">
        <div class="pane-header">
          <span class="title">OPTICAL RECONNAISSANCE HUD</span>
          <button class="video-toggle" id="toggle-video-btn" onclick="toggleVideo()">HUD STREAM: ACTIVE</button>
        </div>
        <div class="video-container">
          <img id="video-feed" src="/stream.mjpg" alt="Live HUD Stream">
        </div>
      </div>

      <div class="pane" style="flex: 1;">
        <div class="pane-header">
          <span class="title">COMMAND DECK</span>
          <span>HOTKEYS: [1] [2] [R] [SPACE]</span>
        </div>

        <div class="action-deck">
          <button class="action-btn action-btn-primary" id="btn-1" onclick="sendNav('nav_ab')">
            <div><span class="key-badge">1</span><span>Traverse Laterite Trail (Point A &rarr; B)</span></div>
            <span style="font-family: var(--font-mono); font-size: 0.70rem; color: var(--text-muted);">(7.5, 0.0)</span>
          </button>

          <button class="action-btn" id="btn-2" onclick="sendNav('nav_slalom')">
            <div><span class="key-badge">2</span><span>Execute Serpentine Slalom Weave</span></div>
            <span style="font-family: var(--font-mono); font-size: 0.70rem; color: var(--text-muted);">7 Waypoints</span>
          </button>

          <button class="action-btn" id="btn-r" onclick="sendNav('return_base')">
            <div><span class="key-badge">R</span><span>Return to Base Origin</span></div>
            <span style="font-family: var(--font-mono); font-size: 0.70rem; color: var(--text-muted);">(0.0, 0.0)</span>
          </button>

          <button class="action-btn action-btn-danger" id="btn-stop" onclick="sendNav('stop')">
            <div><span class="key-badge">SPC</span><span>EMERGENCY ALL-STOP</span></div>
            <span style="font-family: var(--font-mono); font-size: 0.70rem; color: var(--rose);">Instant 0m/s</span>
          </button>
        </div>

        <div class="log-stream" id="log-box">
          <!-- Populated live via telemetry -->
        </div>
      </div>
    </div>
  </main>

  <footer>
    <div>SIH 2026 | Problem Statement SIH26126 (BEL) | Government Engineering College, Jaipur</div>
    <div>ROS 2 Jazzy &bull; Calibrated IPM &bull; MobileNetV3 ONNX &bull; Threaded Engine</div>
  </footer>

  <script>
    // Real-time State Store
    const state = {
      pos_x: 0,
      pos_y: 0,
      speed: 0,
      heading_deg: 0,
      target_x: null,
      target_y: null,
      distance_to_goal: 0,
      trail: [],
      planned_path: [],
      fps: 29.5,
      latency_ms: 3.8,
      status: 'READY'
    };

    let videoActive = true;
    function toggleVideo() {
      videoActive = !videoActive;
      const img = document.getElementById('video-feed');
      const btn = document.getElementById('toggle-video-btn');
      if (videoActive) {
        img.src = '/stream.mjpg';
        btn.textContent = 'HUD STREAM: ACTIVE';
        btn.style.color = '#fff';
      } else {
        img.src = '';
        btn.textContent = 'HUD STREAM: PAUSED';
        btn.style.color = 'var(--amber)';
      }
    }

    // 2D Tactical Map Renderer
    const canvas = document.getElementById('map-canvas');
    const ctx = canvas.getContext('2d');
    let canvasW = 0, canvasH = 0;

    function resizeCanvas() {
      const rect = canvas.getBoundingClientRect();
      if (rect.width !== canvasW || rect.height !== canvasH) {
        canvasW = rect.width;
        canvasH = rect.height;
        canvas.width = canvasW * window.devicePixelRatio;
        canvas.height = canvasH * window.devicePixelRatio;
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
    }

    // Coordinate Mapping: World (X: -2 to 10m, Y: -4 to +4m) -> Canvas
    const WORLD = { minX: -2.0, maxX: 10.0, minY: -3.8, maxY: 3.8 };
    function worldToCanvas(wx, wy) {
      const u = (wx - WORLD.minX) / (WORLD.maxX - WORLD.minX) * canvasW;
      const v = (1.0 - (wy - WORLD.minY) / (WORLD.maxY - WORLD.minY)) * canvasH;
      return { u, v };
    }
    function canvasToWorld(u, v) {
      const wx = WORLD.minX + (u / canvasW) * (WORLD.maxX - WORLD.minX);
      const wy = WORLD.maxY - (v / canvasH) * (WORLD.maxY - WORLD.minY);
      return { wx, wy };
    }

    // Interactive Click-To-Navigate
    canvas.addEventListener('click', (e) => {
      const rect = canvas.getBoundingClientRect();
      const u = e.clientX - rect.left;
      const v = e.clientY - rect.top;
      const { wx, wy } = canvasToWorld(u, v);
      
      // Instant visual feedback: place target immediately
      state.target_x = Math.round(wx * 10) / 10;
      state.target_y = Math.round(wy * 10) / 10;
      state.status = `NAVIGATING TO (${state.target_x}, ${state.target_y})`;
      renderMap();

      // Dispatch to ROS 2 backend
      sendCustomGoal(state.target_x, state.target_y);
    });

    function renderMap() {
      resizeCanvas();
      if (!canvasW || !canvasH) return;

      ctx.clearRect(0, 0, canvasW, canvasH);

      // 1. Grid lines (1m intervals)
      ctx.strokeStyle = '#141414';
      ctx.lineWidth = 1;
      for (let x = Math.ceil(WORLD.minX); x <= WORLD.maxX; x += 1.0) {
        const { u } = worldToCanvas(x, 0);
        ctx.beginPath();
        ctx.moveTo(u, 0);
        ctx.lineTo(u, canvasH);
        ctx.stroke();
      }
      for (let y = Math.ceil(WORLD.minY); y <= WORLD.maxY; y += 1.0) {
        const { v } = worldToCanvas(0, y);
        ctx.beginPath();
        ctx.moveTo(0, v);
        ctx.lineTo(canvasW, v);
        ctx.stroke();
      }

      // 2. Laterite Trail Band (Y: -2.1 to +2.1m, width: 4.2m)
      const topTrail = worldToCanvas(0, 2.1).v;
      const botTrail = worldToCanvas(0, -2.1).v;
      ctx.fillStyle = 'rgba(217, 119, 6, 0.04)';
      ctx.fillRect(0, topTrail, canvasW, botTrail - topTrail);
      ctx.strokeStyle = 'rgba(217, 119, 6, 0.15)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, topTrail); ctx.lineTo(canvasW, topTrail);
      ctx.moveTo(0, botTrail); ctx.lineTo(canvasW, botTrail);
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Known Natural Hazards & Landmarks (Exact Metric World Coordinates)
      // Dynamic Hazard Patrol Corridor (X=3.4, Y=1.2 to 2.6m)
      const dh1 = worldToCanvas(3.4, 1.2);
      const dh2 = worldToCanvas(3.4, 2.6);
      ctx.strokeStyle = 'rgba(244, 63, 94, 0.4)';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(dh1.u, dh1.v);
      ctx.lineTo(dh2.u, dh2.v);
      ctx.stroke();
      ctx.fillStyle = '#f43f5e';
      ctx.beginPath();
      ctx.arc(dh1.u, (dh1.v + dh2.v) / 2, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = '8px JetBrains Mono';
      ctx.fillText('DYNAMIC HAZARD [3.4, 1.2-2.6]', dh1.u + 10, (dh1.v + dh2.v) / 2 + 3);

      // Faceted Boulder at (5.0, 0.35, radius: 0.50m)
      const bCoord = worldToCanvas(5.0, 0.35);
      ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(bCoord.u, bCoord.v, 13, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#ef4444';
      ctx.font = '9px JetBrains Mono';
      ctx.fillText('BOULDER [5.0, 0.35]', bCoord.u + 16, bCoord.v + 3);

      // Scrub Tree at (8.0, -2.0, radius: 0.42m)
      const tCoord = worldToCanvas(8.0, -2.0);
      ctx.fillStyle = 'rgba(234, 179, 8, 0.18)';
      ctx.strokeStyle = '#eab308';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(tCoord.u, tCoord.v, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#eab308';
      ctx.font = '9px JetBrains Mono';
      ctx.fillText('TREE [8.0, -2.0]', tCoord.u + 14, tCoord.v + 3);

      // Natural Ditch Barrier at (12.0, 1.0)
      const barCoord = worldToCanvas(12.0, 1.0);
      ctx.fillStyle = 'rgba(244, 63, 94, 0.2)';
      ctx.strokeStyle = '#f43f5e';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.rect(barCoord.u - 8, barCoord.v - 18, 16, 36);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#f43f5e';
      ctx.font = '9px JetBrains Mono';
      ctx.fillText('BARRIER [12.0, 1.0]', barCoord.u + 12, barCoord.v + 3);

      // Goal B Milestone (7.5, 0.0)
      const gBCoord = worldToCanvas(7.5, 0.0);
      ctx.fillStyle = 'rgba(34, 197, 94, 0.18)';
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(gBCoord.u, gBCoord.v, 9, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#22c55e';
      ctx.font = 'bold 9px JetBrains Mono';
      ctx.fillText('GOAL B [7.5, 0.0]', gBCoord.u + 12, gBCoord.v + 3);

      // Base Origin Marker (0,0)
      const oCoord = worldToCanvas(0, 0);
      ctx.strokeStyle = '#64748b';
      ctx.beginPath();
      ctx.arc(oCoord.u, oCoord.v, 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = '#94a3b8';
      ctx.font = '9px JetBrains Mono';
      ctx.fillText('BASE [0, 0]', oCoord.u + 10, oCoord.v - 6);

      // 4. Vehicle Breadcrumb Trail
      if (state.trail && state.trail.length > 1) {
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        state.trail.forEach((pt, idx) => {
          const { u, v } = worldToCanvas(pt[0], pt[1]);
          if (idx === 0) ctx.moveTo(u, v);
          else ctx.lineTo(u, v);
        });
        ctx.stroke();
      }

      // 5.5. Serpentine Slalom Course Milestones & S-Curve Trajectory
      if (state.course_waypoints && state.course_waypoints.length > 0) {
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.45)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        state.course_waypoints.forEach((pt, idx) => {
          const { u, v } = worldToCanvas(pt[0], pt[1]);
          if (idx === 0) ctx.moveTo(u, v);
          else ctx.lineTo(u, v);
        });
        ctx.stroke();
        ctx.setLineDash([]);

        // Numbered Milestone Badges
        state.course_waypoints.forEach((pt, idx) => {
          const { u, v } = worldToCanvas(pt[0], pt[1]);
          const isCurrent = (state.target_x !== null && Math.hypot(pt[0] - state.target_x, pt[1] - state.target_y) < 0.35);
          ctx.fillStyle = isCurrent ? '#38bdf8' : '#1e293b';
          ctx.strokeStyle = isCurrent ? '#ffffff' : '#f59e0b';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(u, v, 8, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = isCurrent ? '#000000' : '#f8fafc';
          ctx.font = 'bold 9px Inter, sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(String(idx + 1), u, v);
        });
        ctx.textAlign = 'start';
        ctx.textBaseline = 'alphabetic';
      }

      // 6. Target Waypoint Reticle
      if (state.target_x !== null && state.target_y !== null) {
        const tPos = worldToCanvas(state.target_x, state.target_y);
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(tPos.u, tPos.v, 9, 0, Math.PI * 2);
        ctx.stroke();

        // Crosshairs
        ctx.beginPath();
        ctx.moveTo(tPos.u - 14, tPos.v); ctx.lineTo(tPos.u + 14, tPos.v);
        ctx.moveTo(tPos.u, tPos.v - 14); ctx.lineTo(tPos.u, tPos.v + 14);
        ctx.stroke();

        // Direct trajectory guide line from vehicle to target
        const vPos = worldToCanvas(state.pos_x, state.pos_y);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
        ctx.setLineDash([2, 4]);
        ctx.beginPath();
        ctx.moveTo(vPos.u, vPos.v);
        ctx.lineTo(tPos.u, tPos.v);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 7. Vehicle Body & Heading Arrow
      const vPos = worldToCanvas(state.pos_x, state.pos_y);
      const rad = state.heading_deg * Math.PI / 180.0;
      
      ctx.save();
      ctx.translate(vPos.u, vPos.v);
      ctx.rotate(-rad); // Invert for canvas coordinate system

      // Sharp directional wedge
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(14, 0);
      ctx.lineTo(-9, -8);
      ctx.lineTo(-5, 0);
      ctx.lineTo(-9, 8);
      ctx.closePath();
      ctx.fill();

      // Heading projection ray
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(14, 0);
      ctx.lineTo(28, 0);
      ctx.stroke();

      ctx.restore();

      // Update Canvas HUD
      const tgtStr = (state.target_x !== null) ? `(${state.target_x.toFixed(1)}, ${state.target_y.toFixed(1)})` : 'NONE';
      const distStr = (state.distance_to_goal > 0) ? ` | DIST: ${state.distance_to_goal.toFixed(2)}m` : '';
      document.getElementById('canvas-hud').textContent = 
        `UGV: (${state.pos_x.toFixed(2)}, ${state.pos_y.toFixed(2)}) | GOAL: ${tgtStr}${distStr}`;
    }

    // Telemetry Polling via Threaded Endpoint
    let isPolling = false;
    async function updateTelemetry() {
      if (isPolling) return;
      isPolling = true;
      try {
        const res = await fetch('/api/telemetry');
        if (!res.ok) { isPolling = false; return; }
        const data = await res.json();

        // Sync local state
        state.pos_x = data.pos_x;
        state.pos_y = data.pos_y;
        state.speed = data.speed;
        state.heading_deg = data.heading_deg;
        state.target_x = data.target_x;
        state.target_y = data.target_y;
        state.distance_to_goal = data.distance_to_goal;
        state.trail = data.trail || [];
        state.planned_path = data.planned_path || [];
        state.course_waypoints = data.course_waypoints || [];
        state.fps = data.fps;
        state.latency_ms = data.latency_ms;
        state.status = data.mission_status;

        // Render DOM Elements
        document.getElementById('val-x').textContent = state.pos_x.toFixed(2);
        document.getElementById('val-y').textContent = state.pos_y.toFixed(2);
        document.getElementById('val-spd').textContent = state.speed.toFixed(2);
        document.getElementById('val-hdg').textContent = String(Math.round(state.heading_deg)).padStart(3, '0');

        document.getElementById('stat-fps').textContent = state.fps.toFixed(1);
        document.getElementById('stat-lat').textContent = state.latency_ms.toFixed(1) + ' ms';
        document.getElementById('stat-target').textContent = data.active_goal || 'NONE';

        const statusEl = document.getElementById('stat-status');
        statusEl.textContent = state.status;
        if (state.status.includes('ACTIVE') || state.status.includes('NAV') || state.status.includes('SLALOM')) {
          statusEl.className = 'status-pill status-active';
        } else if (state.status.includes('ALERT') || state.status.includes('HALT')) {
          statusEl.className = 'status-pill status-alert';
        } else {
          statusEl.className = 'status-pill status-ready';
        }

        // Terminal Log
        const logBox = document.getElementById('log-box');
        logBox.innerHTML = '';
        (data.logs || []).slice(-10).forEach(line => {
          const div = document.createElement('div');
          div.className = 'log-entry';
          div.textContent = line;
          logBox.appendChild(div);
        });
        logBox.scrollTop = logBox.scrollHeight;

        // Redraw 2D Map
        renderMap();
      } catch (e) {
        // silent recovery
      } finally {
        isPolling = false;
      }
    }

    // Action Command Dispatchers
    async function sendNav(cmd) {
      if (cmd === 'nav_ab') {
        state.course_waypoints = [];
        state.target_x = 7.5;
        state.target_y = 0.0;
        state.status = 'NAVIGATING TO (7.5, 0.0)';
      } else if (cmd === 'nav_slalom') {
        state.course_waypoints = [
          [2.0, 1.8], [3.6, -1.8], [5.2, 2.0], [7.0, -1.4], [9.0, 1.0], [4.5, -1.6], [0.0, 0.0]
        ];
        state.target_x = 2.0;
        state.target_y = 1.8;
        state.status = 'SLALOM [1/7]: Weave 1';
      } else if (cmd === 'return_base') {
        state.course_waypoints = [];
        state.target_x = 0.0;
        state.target_y = 0.0;
        state.status = 'RETURNING TO BASE (0.0, 0.0)';
      } else if (cmd === 'stop') {
        state.course_waypoints = [];
        state.target_x = null;
        state.target_y = null;
        state.planned_path = [];
        state.status = 'EMERGENCY HALT';
      }
      renderMap();

      try {
        await fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: cmd })
        });
        updateTelemetry();
      } catch (e) {
        alert("Command dispatch error: " + e);
      }
    }

    async function sendCustomGoal(x, y) {
      state.course_waypoints = [];
      try {
        await fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: 'custom_goal', x: x, y: y })
        });
        updateTelemetry();
      } catch (e) {
        alert("Custom waypoint dispatch error: " + e);
      }
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === '1') { e.preventDefault(); sendNav('nav_ab'); }
      else if (e.key === '2') { e.preventDefault(); sendNav('nav_slalom'); }
      else if (e.key === 'r' || e.key === 'R') { e.preventDefault(); sendNav('return_base'); }
      else if (e.code === 'Space') { e.preventDefault(); sendNav('stop'); }
    });

    window.addEventListener('resize', renderMap);
    async function pollLoop() {
      await updateTelemetry();
      setTimeout(pollLoop, 35);
    }
    renderMap();
    pollLoop();
  </script>
</body>
</html>
"""

class MissionControlHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence console log noise to keep output fast and clean
        return

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode('utf-8'))

        elif self.path == '/api/telemetry':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with state_lock:
                telemetry_data = {k: v for k, v in dashboard_state.items() if k != 'latest_jpeg'}
                data_str = json.dumps(telemetry_data)
            self.wfile.write(data_str.encode('utf-8'))

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            try:
                last_frame = None
                while True:
                    with frame_condition:
                        frame_condition.wait(timeout=0.1)
                        frame_bytes = dashboard_state['latest_jpeg']
                    if frame_bytes is not None and frame_bytes != last_frame:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(frame_bytes)))
                        self.end_headers()
                        self.wfile.write(frame_bytes)
                        self.wfile.write(b'\r\n')
                        self.wfile.flush()
                        last_frame = frame_bytes
            except (ConnectionResetError, BrokenPipeError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/command':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                cmd_data = json.loads(body.decode('utf-8'))
                if ros_node_instance:
                    ros_node_instance.handle_user_command(cmd_data)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'OK'}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

class MissionControlNode(Node):
    def __init__(self):
        super().__init__('ugv_mission_control_node')
        self.bridge = CvBridge()

        # Subscribers
        self.sub_overlay = self.create_subscription(
            Image,
            '/perception/segmentation_overlay',
            self.overlay_callback,
            10
        )
        self.sub_odom = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.odom_callback,
            10
        )
        self.sub_plan = self.create_subscription(
            Path,
            '/plan',
            self.plan_callback,
            10
        )
        self.sub_fps = self.create_subscription(
            Float32,
            '/perception/fps',
            self.fps_callback,
            10
        )
        self.sub_lat = self.create_subscription(
            Float32,
            '/perception/latency_ms',
            self.lat_callback,
            10
        )

        # Publishers & Nav2 Action Client
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_goal_pose = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.nav_action_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.active_goal_handle = None
        self.active_target_coords = None
        self.mission_queue = []
        self.total_queue_len = 0
        self.current_leg_idx = 0

        self.get_logger().info('Mission Control ROS 2 Threaded Node initialized.')

    def overlay_callback(self, msg: Image):
        # Allow fluid 30 FPS video streaming
        now = time.time()
        if hasattr(self, '_last_enc') and (now - self._last_enc < 0.033):
            return
        self._last_enc = now

        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            scaled_img = cv2.resize(cv_img, (512, 384), interpolation=cv2.INTER_AREA)
            success, jpeg_buf = cv2.imencode('.jpg', scaled_img, [cv2.IMWRITE_JPEG_QUALITY, 62])
            if success:
                with frame_condition:
                    dashboard_state['latest_jpeg'] = jpeg_buf.tobytes()
                    frame_condition.notify_all()
        except Exception as e:
            self.get_logger().error(f'Frame encode error: {e}')

    def odom_callback(self, msg: Odometry):
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        spd = math.sqrt(vx * vx + vy * vy)
        px = msg.pose.pose.position.x
        py = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw_deg = (math.degrees(math.atan2(siny_cosp, cosy_cosp)) + 360.0) % 360.0

        with state_lock:
            dashboard_state['pos_x'] = round(px, 2)
            dashboard_state['pos_y'] = round(py, 2)
            dashboard_state['speed'] = round(spd, 2)
            dashboard_state['heading_deg'] = round(yaw_deg, 1)

            # Accumulate vehicle breadcrumb trail
            trail = dashboard_state.setdefault('trail', [])
            if not trail or math.hypot(px - trail[-1][0], py - trail[-1][1]) > 0.12:
                trail.append([round(px, 2), round(py, 2)])
                if len(trail) > 80:
                    trail.pop(0)
            dashboard_state['trail'] = trail

            # Update distance if active target exists
            if self.active_target_coords and self.active_goal_handle is None:
                tx, ty = self.active_target_coords
                dashboard_state['distance_to_goal'] = round(math.hypot(tx - px, ty - py), 2)

    def plan_callback(self, msg: Path):
        pts = []
        step = max(1, len(msg.poses) // 35)
        for pose in msg.poses[::step]:
            pts.append([round(pose.pose.position.x, 2), round(pose.pose.position.y, 2)])
        if msg.poses:
            last = msg.poses[-1].pose.position
            pts.append([round(last.x, 2), round(last.y, 2)])
        with state_lock:
            dashboard_state['planned_path'] = pts

    def fps_callback(self, msg: Float32):
        with state_lock:
            dashboard_state['fps'] = float(msg.data)

    def lat_callback(self, msg: Float32):
        with state_lock:
            dashboard_state['latency_ms'] = float(msg.data)

    def log_event(self, text: str):
        timestamp = time.strftime('%H:%M:%S')
        entry = f"[{timestamp}] {text}"
        self.get_logger().info(text)
        with state_lock:
            dashboard_state['logs'].append(entry)
            if len(dashboard_state['logs']) > 40:
                dashboard_state['logs'].pop(0)

    def handle_user_command(self, cmd_data):
        if isinstance(cmd_data, dict):
            cmd = cmd_data.get('command')
        else:
            cmd = str(cmd_data)

        if cmd == 'nav_ab':
            self.mission_queue = []
            self.total_queue_len = 0
            self.current_leg_idx = 0
            with state_lock:
                dashboard_state['slalom_active'] = False
                dashboard_state['course_waypoints'] = []
            self.log_event("COMMAND: Mission A -> B (Goal: X=7.5, Y=-0.5)")
            self.dispatch_goal(7.5, -0.5, 0.0)

        elif cmd == 'return_base':
            curr_x = dashboard_state.get('pos_x', 0.0)
            if curr_x > 5.2:
                # Robot is deep in field — use 3-leg southern return, avoiding tree at (8,-2,r=0.42)
                # Tree inflation zone: 0.42+0.65=1.07m. Safe: x<6.93 or y<-3.07 or y>-0.93
                # Boulder inflation zone: 0.5+0.65=1.15m. Safe: y<-0.8 or y>1.5 around x=5
                self.mission_queue = [
                    {'x': 6.0,  'y': -1.00, 'yaw': 2.60,     'name': 'Leg R1: Diagonal South-West Escape'},
                    {'x': 3.0,  'y': -1.50, 'yaw': 3.14159,  'name': 'Leg R2: West via South Corridor'},
                    {'x': 0.0,  'y': 0.0,   'yaw': 3.14159,  'name': 'Leg R3: Base Camp Home'}
                ]
                self.total_queue_len = len(self.mission_queue)
                self.current_leg_idx = 0
                with state_lock:
                    dashboard_state['slalom_active'] = False
                    dashboard_state['course_waypoints'] = [[6.0, -1.0], [3.0, -1.5], [0.0, 0.0]]
                self.log_event("COMMAND: Safe Return via (6.0,-1.0) -> (3.0,-1.5) -> (0.0,0.0)")
                self.dispatch_next_mission_waypoint()
            else:
                self.mission_queue = []
                self.total_queue_len = 0
                self.current_leg_idx = 0
                with state_lock:
                    dashboard_state['slalom_active'] = False
                    dashboard_state['course_waypoints'] = []
                self.log_event("COMMAND: Return Base (Goal: X=0.0, Y=0.0)")
                self.dispatch_goal(0.0, 0.0, 3.14159)

        elif cmd == 'nav_slalom':
            self.log_event("COMMAND: Serpentine Slalom Course Initiated (7 Legs)")
            self.mission_queue = [dict(wp) for wp in SLALOM_WAYPOINTS]
            self.total_queue_len = len(self.mission_queue)
            self.current_leg_idx = 0
            with state_lock:
                dashboard_state['slalom_active'] = True
                dashboard_state['course_waypoints'] = [[wp['x'], wp['y']] for wp in SLALOM_WAYPOINTS]
            self.dispatch_next_mission_waypoint()

        elif cmd == 'custom_goal':
            self.mission_queue = []
            self.total_queue_len = 0
            self.current_leg_idx = 0
            with state_lock:
                dashboard_state['slalom_active'] = False
                dashboard_state['course_waypoints'] = []
            gx = float(cmd_data.get('x', 0.0))
            gy = float(cmd_data.get('y', 0.0))
            self.log_event(f"COMMAND: Map Waypoint (X={gx:.1f}, Y={gy:.1f})")
            self.dispatch_goal(gx, gy, 0.0)

        elif cmd == 'stop':
            self.mission_queue = []
            self.total_queue_len = 0
            self.current_leg_idx = 0
            self.log_event("COMMAND: EMERGENCY ALL-STOP TRIGGERED")
            with state_lock:
                dashboard_state['mission_status'] = 'EMERGENCY HALT'
                dashboard_state['slalom_active'] = False
                dashboard_state['course_waypoints'] = []
                dashboard_state['target_x'] = None
                dashboard_state['target_y'] = None
                dashboard_state['active_goal'] = 'NONE'
                dashboard_state['distance_to_goal'] = 0.0
                dashboard_state['planned_path'] = []

            if self.active_goal_handle is not None:
                try:
                    self.active_goal_handle.cancel_goal_async()
                except Exception:
                    pass
                self.active_goal_handle = None

            zero_twist = Twist()
            for _ in range(5):
                self.pub_cmd_vel.publish(zero_twist)

    def dispatch_next_mission_waypoint(self):
        if not self.mission_queue:
            with state_lock:
                dashboard_state['slalom_active'] = False
                dashboard_state['mission_status'] = 'SLALOM COMPLETE: ALL 7 LEGS SUCCESS'
            self.log_event("COURSE COMPLETE: All 7 Slalom Weave milestones achieved successfully!")
            self.total_queue_len = 0
            self.current_leg_idx = 0
            return

        wp = self.mission_queue.pop(0)
        self.current_leg_idx += 1
        leg_name = wp.get('name', f"Leg {self.current_leg_idx}/{self.total_queue_len}")
        self.log_event(f"SLALOM PROGRESS [{self.current_leg_idx}/{self.total_queue_len}]: Dispatching to {leg_name} -> ({wp['x']:.1f}, {wp['y']:.1f})")
        with state_lock:
            dashboard_state['mission_status'] = f"SLALOM [{self.current_leg_idx}/{self.total_queue_len}]: {leg_name}"
        self.dispatch_goal(wp['x'], wp['y'], wp['yaw'])

    def dispatch_goal(self, x: float, y: float, yaw: float):
        qz = float(round(math.sin(yaw / 2.0), 4))
        qw = float(round(math.cos(yaw / 2.0), 4))
        self.active_target_coords = (x, y)

        with state_lock:
            dashboard_state['target_x'] = round(x, 2)
            dashboard_state['target_y'] = round(y, 2)
            dashboard_state['active_goal'] = f"({x:.1f}, {y:.1f})"
            curr_x = dashboard_state['pos_x']
            curr_y = dashboard_state['pos_y']
            dashboard_state['distance_to_goal'] = round(math.hypot(x - curr_x, y - curr_y), 2)
            if not dashboard_state['slalom_active']:
                dashboard_state['mission_status'] = f"NAVIGATING TO ({x:.1f}, {y:.1f})"

        self.log_event(f"Nav2 Dispatch Target: ({x:.2f}, {y:.2f})")

        # Async Nav2 Action Client (clean single-channel dispatch)
        def _send_nav_action():
            if not self.nav_action_client.wait_for_server(timeout_sec=3.0):
                self.log_event("Nav2 action server not available. Dispatched via topic fallback.")
                goal_msg = PoseStamped()
                goal_msg.header.stamp = self.get_clock().now().to_msg()
                goal_msg.header.frame_id = 'map'
                goal_msg.pose.position.x = float(x)
                goal_msg.pose.position.y = float(y)
                goal_msg.pose.position.z = 0.0
                goal_msg.pose.orientation.z = qz
                goal_msg.pose.orientation.w = qw
                self.pub_goal_pose.publish(goal_msg)
                return

            # Cleanly cancel any existing active goal before submitting a new one
            if self.active_goal_handle is not None:
                try:
                    self.active_goal_handle.cancel_goal_async()
                except Exception:
                    pass
                self.active_goal_handle = None

            action_goal = NavigateToPose.Goal()
            action_goal.pose.header.frame_id = 'map'
            action_goal.pose.header.stamp = self.get_clock().now().to_msg()
            action_goal.pose.pose.position.x = float(x)
            action_goal.pose.pose.position.y = float(y)
            action_goal.pose.pose.orientation.z = qz
            action_goal.pose.pose.orientation.w = qw

            send_future = self.nav_action_client.send_goal_async(
                action_goal,
                feedback_callback=self.action_feedback_callback
            )
            send_future.add_done_callback(lambda fut: self.goal_response_callback(fut, x, y))

        threading.Thread(target=_send_nav_action, daemon=True).start()

    def action_feedback_callback(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        with state_lock:
            dashboard_state['distance_to_goal'] = round(float(dist), 2)

    def goal_response_callback(self, future, x, y):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.log_event(f"Goal REJECTED by Nav2 ({x:.1f}, {y:.1f})")
                with state_lock:
                    dashboard_state['mission_status'] = 'GOAL REJECTED'
                return

            self.active_goal_handle = goal_handle
            self.log_event(f"Goal ACCEPTED ({x:.1f}, {y:.1f}). Tracking trajectory.")
            with state_lock:
                if not dashboard_state['slalom_active']:
                    dashboard_state['mission_status'] = f'TRACKING ({x:.1f}, {y:.1f})'

            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(lambda fut: self.get_result_callback(fut, x, y))
        except Exception as e:
            self.log_event(f"Goal response error: {e}")

    def get_result_callback(self, future, x, y):
        try:
            result = future.result()
            status = result.status
            if status == GoalStatus.STATUS_SUCCEEDED:
                self.log_event(f"MISSION SUCCESS: Reached ({x:.1f}, {y:.1f})")
                with state_lock:
                    dashboard_state['distance_to_goal'] = 0.0
                    dashboard_state['planned_path'] = []

                if self.mission_queue:
                    next_num = self.current_leg_idx + 1
                    self.log_event(f"Auto-advancing to Slalom Leg {next_num}/{self.total_queue_len} in 0.4s...")
                    threading.Timer(0.4, self.dispatch_next_mission_waypoint).start()
                else:
                    if self.total_queue_len > 0:
                        with state_lock:
                            dashboard_state['slalom_active'] = False
                            dashboard_state['mission_status'] = 'SLALOM COMPLETE: ALL 7 LEGS SUCCESS'
                        self.log_event("COURSE COMPLETE: All 7 Slalom Weave milestones achieved!")
                        self.total_queue_len = 0
                        self.current_leg_idx = 0
                    else:
                        with state_lock:
                            dashboard_state['mission_status'] = 'TARGET REACHED'
            elif status == GoalStatus.STATUS_CANCELED:
                self.mission_queue = []
                self.total_queue_len = 0
                self.current_leg_idx = 0
                self.log_event("MISSION HALTED: Canceled by user.")
                with state_lock:
                    dashboard_state['slalom_active'] = False
                    dashboard_state['mission_status'] = 'CANCELED'
            else:
                self.log_event(f"Mission leg aborted (status {status}).")
                self.mission_queue = []
                self.total_queue_len = 0
                self.current_leg_idx = 0
                with state_lock:
                    dashboard_state['slalom_active'] = False
                    dashboard_state['mission_status'] = f'STOPPED (Status {status})'
        except Exception as e:
            self.log_event(f"Result error: {e}")
        finally:
            self.active_goal_handle = None

class ReusableThreadingServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def start_http_server(preferred_ports=(8080, 8090, 8088)):
    for port in preferred_ports:
        try:
            server = ReusableThreadingServer(("", port), MissionControlHTTPHandler)
            print(f"\n=======================================================")
            print(f"[MISSION CONTROL] Threaded Dashboard active: http://localhost:{port}")
            print(f"=======================================================\n")
            server.serve_forever()
            return
        except OSError:
            print(f"[MISSION CONTROL] Port {port} busy, trying fallback...")

def main():
    global ros_node_instance
    rclpy.init()
    ros_node_instance = MissionControlNode()

    # Synthetic Standby HUD Frame
    standby_img = np.zeros((384, 512, 3), dtype=np.uint8)
    cv2.putText(standby_img, "TIKKA TECHIES | UGV MISSION CONTROL", (50, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (56, 189, 248), 2, cv2.LINE_AA)
    cv2.putText(standby_img, "CALIBRATED IPM PERCEPTION ONLINE", (90, 215),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
    _, s_jpg = cv2.imencode('.jpg', standby_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    dashboard_state['latest_jpeg'] = s_jpg.tobytes()

    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(ros_node_instance)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        ros_node_instance.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
