#!/usr/bin/env python3
"""
===========================================================================
UPI TRANSACTION SIMULATOR — CONTROL PANEL & DEMO INTERFACE
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

main_event_loop = None

HTML_GUI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPI Transaction Simulator — Demo Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: #0b0f19; color: #f3f4f6; padding: 24px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f293d; padding-bottom: 16px; margin-bottom: 24px; }
        .logo { font-size: 20px; font-weight: 700; background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .badge { background: #1e1b4b; color: #818cf8; font-weight: 600; padding: 4px 12px; border-radius: 9999px; font-size: 12px; border: 1px solid #3730a3; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #111827; border: 1px solid #1f293d; border-radius: 12px; padding: 20px; }
        .card-title { color: #9ca3af; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-bottom: 8px; }
        .card-value { font-size: 28px; font-weight: 700; color: #ffffff; }
        .card-value.highlight { color: #22c55e; }
        .card-value.warn { color: #f59e0b; }
        .card-value.danger { color: #ef4444; }
        .control-panel { background: #111827; border: 1px solid #1f293d; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
        .panel-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #e5e7eb; }
        .slider-group { margin-bottom: 20px; }
        .slider-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: 600; font-size: 14px; }
        input[type=range] { width: 100%; accent-color: #6366f1; height: 8px; border-radius: 4px; background: #1f293d; cursor: pointer; }
        
        .main-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .btn-large { padding: 18px 24px; border-radius: 12px; font-weight: 700; border: none; cursor: pointer; transition: all 0.2s; font-size: 15px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; }
        .btn-normal { background: linear-gradient(135deg, #16a34a, #15803d); color: white; box-shadow: 0 4px 14px rgba(22, 163, 74, 0.3); }
        .btn-normal:hover { background: linear-gradient(135deg, #15803d, #166534); transform: translateY(-1px); }
        .btn-suspicious { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; box-shadow: 0 4px 14px rgba(220, 38, 38, 0.3); }
        .btn-suspicious:hover { background: linear-gradient(135deg, #b91c1c, #991b1b); transform: translateY(-1px); }
        .btn-stream { background: linear-gradient(135deg, #4f46e5, #4338ca); color: white; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3); }
        .btn-stream:hover { background: linear-gradient(135deg, #4338ca, #3730a3); transform: translateY(-1px); }
        
        .sub-btn-group { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
        .btn-sm { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; border: 1px solid #374151; background: #1f293d; color: #d1d5db; cursor: pointer; }
        .btn-sm:hover { background: #374151; color: white; }

        .log-box { background: #050811; border: 1px solid #1f293d; border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; height: 220px; overflow-y: auto; color: #a7f3d0; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">⚡ UPI Transaction Simulator</div>
        <div class="badge" id="statusBadge">READY — V3 REFERENCE DATASET</div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Simulator Mode</div>
            <div class="card-value highlight" id="simMode">IDLE</div>
        </div>
        <div class="card">
            <div class="card-title">Target Throughput</div>
            <div class="card-value" id="tpsVal">100 TPS</div>
        </div>
        <div class="card">
            <div class="card-title">Total Sent to ML API</div>
            <div class="card-value" id="totalSent">0</div>
        </div>
        <div class="card">
            <div class="card-title">ML Flagged Anomalies</div>
            <div class="card-value danger" id="anomalies">0</div>
        </div>
    </div>

    <div class="main-actions">
        <button class="btn-large btn-normal" onclick="triggerNormal()">
            <span>✅ Normal Transaction</span>
            <span style="font-size: 12px; opacity: 0.85; font-weight: 400;">Selects clean V3 transaction & sends raw JSON</span>
        </button>
        <button class="btn-large btn-suspicious" onclick="triggerSuspicious()">
            <span>🚨 Generate Suspicious Transaction</span>
            <span style="font-size: 12px; opacity: 0.85; font-weight: 400;">Selects ground-truth anomaly & sends raw JSON</span>
        </button>
        <button class="btn-large btn-stream" id="streamBtn" onclick="toggleStream()">
            <span>▶️ Stream Transactions</span>
            <span style="font-size: 12px; opacity: 0.85; font-weight: 400;">Continuously stream raw transactions at TPS speed</span>
        </button>
    </div>

    <div class="control-panel">
        <div class="panel-title">Specific Anomaly Injectors (Ground-Truth Reference Data)</div>
        <div class="sub-btn-group">
            <button class="btn-sm" onclick="triggerSpecific('NEW_RECEIVER')">👤 New Receiver Anomaly</button>
            <button class="btn-sm" onclick="triggerSpecific('UNUSUAL_LOCATION')">✈️ Unusual Location / Travel</button>
            <button class="btn-sm" onclick="triggerSpecific('NEW_DEVICE')">📱 New Device Anomaly</button>
            <button class="btn-sm" onclick="triggerSpecific('BEHAVIORAL_DRIFT')">📈 Behavioral Drift Anomaly</button>
        </div>

        <div class="slider-group" style="margin-top: 24px;">
            <div class="slider-header">
                <span>Streaming Speed (Transactions Per Second)</span>
                <span id="sliderValue">100 TPS</span>
            </div>
            <input type="range" id="tpsSlider" min="1" max="500" value="100" oninput="updateTPS(this.value)">
        </div>
    </div>

    <h3 style="margin-bottom: 12px; font-size: 14px; color: #9ca3af;">Live Output Log Stream</h3>
    <div class="log-box" id="logBox">
        [SYSTEM] UPI Simulator Control Panel Ready.<br>
        [SYSTEM] Connected to Dataset: synthetic_upi_transactions_v3.csv<br>
        [SYSTEM] Ground truth fields are stripped before sending raw JSON payloads to ML API.<br>
    </div>

    <script>
        let isStreaming = false;

        function log(msg) {
            const logBox = document.getElementById('logBox');
            logBox.innerHTML += '[' + new Date().toLocaleTimeString() + '] ' + msg + '<br>';
            logBox.scrollTop = logBox.scrollHeight;
        }

        function triggerNormal() {
            log('--> [ACTION] Clicked "Normal Transaction"');
            fetch('/api/trigger-normal')
                .then(r => r.json())
                .then(data => {
                    log('  <-- ML Response: Risk = ' + (data.risk_score ? data.risk_score.toFixed(2) : 0) + '%, Decision = ' + (data.decision || 'NORMAL'));
                }).catch(e => log('  <-- Error: ' + e));
        }

        function triggerSuspicious() {
            log('--> [ACTION] Clicked "Generate Suspicious Transaction"');
            fetch('/api/trigger-suspicious')
                .then(r => r.json())
                .then(data => {
                    log('  <-- ML Response: Risk = ' + (data.risk_score ? data.risk_score.toFixed(2) : 0) + '%, Decision = ' + (data.decision || 'ANOMALY'));
                    if (data.reasons && data.reasons.length > 0) {
                        data.reasons.forEach(r => log('      • Reason: ' + r.title + ' - ' + r.detail));
                    }
                }).catch(e => log('  <-- Error: ' + e));
        }

        function triggerSpecific(type) {
            log('--> [ACTION] Triggering anomaly pattern: ' + type);
            fetch('/api/trigger-suspicious?type=' + type)
                .then(r => r.json())
                .then(data => {
                    log('  <-- ML Response: Risk = ' + (data.risk_score ? data.risk_score.toFixed(2) : 0) + '%, Decision = ' + (data.decision || 'ANOMALY'));
                }).catch(e => log('  <-- Error: ' + e));
        }

        function toggleStream() {
            isStreaming = !isStreaming;
            const btn = document.getElementById('streamBtn');
            const modeEl = document.getElementById('simMode');
            if (isStreaming) {
                btn.innerHTML = '<span>⏸️ Pause Stream</span><span style="font-size: 12px; opacity: 0.85; font-weight: 400;">Stop streaming transactions</span>';
                modeEl.innerText = 'STREAMING';
                log('[ACTION] Started continuous transaction stream');
                fetch('/api/toggle-stream?state=start');
            } else {
                btn.innerHTML = '<span>▶️ Stream Transactions</span><span style="font-size: 12px; opacity: 0.85; font-weight: 400;">Continuously stream raw transactions at TPS speed</span>';
                modeEl.innerText = 'IDLE';
                log('[ACTION] Paused continuous transaction stream');
                fetch('/api/toggle-stream?state=stop');
            }
        }

        function updateTPS(val) {
            document.getElementById('sliderValue').innerText = val + ' TPS';
            document.getElementById('tpsVal').innerText = val + ' TPS';
            fetch('/api/set-tps?val=' + val);
        }

        setInterval(() => {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalSent').innerText = data.totalSent.toLocaleString();
                    document.getElementById('anomalies').innerText = data.anomalies.toLocaleString();
                }).catch(() => {});
        }, 1000);
    </script>
</body>
</html>
"""

class ControlPanelHandler(http.server.SimpleHTTPRequestHandler):
    bot_instance = None

    def _send_json_response(self, data: dict, status_code=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        bot = ControlPanelHandler.bot_instance
        if self.path == '/' or self.path == '/index.html':
            body = HTML_GUI.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith('/api/trigger-normal'):
            if bot and main_event_loop:
                async def _do_normal():
                    try:
                        payload = bot.loader.get_normal_transaction(update_timestamp=True)
                        async with aiohttp.ClientSession() as session:
                            async with session.post("http://127.0.0.1:5001/transactions", json=payload) as resp:
                                res_data = await resp.json()
                                if res_data.get("decision") == "ANOMALY":
                                    bot.total_anomalies += 1
                                    bot.total_blocked += 1
                                bot.total_sent += 1
                                return res_data
                    except Exception as ex:
                        return {"status": "error", "message": f"{type(ex).__name__}: {str(ex)}"}

                fut = asyncio.run_coroutine_threadsafe(_do_normal(), main_event_loop)
                try:
                    res = fut.result(timeout=5.0)
                except Exception as e:
                    res = {"status": "error", "message": f"Future timeout: {type(e).__name__}: {str(e)}"}
            else:
                res = {"status": "error", "message": "Bot or main_event_loop unavailable"}
            
            self._send_json_response(res)

        elif self.path.startswith('/api/trigger-suspicious'):
            atype = None
            if '?type=' in self.path:
                atype = self.path.split('?type=')[1]

            if bot and main_event_loop:
                async def _do_suspicious():
                    try:
                        payload = bot.loader.get_suspicious_transaction(anomaly_type=atype, update_timestamp=True)
                        async with aiohttp.ClientSession() as session:
                            async with session.post("http://127.0.0.1:5001/transactions", json=payload) as resp:
                                res_data = await resp.json()
                                if res_data.get("decision") == "ANOMALY" or res_data.get("risk_probability", 0) >= 0.86:
                                    bot.total_anomalies += 1
                                    bot.total_blocked += 1
                                bot.total_sent += 1
                                return res_data
                    except Exception as ex:
                        return {"status": "error", "message": f"{type(ex).__name__}: {str(ex)}"}

                fut = asyncio.run_coroutine_threadsafe(_do_suspicious(), main_event_loop)
                try:
                    res = fut.result(timeout=5.0)
                except Exception as e:
                    res = {"status": "error", "message": f"Future timeout: {type(e).__name__}: {str(e)}"}
            else:
                res = {"status": "error", "message": "Bot or main_event_loop unavailable"}

            self._send_json_response(res)

        elif self.path.startswith('/api/toggle-stream'):
            state = "stop"
            if '?state=' in self.path:
                state = self.path.split('?state=')[1]
            
            if bot:
                bot.running = (state == "start")
            
            self._send_json_response({"status": "ok", "running": bot.running if bot else False})

        elif self.path.startswith('/api/set-tps'):
            try:
                tps = int(self.path.split('=')[1])
                if bot:
                    bot.tps = tps
                self._send_json_response({"status": "ok", "tps": tps})
            except Exception:
                self.send_error(400)

        elif self.path == '/api/stats':
            stats = {
                "totalSent": bot.total_sent if bot else 0,
                "anomalies": bot.total_anomalies if bot else 0,
                "tps": bot.tps if bot else 100
            }
            self._send_json_response(stats)

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass

def run_http_control_server(port=9090):
    handler = ControlPanelHandler
    server = socketserver.ThreadingTCPServer(("", port), handler)
    server.daemon_threads = True
    print(f"\033[96m[Web Control Panel] Simulator Dashboard running on http://localhost:{port}\033[0m")
    server.serve_forever()

def main():
    global main_event_loop
    bot = TransactionSimulatorBot(tps_override=100)
    bot.running = True  # Enable live 100 TPS transaction stream by default
    ControlPanelHandler.bot_instance = bot

    # Start HTTP GUI Server in background thread
    gui_thread = threading.Thread(target=run_http_control_server, daemon=True)
    gui_thread.start()

    try:
        main_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(main_event_loop)
        main_event_loop.run_until_complete(bot.run_simulation())
    except KeyboardInterrupt:
        print("\n[Server] Shutdown requested.")

if __name__ == "__main__":
    main()


