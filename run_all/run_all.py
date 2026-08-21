#!/usr/bin/env python3
"""
===========================================================================
UPI ANOMALY / FRAUD DETECTION SYSTEM — MASTER RUNNER
===========================================================================
Launches and orchestrates all 3 project tiers simultaneously:
  1. ML API Backend (Python FastAPI)    -> http://localhost:5001  (Docs: /docs)
  2. Transaction Simulator (100 TPS)    -> http://localhost:9090  (WS: 8080)
  3. Frontend Dashboard (React/Vite)    -> http://localhost:5173
===========================================================================
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(r"C:\Hackathon")
MODEL_DIR = BASE_DIR / "model 1"
UI_DIR = BASE_DIR / "UI"
STIMULATION_DIR = UI_DIR / "stimulation"

processes = []

def log_stream(name: str, stream):
    for line in iter(stream.readline, ''):
        if line:
            print(f"[{name}] {line.strip()}", flush=True)

def run_service(name: str, cmd: str, cwd: Path):
    print(f"[Launcher] Starting {name}...")
    p = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(p)
    t = threading.Thread(target=log_stream, args=(name, p.stdout), daemon=True)
    t.start()
    return p

def kill_stale_ports():
    ports = [5001, 9090, 8080, 5173, 5174]
    print("[Launcher] Clearing any stale processes on ports:", ports)
    for port in ports:
        try:
            out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True)
            pids = set()
            for line in out.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pids.add(parts[-1])
            for pid in pids:
                if pid and pid != "0":
                    print(f" -> Killing stale PID {pid} listening on port {port}")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def main():
    kill_stale_ports()
    print("=" * 75)
    print("STARTING COMPLETE UPI ANOMALY DETECTION SYSTEM (ML + BACKEND + FRONTEND)")
    print("=" * 75)
    print(f"Base Directory: {BASE_DIR}")
    print("Services to run:")
    print("  1. ML API Backend (FastAPI)     : http://localhost:5001")
    print("  2. Transaction Simulator        : http://localhost:9090")
    print("  3. Frontend UI Dashboard        : http://localhost:5173")
    print("=" * 75)

    # 1. Start ML API Backend
    backend_cmd = f'"{sys.executable}" -m uvicorn api.main:app --host 127.0.0.1 --port 5001'
    run_service("FASTAPI ML API", backend_cmd, MODEL_DIR)

    time.sleep(2)

    # 2. Start Simulator & Web Control Panel
    sim_cmd = f'"{sys.executable}" server.py'
    run_service("100 TPS SIMULATOR", sim_cmd, STIMULATION_DIR)

    time.sleep(2)

    # 3. Start React Frontend Dashboard
    ui_cmd = "cmd /c npm run dev"
    run_service("FRONTEND UI", ui_cmd, UI_DIR)

    print("\n" + "=" * 75)
    print("ALL SERVICES RUNNING SUCCESSFULLY!")
    print("ML API Swagger Docs      : http://localhost:5001/docs")
    print("Simulator Control Panel  : http://localhost:9090")
    print("Live UI Dashboard        : http://localhost:5173")
    print("=" * 75 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down all services...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        print("[Launcher] Shutdown complete.")

if __name__ == "__main__":
    main()
