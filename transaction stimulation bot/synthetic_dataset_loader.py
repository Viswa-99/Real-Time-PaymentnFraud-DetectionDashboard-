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
    def __init__(self, zip_path: str, csv_filename: str = "synthetic_upi_transactions_improved.csv"):
        self.zip_path = os.path.abspath(zip_path)
        self.csv_filename = csv_filename
        self.zip_file = None
        self.csv_stream = None
        self.reader = None
        self.counter = 0
        self._init_reader()

    def _init_reader(self):
        if not os.path.exists(self.zip_path):
            # Fallback path check
            alt_path = os.path.join(os.path.dirname(__file__), "..", "synthetic_upi_transactions_improved.zip")
            if os.path.exists(alt_path):
                self.zip_path = os.path.abspath(alt_path)
            else:
                print(f"[DatasetLoader] Warning: Zip file not found at {self.zip_path}. Using pure synthetic mode.")
                return

        try:
            self.zip_file = zipfile.ZipFile(self.zip_path, 'r')
            self.csv_stream = self.zip_file.open(self.csv_filename)
            lines = (line.decode('utf-8') for line in self.csv_stream)
            self.reader = csv.DictReader(lines)
            print(f"[DatasetLoader] Successfully loaded dataset: {self.zip_path}")
        except Exception as e:
            print(f"[DatasetLoader] Error opening zip/csv dataset: {e}")
            self.reader = None

    def get_next_raw_row(self) -> dict:
        if self.reader is None:
            return None

        try:
            row = next(self.reader)
            self.counter += 1
            return row
        except StopIteration:
            # Re-open stream for continuous looping
            print("[DatasetLoader] Reached end of dataset. Looping back to beginning...")
            self._close()
            self._init_reader()
            if self.reader:
                try:
                    return next(self.reader)
                except Exception:
                    return None
            return None
        except Exception as e:
            print(f"[DatasetLoader] Read error: {e}")
            return None

    def get_next_formatted_transaction(self, update_timestamp: bool = True) -> dict:
        raw = self.get_next_raw_row()
        if not raw:
            return self._generate_fallback_synthetic()

        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y-%m-%d %H:%M:%S") if update_timestamp else raw.get("timestamp", "")
        self.counter += 1

        # Format raw dataset into standard UPI Transaction Object
        txn = {
            "transaction_id": f"TXN_{self.counter:09d}",
            "user_id": raw.get("user_id", f"USR_{random.randint(10000, 99999)}"),
            "account_id": raw.get("account_id", f"ACC_{random.randint(10000, 99999)}"),
            "timestamp": ts_str,
            "amount": safe_float(raw.get("amount"), 100.0),
            "currency": raw.get("currency", "INR"),
            "sender_id": raw.get("sender_id", f"ACC_{random.randint(10000, 99999)}"),
            "sender_type": raw.get("sender_type", "PERSON"),
            "receiver_id": raw.get("receiver_id", f"REC_{random.randint(10000, 99999)}"),
            "receiver_name": raw.get("receiver_name", "MERCHANT"),
            "receiver_type": raw.get("receiver_type", "MERCHANT"),
            "merchant_id": raw.get("merchant_id", "MRC_001"),
            "merchant_category": raw.get("merchant_category", "Retail"),
            "transaction_type": raw.get("transaction_type", "PURCHASE"),
            "payment_method": raw.get("payment_method", "UPI"),
            "location_latitude": safe_float(raw.get("location_latitude"), 17.385),
            "location_longitude": safe_float(raw.get("location_longitude"), 78.4867),
            "location_region": raw.get("location_region", "South_Region"),
            "device_id": raw.get("device_id", f"DEV_{random.randint(1000, 9999)}"),
            "device_type": raw.get("device_type", "Android"),
            "os": raw.get("os", "Android 14"),
            "ip_address_simulated": raw.get("ip_address_simulated", "49.205.12.4"),
            "is_new_device": safe_int(raw.get("is_new_device")),
            "is_new_receiver": safe_int(raw.get("is_new_receiver")),
            "is_new_merchant": safe_int(raw.get("is_new_merchant")),
            "distance_from_usual_location": safe_float(raw.get("distance_from_usual_location")),
            "is_anomaly": safe_int(raw.get("is_anomaly")),
            "anomaly_type": raw.get("anomaly_type", "NONE"),
            "anomaly_severity": raw.get("anomaly_severity", "NONE"),
            "distance_from_previous_transaction": safe_float(raw.get("distance_from_previous_transaction")),
            "time_since_last_transaction_seconds": safe_float(raw.get("time_since_last_transaction_seconds")),
            "implied_travel_speed_kmph": safe_float(raw.get("implied_travel_speed_kmph")),
            "user_history_count": safe_int(raw.get("user_history_count"))
        }

        return txn


    def _generate_fallback_synthetic(self) -> dict:
        self.counter += 1
        now = datetime.now(timezone.utc)
        return {
            "transaction_id": f"TXN_{self.counter:09d}",
            "user_id": f"USR_{random.randint(10000, 99999)}",
            "account_id": f"ACC_{random.randint(10000, 99999)}",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": round(random.uniform(50, 5000), 2),
            "currency": "INR",
            "sender_id": f"ACC_{random.randint(10000, 99999)}",
            "sender_type": "PERSON",
            "receiver_id": f"REC_{random.randint(10000, 99999)}",
            "receiver_name": random.choice(["Swiggy", "Flipkart", "Amazon", "BigBasket", "Zomato"]),
            "receiver_type": "MERCHANT",
            "merchant_id": f"MRC_{random.randint(1000, 9999)}",
            "merchant_category": random.choice(["Food", "Retail", "Travel", "Electronics"]),
            "transaction_type": "PURCHASE",
            "payment_method": "UPI",
            "location_latitude": 17.385,
            "location_longitude": 78.4867,
            "location_region": "South_Region",
            "device_id": f"DEV_{random.randint(1000, 9999)}",
            "device_type": "Android",
            "os": "Android 14",
            "ip_address_simulated": f"49.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "is_new_device": 0,
            "is_new_receiver": 0,
            "is_new_merchant": 0,
            "distance_from_usual_location": 2.5,
            "is_anomaly": 0,
            "anomaly_type": "NONE",
            "anomaly_severity": "NONE",
            "distance_from_previous_transaction": 0.5,
            "time_since_last_transaction_seconds": 3600.0,
            "implied_travel_speed_kmph": 15.0,
            "user_history_count": 42
        }

    def _close(self):
        try:
            if self.csv_stream:
                self.csv_stream.close()
            if self.zip_file:
                self.zip_file.close()
        except Exception:
            pass

    def __del__(self):
        self._close()
