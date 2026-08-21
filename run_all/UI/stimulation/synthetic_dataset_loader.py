import os
import zipfile
import csv
import time
import random
from datetime import datetime, timezone

def safe_float(val, default=0.0) -> float:
    try:
        if val is None or val == '':
            return float(default)
        return float(val)
    except (ValueError, TypeError):
        return float(default)

def safe_int(val, default=0) -> int:
    try:
        if val is None or val == '':
            return int(default)
        return int(float(val))
    except (ValueError, TypeError):
        return int(default)

class DatasetLoader:
    def __init__(self, dataset_path: str = r"c:\Hackathon\Dataset\synthetic_upi_transactions_v3.csv"):
        self.dataset_path = os.path.abspath(dataset_path)
        self.rows = []
        self.counter = 0
        self.normal_indices = []
        self.suspicious_indices = []
        self._init_data()

    def _init_data(self):
        # 1. Try direct CSV path
        if os.path.exists(self.dataset_path) and self.dataset_path.endswith('.csv'):
            try:
                with open(self.dataset_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.rows = list(reader)
                print(f"[DatasetLoader] Successfully loaded {len(self.rows):,} rows directly from CSV: {self.dataset_path}")
            except Exception as e:
                print(f"[DatasetLoader] Error reading CSV {self.dataset_path}: {e}")

        # 2. Try Zip file if direct CSV failed or not found
        if not self.rows:
            zip_paths = [
                r"c:\Hackathon\Dataset\upi_synthetic_dataset.zip",
                os.path.join(os.path.dirname(__file__), "..", "synthetic_upi_transactions_improved.zip")
            ]
            for zp in zip_paths:
                if os.path.exists(zp):
                    try:
                        with zipfile.ZipFile(zp, 'r') as zf:
                            csv_names = [name for name in zf.namelist() if name.endswith('.csv')]
                            if csv_names:
                                with zf.open(csv_names[0]) as csv_file:
                                    lines = (line.decode('utf-8') for line in csv_file)
                                    reader = csv.DictReader(lines)
                                    self.rows = list(reader)
                                print(f"[DatasetLoader] Successfully loaded {len(self.rows):,} rows from Zip: {zp}")
                                break
                    except Exception as e:
                        print(f"[DatasetLoader] Error loading zip {zp}: {e}")

        # Classify row indices for quick lookup
        if self.rows:
            for idx, r in enumerate(self.rows):
                if safe_int(r.get("is_anomaly")) == 1 or r.get("anomaly_type", "NONE") != "NONE":
                    self.suspicious_indices.append(idx)
                else:
                    self.normal_indices.append(idx)
            print(f"[DatasetLoader] Indexed dataset: {len(self.normal_indices):,} Normal, {len(self.suspicious_indices):,} Suspicious transactions.")

    def format_raw_payload(self, raw: dict, update_timestamp: bool = True) -> dict:
        """
        Strips ground truth fields (is_anomaly, anomaly_type, anomaly_severity)
        and returns clean raw transaction JSON object for ML ingestion.
        """
        self.counter += 1
        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y-%m-%dT%H:%M:%S") if update_timestamp else raw.get("timestamp", now.strftime("%Y-%m-%dT%H:%M:%S"))

        raw_payload = {
            "transaction_id": raw.get("transaction_id") or f"TXN_{self.counter:09d}",
            "user_id": raw.get("user_id") or f"USR_{random.randint(10000, 99999)}",
            "account_id": raw.get("account_id") or f"ACC_{random.randint(10000, 99999)}",
            "timestamp": ts_str,
            "amount": safe_float(raw.get("amount"), 100.0),
            "currency": raw.get("currency", "INR"),
            "sender_id": raw.get("sender_id") or raw.get("user_id") or f"ACC_{random.randint(10000, 99999)}",
            "sender_type": raw.get("sender_type", "PERSON"),
            "receiver_id": raw.get("receiver_id") if raw.get("receiver_id") != '' else None,
            "receiver_name": raw.get("receiver_name", "MERCHANT"),
            "receiver_type": raw.get("receiver_type", "MERCHANT"),
            "merchant_id": raw.get("merchant_id") if raw.get("merchant_id") != '' else None,
            "merchant_category": raw.get("merchant_category", "Retail"),
            "transaction_type": raw.get("transaction_type", "UPI_TRANSFER"),
            "payment_method": raw.get("payment_method", "UPI"),
            "location_latitude": safe_float(raw.get("location_latitude"), 17.385),
            "location_longitude": safe_float(raw.get("location_longitude"), 78.4867),
            "location_region": raw.get("location_region", "South_Region"),
            "device_id": raw.get("device_id") or f"DEV_{random.randint(1000, 9999)}",
            "device_type": raw.get("device_type", "Android"),
            "os": raw.get("os", "Android 14")
        }
        return raw_payload

    def get_next_raw_transaction(self, update_timestamp: bool = True) -> dict:
        """
        Gets next raw transaction, sampling ~4% ground-truth anomalies and 96% normal transactions
        so that live streaming contains realistic threat events detected by the ML engine.
        """
        if not self.rows:
            return self._generate_fallback_raw()

        # Inject realistic ~4% anomaly rate into live stream
        if self.suspicious_indices and random.random() < 0.04:
            idx = random.choice(self.suspicious_indices)
        elif self.normal_indices:
            idx = random.choice(self.normal_indices)
        else:
            idx = self.counter % len(self.rows)

        raw = self.rows[idx]
        return self.format_raw_payload(raw, update_timestamp=update_timestamp)

    def get_normal_transaction(self, update_timestamp: bool = True) -> dict:
        """
        Selects a clean NORMAL transaction from ground truth (is_anomaly == 0).
        """
        if not self.normal_indices:
            return self._generate_fallback_raw(is_suspicious=False)

        idx = random.choice(self.normal_indices)
        raw = self.rows[idx]
        return self.format_raw_payload(raw, update_timestamp=update_timestamp)

    def get_suspicious_transaction(self, anomaly_type: str = None, update_timestamp: bool = True) -> dict:
        """
        Selects a ground-truth SUSPICIOUS transaction (is_anomaly == 1).
        Optionally filters by anomaly_type (e.g. HIGH_VELOCITY, UNUSUAL_LOCATION, NEW_DEVICE, BEHAVIORAL_DRIFT).
        """
        if not self.suspicious_indices:
            return self._generate_fallback_raw(is_suspicious=True)

        if anomaly_type:
            matching = [
                i for i in self.suspicious_indices
                if self.rows[i].get("anomaly_type", "").upper() == anomaly_type.upper()
            ]
            if matching:
                raw = self.rows[random.choice(matching)]
                return self.format_raw_payload(raw, update_timestamp=update_timestamp)

        idx = random.choice(self.suspicious_indices)
        raw = self.rows[idx]
        return self.format_raw_payload(raw, update_timestamp=update_timestamp)

    def _generate_fallback_raw(self, is_suspicious: bool = False) -> dict:
        self.counter += 1
        now = datetime.now(timezone.utc)
        amount = round(random.uniform(15000, 45000), 2) if is_suspicious else round(random.uniform(50, 1500), 2)
        return {
            "transaction_id": f"TXN_{self.counter:09d}",
            "user_id": f"USR_{random.randint(10000, 99999)}",
            "account_id": f"ACC_{random.randint(10000, 99999)}",
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "amount": amount,
            "currency": "INR",
            "sender_id": f"ACC_{random.randint(10000, 99999)}",
            "sender_type": "PERSON",
            "receiver_id": f"REC_{random.randint(10000, 99999)}",
            "receiver_name": "Flipkart" if not is_suspicious else "Unknown Entity",
            "receiver_type": "MERCHANT",
            "merchant_id": f"MRC_{random.randint(1000, 9999)}",
            "merchant_category": "Retail",
            "transaction_type": "UPI_TRANSFER",
            "payment_method": "UPI",
            "location_latitude": 28.6139 if is_suspicious else 17.385,
            "location_longitude": 77.2090 if is_suspicious else 78.4867,
            "location_region": "Delhi" if is_suspicious else "South_Region",
            "device_id": f"DEV_{random.randint(1000, 9999)}",
            "device_type": "iOS" if is_suspicious else "Android",
            "os": "iOS 17" if is_suspicious else "Android 14"
        }

