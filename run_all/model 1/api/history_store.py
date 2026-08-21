import threading
from typing import Dict, List, Optional
from datetime import datetime


class HistoryStore:
    """
    In-memory thread-safe store for user transaction histories.
    Used for real-time feature engineering during API inference.
    """

    def __init__(self, max_records_per_user: int = 100):
        self._store: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()
        self.max_records_per_user = max_records_per_user

    def get_user_history(self, user_id: str) -> List[dict]:
        with self._lock:
            # Return shallow copy of user history list sorted by timestamp
            records = self._store.get(user_id, [])
            return sorted(records, key=lambda x: x["timestamp"])

    def add_user_transaction(self, user_id: str, record: dict) -> None:
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []
            
            # Ensure timestamp is offset-naive datetime
            rec = dict(record)
            ts = rec.get("timestamp")
            if isinstance(ts, str):
                rec["timestamp"] = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            elif isinstance(ts, datetime):
                rec["timestamp"] = ts.replace(tzinfo=None)
            else:
                rec["timestamp"] = datetime.now().replace(tzinfo=None)
                
            self._store[user_id].append(rec)
            
            # Keep history bounded for efficiency
            if len(self._store[user_id]) > self.max_records_per_user:
                self._store[user_id] = sorted(self._store[user_id], key=lambda x: x["timestamp"])[-self.max_records_per_user:]

    def clear(self, user_id: Optional[str] = None) -> None:
        with self._lock:
            if user_id:
                self._store.pop(user_id, None)
            else:
                self._store.clear()


# Global singleton instance
history_store = HistoryStore()
