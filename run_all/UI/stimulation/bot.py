#!/usr/bin/env python3
"""
===========================================================================
REAL-TIME PAYMENTS FRAUD DETECTION DASHBOARD
TRANSACTION SIMULATION BOT (100 TPS HIGH-PERFORMANCE ENGINE)
===========================================================================
"""

import os
import sys
import json
import time
import asyncio
import argparse
import signal
from datetime import datetime
from synthetic_dataset_loader import DatasetLoader
from anomaly_engine import AnomalyEngine

# Color terminal formatting
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Optional third-party imports gracefully handled
AIOHTTP_AVAILABLE = False
WEBSOCKETS_AVAILABLE = False
ASYNC_PG_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    pass

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    pass

try:
    import asyncpg
    ASYNC_PG_AVAILABLE = True
except ImportError:
    pass


class TransactionSimulatorBot:
    def __init__(self, config_path: str = "config.json", tps_override: int = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.tps = tps_override or self.config.get("tps", 100)
        self.batch_size = self.config.get("batch_size", 10)

        endpoints = self.config.get("endpoints", {})
        self.http_url = endpoints.get("http_url", "http://localhost:8000/transactions")
        self.ws_server_port = endpoints.get("ws_server_port", 8080)
        self.ws_client_url = endpoints.get("ws_client_url", "ws://localhost:8000/ws/transactions")
        self.postgres_uri = endpoints.get("postgres_uri", "postgresql://postgres:postgres@localhost:5432/upi_fraud_db")

        self.enable_http = endpoints.get("enable_http", False)
        self.enable_ws_server = endpoints.get("enable_ws_server", True)
        self.enable_ws_client = endpoints.get("enable_ws_client", False)
        self.enable_postgres = endpoints.get("enable_postgres", False)

        # Core Engine
        dataset_path = self.config.get("dataset_v3_path", r"c:\Hackathon\Dataset\synthetic_upi_transactions_v3.csv")
        self.loader = DatasetLoader(dataset_path=dataset_path)

        # State and Metrics
        self.running = False
        self.total_sent = 0
        self.total_anomalies = 0
        self.total_blocked = 0
        self.anomaly_counts = {}
        self.connected_ws_clients = set()

        # Performance Tracking
        self.start_time = 0
        self.last_tps_check = 0
        self.tx_count_last_interval = 0
        self.current_actual_tps = 0.0

        # Connection Pool / Sessions
        self.db_pool = None
        self.http_session = None

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"{Colors.WARNING}[Config] Error loading {self.config_path}: {e}{Colors.ENDC}")
        return {}

    async def initialize_connections(self):
        if AIOHTTP_AVAILABLE:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5.0)
            )
            print(f"{Colors.OKCYAN}[HTTP] Client Session initialized targeting: {self.http_url}{Colors.ENDC}")

        if self.enable_postgres and ASYNC_PG_AVAILABLE:
            try:
                self.db_pool = await asyncpg.create_pool(self.postgres_uri, min_size=2, max_size=10)
                print(f"{Colors.OKGREEN}[PostgreSQL] Connected to DB Pool successfully.{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.WARNING}[PostgreSQL] DB Connection failed: {e}{Colors.ENDC}")

    async def close_connections(self):
        if self.http_session:
            await self.http_session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def ws_handler(self, websocket, path=None):
        """Websocket server handler for broadcast stream"""
        self.connected_ws_clients.add(websocket)
        print(f"\n{Colors.OKGREEN}[WebSocket Server] Client connected! Total active clients: {len(self.connected_ws_clients)}{Colors.ENDC}")
        try:
            async for message in websocket:
                pass
        except Exception:
            pass
        finally:
            self.connected_ws_clients.remove(websocket)
            print(f"\n{Colors.WARNING}[WebSocket Server] Client disconnected. Remaining: {len(self.connected_ws_clients)}{Colors.ENDC}")

    async def broadcast_ws(self, payload: dict):
        if not self.connected_ws_clients:
            return

        msg_str = json.dumps(payload)
        stale = set()
        for ws in list(self.connected_ws_clients):
            try:
                await ws.send(msg_str)
            except Exception:
                stale.add(ws)

        for ws in stale:
            self.connected_ws_clients.discard(ws)

    async def dispatch_batch_http(self, batch: list):
        if not self.http_session and AIOHTTP_AVAILABLE:
            try:
                connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=60.0, force_close=False)
                self.http_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(total=5.0)
                )
            except Exception:
                pass

        if self.http_session:
            try:
                # Send raw transaction payloads to FastAPI Backend
                async with self.http_session.post(self.http_url, json=batch) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        preds = data.get("predictions", []) if isinstance(data, dict) else [data]
                        for p in preds:
                            if isinstance(p, dict):
                                if p.get("decision") == "ANOMALY" or p.get("risk_probability", 0) >= 0.91:
                                    self.total_blocked += 1
                                    self.total_anomalies += 1
            except Exception as e:
                pass
        else:
            # Fallback using urllib in executor
            loop = asyncio.get_running_loop()
            def _send():
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        self.http_url,
                        data=json.dumps(batch).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode('utf-8'))
                            preds = data.get("predictions", []) if isinstance(data, dict) else [data]
                            for p in preds:
                                if isinstance(p, dict):
                                    if p.get("decision") == "ANOMALY" or p.get("risk_probability", 0) >= 0.91:
                                        self.total_blocked += 1
                                        self.total_anomalies += 1
                except Exception:
                    pass
            await loop.run_in_executor(None, _send)

    async def trigger_single_normal(self) -> dict:
        """Fetch a normal transaction from V3 dataset and send raw payload to Backend ML API."""
        raw_payload = self.loader.get_normal_transaction(update_timestamp=True)
        return await self._send_single_raw_transaction(raw_payload)

    async def trigger_single_suspicious(self, anomaly_type: str = None) -> dict:
        """Fetch a suspicious transaction from V3 dataset and send raw payload to Backend ML API."""
        raw_payload = self.loader.get_suspicious_transaction(anomaly_type=anomaly_type, update_timestamp=True)
        return await self._send_single_raw_transaction(raw_payload)

    async def _send_single_raw_transaction(self, raw_payload: dict) -> dict:
        self.total_sent += 1
        loop = asyncio.get_running_loop()
        def _sync_send():
            try:
                import urllib.request
                req = urllib.request.Request(
                    self.http_url,
                    data=json.dumps(raw_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        res_data = json.loads(resp.read().decode('utf-8'))
                        if res_data.get("decision") == "ANOMALY" or res_data.get("risk_probability", 0) >= 0.91:
                            self.total_anomalies += 1
                            self.total_blocked += 1
                        return res_data
            except Exception as ex:
                return {"status": "error", "message": str(ex)}
            return {"status": "sent", "raw_payload": raw_payload}

        return await loop.run_in_executor(None, _sync_send)

    def generate_single_transaction(self) -> dict:
        return self.loader.get_next_raw_transaction(update_timestamp=True)

    async def run_simulation(self, duration_sec: int = 0):
        self.running = True
        self.start_time = time.time()
        self.last_tps_check = time.time()
        self.tx_count_last_interval = 0

        print(f"\n{Colors.BOLD}{Colors.HEADER}========================================================================={Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN} STARTING TRANSACTION SIMULATION BOT — TARGET: {self.tps} TPS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}========================================================================={Colors.ENDC}\n")

        # Start WebSocket Server if enabled and library present
        ws_server = None
        if self.enable_ws_server and WEBSOCKETS_AVAILABLE:
            try:
                ws_server = await websockets.serve(self.ws_handler, "0.0.0.0", self.ws_server_port)
                print(f"{Colors.OKGREEN}[WebSocket Broadcast Server] Running on ws://localhost:{self.ws_server_port}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.WARNING}[WebSocket Server] Could not start server: {e}{Colors.ENDC}")

        await self.initialize_connections()

        target_interval = 1.0 / self.tps if self.tps > 0 else 0.01
        batch_queue = []

        batch_queue = []
        last_tps_governor_time = time.perf_counter()
        emitted_in_sec = 0

        try:
            while self.running:
                now_perf = time.perf_counter()
                time_delta = now_perf - last_tps_governor_time

                # Token bucket / dynamic governor
                allowed_this_sec = int(self.tps * time_delta)
                if allowed_this_sec <= emitted_in_sec:
                    await asyncio.sleep(0.001)
                    continue

                items_to_emit = min(50, allowed_this_sec - emitted_in_sec)
                for _ in range(items_to_emit):
                    if not self.running:
                        break

                    payload = self.generate_single_transaction()
                    self.total_sent += 1
                    self.tx_count_last_interval += 1
                    emitted_in_sec += 1

                    if self.enable_ws_server and self.connected_ws_clients:
                        asyncio.create_task(self.broadcast_ws({"transaction": payload}))

                    # Add raw payload to batch queue
                    batch_queue.append(payload)
                    if len(batch_queue) >= max(10, self.batch_size):
                        current_batch = batch_queue[:]
                        batch_queue.clear()
                        asyncio.create_task(self.dispatch_batch_http(current_batch))

                # Reset governor interval every second
                if time_delta >= 1.0:
                    last_tps_governor_time = now_perf
                    emitted_in_sec = 0

                # Stats & Console Refresh every 0.5s
                now = time.time()
                elapsed_check = now - self.last_tps_check
                if elapsed_check >= 0.5:
                    self.current_actual_tps = self.tx_count_last_interval / elapsed_check
                    self.last_tps_check = now
                    self.tx_count_last_interval = 0
                    self.print_dashboard_status()

                if duration_sec > 0 and (now - self.start_time) >= duration_sec:
                    print(f"\n{Colors.OKGREEN}[Bot] Target duration of {duration_sec}s reached. Stopping simulation.{Colors.ENDC}")
                    break

        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            await self.close_connections()
            if ws_server:
                ws_server.close()
                await ws_server.wait_closed()
            self.print_final_summary()

    def print_dashboard_status(self):
        elapsed = time.time() - self.start_time
        sys.stdout.write(
            f"\r{Colors.BOLD}[SIMULATOR]{Colors.ENDC} "
            f"Sent: {Colors.OKGREEN}{self.total_sent:,}{Colors.ENDC} | "
            f"Target: {Colors.OKCYAN}{self.tps} TPS{Colors.ENDC} | "
            f"Actual: {Colors.BOLD}{Colors.OKGREEN}{self.current_actual_tps:.1f} TPS{Colors.ENDC} | "
            f"Anomalies: {Colors.WARNING}{self.total_anomalies:,}{Colors.ENDC} | "
            f"Blocked: {Colors.FAIL}{self.total_blocked:,}{Colors.ENDC} | "
            f"WS Clients: {len(self.connected_ws_clients)} | "
            f"Elapsed: {int(elapsed)}s "
        )
        sys.stdout.flush()

    def print_final_summary(self):
        elapsed = max(0.001, time.time() - self.start_time)
        avg_tps = self.total_sent / elapsed

        print(f"\n\n{Colors.BOLD}{Colors.HEADER}========================================================================={Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN} SIMULATION SUMMARY & LAYER 2 ANOMALY BENCHMARK{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}========================================================================={Colors.ENDC}")
        print(f" Total Transactions Processed : {self.total_sent:,}")
        print(f" Total Time Elapsed           : {elapsed:.2f} seconds")
        print(f" Average Throughput           : {Colors.BOLD}{Colors.OKGREEN}{avg_tps:.2f} TPS{Colors.ENDC}")
        print(f" Total Flagged Anomalies      : {self.total_anomalies:,} ({(self.total_anomalies/max(1, self.total_sent))*100:.2f}%)")
        print(f" Total Blocked Transactions   : {self.total_blocked:,}")
        print("\n--- ANOMALY TYPE BREAKDOWN ---")
        for k, v in sorted(self.anomaly_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (v / max(1, self.total_anomalies)) * 100
            print(f"  • {k:<25}: {v:>6} ({pct:>5.1f}%)")
        print(f"{Colors.BOLD}{Colors.HEADER}========================================================================={Colors.ENDC}\n")


def main():
    parser = argparse.ArgumentParser(description="Real-Time Payments Fraud Detection Simulator Bot (100 TPS Engine)")
    parser.add_argument("--tps", type=int, default=100, help="Target Transactions Per Second (Default: 100)")
    parser.add_argument("--duration", type=int, default=0, help="Duration to run in seconds (0 = run indefinitely)")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json file")
    args = parser.parse_args()

    bot = TransactionSimulatorBot(config_path=args.config, tps_override=args.tps)

    def signal_handler(sig, frame):
        print(f"\n{Colors.WARNING}[Signal] Shutdown received. Stopping simulator...{Colors.ENDC}")
        bot.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(bot.run_simulation(duration_sec=args.duration))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
