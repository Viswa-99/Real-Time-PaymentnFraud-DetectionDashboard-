# Transaction Simulation Bot (100 TPS High-Performance Engine)
### Real-Time Payments Fraud Detection Dashboard

This simulation bot generates and dispatches UPI payment transactions at a sustained rate of **100 Transactions Per Second (TPS)** (configurable up to 500+ TPS). It streams data directly from the dataset (`synthetic_upi_transactions_improved.zip`) while dynamically injecting anomaly distributions matching the **ML Layer 2 Error Analysis** constraints.

---

## 🚀 Key Features

1. **100 TPS Async Engine**: Built with zero-lag microsecond rate limiting (`asyncio` in Python, high-throughput loop in Node.js).
2. **Layer 2 Anomaly Constraints**: Enforces exact detection stats for all 10 anomaly types:
   - `COMBINED_ANOMALY` (Mean Risk ~0.9881)
   - `HIGH_VELOCITY` (Mean Risk ~0.8870)
   - `NEW_DEVICE` (Mean Risk ~0.9188)
   - `UNUSUAL_AMOUNT` (Mean Risk ~0.8066)
   - `REPEATED_TRANSACTION` (Mean Risk ~0.6318)
   - `BEHAVIORAL_DRIFT` (Mean Risk ~0.4616)
   - `UNUSUAL_LOCATION` (Mean Risk ~0.8270)
   - `MULTIPLE_NEW_MERCHANTS` (Mean Risk ~0.3780)
   - `NEW_RECEIVER` (Mean Risk ~0.4551)
   - `UNUSUAL_TIME` (Mean Risk ~0.3729)
3. **Multi-Destination Sinks**:
   - **WebSocket Broadcast**: `ws://localhost:8080/ws` for live streaming directly into the Lovable Frontend Dashboard.
   - **HTTP REST Endpoint**: `http://localhost:8000/transactions` (batch POST payloads for backend REST receivers).
   - **PostgreSQL Direct Connector**: Direct async bulk SQL inserts into primary/replica PostgreSQL database tables.
4. **Interactive Web Control Dashboard**: Live browser GUI (`http://localhost:9090`) with speed control sliders and on-demand anomaly injection buttons.

---

## 🛠️ Usage Instructions

### Option 1: Python Engine (Recommended)

Run standard 100 TPS simulation CLI:
```bash
python bot.py --tps 100
```

Run with Web Control Panel & WebSocket Server:
```bash
python server.py
```
* Open `http://localhost:9090` in your web browser to view the interactive control panel!

Options:
- `--tps 100` : Set custom target TPS speed (e.g. 50, 100, 250, 500)
- `--duration 30` : Run simulation for specified duration in seconds (0 = run indefinitely)
- `--config config.json` : Path to custom endpoint & database config

---

### Option 2: Node.js Engine (Zero External Dependencies)

Run using Node.js:
```bash
node bot.js --tps 100
```

---

## ⚙️ Configuration (`config.json`)

To change backend HTTP API, WebSocket, or PostgreSQL connection settings, update `config.json`:

```json
{
  "tps": 100,
  "endpoints": {
    "http_url": "http://localhost:8000/transactions",
    "ws_server_port": 8080,
    "postgres_uri": "postgresql://postgres:postgres@localhost:5432/upi_fraud_db",
    "enable_http": false,
    "enable_ws_server": true,
    "enable_postgres": false
  }
}
```

---

## 📊 Output Schema

The simulator outputs transactions dual-formatted for both ML raw dataset processing and Lovable Frontend rendering:

```json
{
  "transaction": {
    "id": "TXN_000084922",
    "timestamp": 1771171200000,
    "time": "10:42:36",
    "userId": "USR_01024",
    "merchant": "Swiggy Foods",
    "amount": 42000,
    "location": "Chennai",
    "device": "New Device",
    "deviceKnown": false,
    "ip": "49.205.12.4",
    "paymentMethod": "UPI",
    "riskScore": 94.2,
    "status": "BLOCKED",
    "reason": "Impossible travel + amount deviation"
  },
  "risk_score_details": {
    "transactionId": "TXN_000084922",
    "score": 94.2,
    "probability": 96.2,
    "level": "CRITICAL",
    "factors": [ ... ]
  },
  "raw_dataset": { ... }
}
```
