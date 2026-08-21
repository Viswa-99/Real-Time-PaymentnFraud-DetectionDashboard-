#!/usr/bin/env python3
"""
===========================================================================
REAL-TIME PAYMENTS FRAUD DETECTION DASHBOARD
SIMULATION BOT WEB CONTROL PANEL & WEBSOCKET BROADCAST SERVER
===========================================================================
"""

import os
import sys
import json
import time
import asyncio
import http.server
import socketserver
import threading
from bot import TransactionSimulatorBot

HTML_GUI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transaction Simulation Bot — Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: #0b0f19; color: #f3f4f6; padding: 24px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f293d; padding-bottom: 16px; margin-bottom: 24px; }
        .logo { font-size: 20px; font-weight: 700; background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .badge { background: #1e1b4b; color: #818cf8; font-weight: 600; padding: 4px 12px; border-radius: 9999px; font-size: 12px; border: 1px solid #3730a3; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #111827; border: 1px solid #1f293d; border-radius: 12px; padding: 20px; }
        .card-title { color: #9ca3af; font-size: 13px; font-weight: 500; text-transform: uppercase; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700; color: #ffffff; }
        .card-value.highlight { color: #22c55e; }
        .card-value.warn { color: #f59e0b; }
        .card-value.danger { color: #ef4444; }
        .control-panel { background: #111827; border: 1px solid #1f293d; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
        .slider-group { margin-bottom: 20px; }
        .slider-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: 600; }
        input[type=range] { width: 100%; accent-color: #6366f1; height: 8px; border-radius: 4px; background: #1f293d; cursor: pointer; }
        .btn-group { display: flex; gap: 12px; flex-wrap: wrap; }
        .btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; border: none; cursor: pointer; transition: all 0.2s; font-size: 14px; }
        .btn-primary { background: #4f46e5; color: white; }
        .btn-primary:hover { background: #4338ca; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-danger:hover { background: #b91c1c; }
        .btn-secondary { background: #1f293d; color: white; border: 1px solid #374151; }
        .btn-secondary:hover { background: #374151; }
        .log-box { background: #050811; border: 1px solid #1f293d; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; height: 180px; overflow-y: auto; color: #a7f3d0; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">⚡ Real-Time Payments Fraud Detection Simulator</div>
        <div class="badge" id="statusBadge">RUNNING — 100 TPS</div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Target Throughput</div>
            <div class="card-value highlight" id="tpsVal">100 TPS</div>
        </div>
        <div class="card">
            <div class="card-title">Total Transactions Sent</div>
            <div class="card-value" id="totalSent">0</div>
        </div>
        <div class="card">
            <div class="card-title">Layer 2 Flagged Anomalies</div>
            <div class="card-value warn" id="anomalies">0</div>
        </div>
        <div class="card">
            <div class="card-title">Blocked Transactions</div>
            <div class="card-value danger" id="blocked">0</div>
        </div>
    </div>

    <div class="control-panel">
        <h3 style="margin-bottom: 16px; font-size: 16px;">Simulation Controls & Rate Governor</h3>
        <div class="slider-group">
            <div class="slider-header">
                <span>Transactions Per Second (TPS) Speed</span>
                <span id="sliderValue">100 TPS</span>
            </div>
            <input type="range" id="tpsSlider" min="1" max="500" value="100" oninput="updateTPS(this.value)">
        </div>

        <div class="btn-group">
            <button class="btn btn-secondary" onclick="triggerAnomaly('HIGH_VELOCITY')">🚨 Inject High Velocity Flood</button>
            <button class="btn btn-secondary" onclick="triggerAnomaly('UNUSUAL_LOCATION')">✈️ Inject Impossible Travel</button>
            <button class="btn btn-secondary" onclick="triggerAnomaly('NEW_DEVICE')">📱 Inject New Device Spike</button>
            <button class="btn btn-secondary" onclick="triggerAnomaly('UNUSUAL_AMOUNT')">💰 Inject High Ticket Size</button>
        </div>
    </div>

    <h3 style="margin-bottom: 12px; font-size: 14px; color: #9ca3af;">Live Output Log Stream</h3>
    <div class="log-box" id="logBox">
        [SYSTEM] Simulator Control Dashboard Loaded.<br>
        [SYSTEM] Connected to WebSocket Broadcast on ws://localhost:8080/ws<br>
    </div>

    <script>
        function updateTPS(val) {
            document.getElementById('sliderValue').innerText = val + ' TPS';
            document.getElementById('tpsVal').innerText = val + ' TPS';
            document.getElementById('statusBadge').innerText = 'RUNNING — ' + val + ' TPS';
            fetch('/api/set-tps?val=' + val);
        }

        function triggerAnomaly(type) {
            const logBox = document.getElementById('logBox');
            logBox.innerHTML += '[ACTION] Injected anomaly burst: ' + type + '<br>';
            logBox.scrollTop = logBox.scrollHeight;
            fetch('/api/inject?type=' + type);
        }

        setInterval(() => {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalSent').innerText = data.totalSent.toLocaleString();
                    document.getElementById('anomalies').innerText = data.anomalies.toLocaleString();
                    document.getElementById('blocked').innerText = data.blocked.toLocaleString();
                }).catch(() => {});
        }, 1000);
    </script>
</body>
</html>
"""

class ControlPanelHandler(http.server.SimpleHTTPRequestHandler):
    bot_instance = None

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_GUI.encode('utf-8'))
        elif self.path.startswith('/api/set-tps'):
            try:
                tps = int(self.path.split('=')[1])
                if ControlPanelHandler.bot_instance:
                    ControlPanelHandler.bot_instance.tps = tps
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "tps": tps}).encode('utf-8'))
            except Exception:
                self.send_error(400)
        elif self.path == '/api/stats':
            b = ControlPanelHandler.bot_instance
            stats = {
                "totalSent": b.total_sent if b else 0,
                "anomalies": b.total_anomalies if b else 0,
                "blocked": b.total_blocked if b else 0,
                "tps": b.tps if b else 100
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Suppress verbose http logging
        pass

def run_http_control_server(port=9090):
    handler = ControlPanelHandler
    server = socketserver.TCPServer(("", port), handler)
    print(f"\033[96m[Web Control Panel] Dashboard running on http://localhost:{port}\033[0m")
    server.serve_forever()

def main():
    bot = TransactionSimulatorBot(tps_override=100)
    ControlPanelHandler.bot_instance = bot

    # Start HTTP GUI Server in background thread
    gui_thread = threading.Thread(target=run_http_control_server, daemon=True)
    gui_thread.start()

    try:
        asyncio.run(bot.run_simulation())
    except KeyboardInterrupt:
        print("\n[Server] Shutdown requested.")

if __name__ == "__main__":
    main()
