import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from .schemas import TransactionRequest


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in km between two lat/lon points."""
    try:
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return float(R * c)
    except Exception:
        return 0.0


def _to_naive_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, (int, float)):
        if val > 1e11:
            return datetime.fromtimestamp(val / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        return datetime.fromtimestamp(val, tz=timezone.utc).replace(tzinfo=None)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass
    return datetime.now().replace(tzinfo=None)


def extract_raw_features(
    req: TransactionRequest,
    history: List[dict]
) -> Dict[str, Any]:
    """
    Extract all behavioral, transactional, and velocity features for a raw transaction
    given the user's prior transaction history.
    """
    ts = _to_naive_dt(req.timestamp)
    amount = float(req.amount)
    user_id = req.user_id or req.sender_id or "USER_DEFAULT"

    # 1. Basic temporal
    hour = int(ts.hour)
    day_of_week = int(ts.weekday())
    is_weekend = 1 if day_of_week >= 5 else 0
    log_amount = float(np.log1p(amount))

    # 2. Historical user statistics
    history_count = len(history)
    has_user_amount_history = 1 if history_count > 0 else 0

    if history_count > 0:
        amounts = [float(x["amount"]) for x in history]
        user_avg_amount = float(np.mean(amounts))
        
        # Population variance matching offline feature engineering
        if history_count >= 2:
            amount_sq = [a ** 2 for a in amounts]
            var_before = max(0.0, (sum(amount_sq) / history_count) - (user_avg_amount ** 2))
            user_std_amount = float(math.sqrt(var_before))
        else:
            user_std_amount = 0.0

        amount_to_user_avg = float(amount / user_avg_amount) if user_avg_amount > 0 else 0.0

        if history_count >= 2 and user_std_amount >= 1e-6:
            raw_z = (amount - user_avg_amount) / user_std_amount
            amount_zscore = float(np.clip(raw_z, -20.0, 20.0))
        else:
            amount_zscore = 0.0

        prev_tx = history[-1]
        prev_ts = _to_naive_dt(prev_tx["timestamp"])
        time_since_last_tx = max(0.0, float((ts - prev_ts).total_seconds()))

        prev_lat = float(prev_tx.get("location_latitude", req.location_latitude))
        prev_lon = float(prev_tx.get("location_longitude", req.location_longitude))
        distance_from_prev = haversine_distance(prev_lat, prev_lon, req.location_latitude, req.location_longitude)
    else:
        user_avg_amount = 0.0
        user_std_amount = 0.0
        amount_to_user_avg = 0.0
        amount_zscore = 0.0
        time_since_last_tx = 0.0
        distance_from_prev = 0.0

    # Speed calculation
    if time_since_last_tx > 0:
        speed_kmph = (distance_from_prev / time_since_last_tx) * 3600.0
    else:
        speed_kmph = 0.0
    log_travel_speed = float(np.log1p(max(0.0, speed_kmph)))

    # 3. Receiver history
    receiver_id = req.receiver_id
    if receiver_id and str(receiver_id).strip():
        rec_history = [x for x in history if x.get("receiver_id") == receiver_id]
        receiver_tx_count = len(rec_history)
        receiver_seen_before = 1 if receiver_tx_count > 0 else 0
        is_new_receiver = 1 if receiver_tx_count == 0 else 0

        if receiver_tx_count > 0:
            first_rec_ts = _to_naive_dt(rec_history[0]["timestamp"])
            receiver_relationship_age = max(0.0, float((ts - first_rec_ts).total_seconds()))

            last_rec_ts = _to_naive_dt(rec_history[-1]["timestamp"])
            time_since_receiver_last_tx = max(0.0, float((ts - last_rec_ts).total_seconds()))
        else:
            receiver_relationship_age = 0.0
            time_since_receiver_last_tx = 0.0
    else:
        receiver_tx_count = 0
        receiver_seen_before = 0
        is_new_receiver = 0
        receiver_relationship_age = 0.0
        time_since_receiver_last_tx = 0.0

    # 4. Merchant history
    merchant_id = req.merchant_id
    merchant_available = 1 if (merchant_id and str(merchant_id).strip() != "") else 0
    if merchant_available == 1:
        merch_history = [x for x in history if x.get("merchant_id") == merchant_id]
        merchant_tx_count = len(merch_history)
        merchant_seen_before = 1 if merchant_tx_count > 0 else 0
        is_new_merchant = 1 if merchant_tx_count == 0 else 0
    else:
        merchant_tx_count = 0
        merchant_seen_before = 0
        is_new_merchant = 0

    # 5. Device history
    device_id = req.device_id
    if device_id and str(device_id).strip():
        dev_history = [x for x in history if x.get("device_id") == device_id]
        device_tx_count = len(dev_history)
        device_seen_before = 1 if device_tx_count > 0 else 0
        is_new_device = 1 if device_tx_count == 0 else 0
    else:
        device_tx_count = 0
        device_seen_before = 0
        is_new_device = 0

    # 6. Velocity windows (prior to current ts)
    t_5m = ts - timedelta(minutes=5)
    t_15m = ts - timedelta(minutes=15)
    t_1h = ts - timedelta(hours=1)
    t_24h = ts - timedelta(hours=24)

    h_5m = [x for x in history if _to_naive_dt(x["timestamp"]) >= t_5m]
    h_15m = [x for x in history if _to_naive_dt(x["timestamp"]) >= t_15m]
    h_1h = [x for x in history if _to_naive_dt(x["timestamp"]) >= t_1h]
    h_24h = [x for x in history if _to_naive_dt(x["timestamp"]) >= t_24h]

    tx_5m = len(h_5m)
    tx_15m = len(h_15m)
    tx_1h = len(h_1h)
    tx_24h = len(h_24h)
    amount_last_1h = float(sum(float(x["amount"]) for x in h_1h))

    # 7. Location features
    dist_usual = float(req.distance_from_usual_location or 0.0)
    user_location_tx_count = history_count
    
    region = req.location_region
    if region:
        user_region_tx_count = len([x for x in history if x.get("location_region") == region])
    else:
        user_region_tx_count = 0

    dist_user_median = abs(dist_usual)
    dist_prev_loc = distance_from_prev
    loc_freq_score = float(1.0 / (1.0 + max(0.0, dist_usual)))

    # 8. V2 Behavioral & Diversity
    recent_5 = history[-5:] if history_count >= 5 else history
    if recent_5:
        recent_avg_5tx = float(np.mean([float(x["amount"]) for x in recent_5]))
    else:
        recent_avg_5tx = 0.0

    historical_avg_amount = user_avg_amount

    if recent_avg_5tx > 0:
        recent_amount_ratio = float(amount / recent_avg_5tx)
    else:
        recent_amount_ratio = 0.0

    recent_tx_count_1h = tx_1h
    recent_tx_count_24h = tx_24h

    if history_count > 0:
        first_ts = _to_naive_dt(history[0]["timestamp"])
        elapsed_days = max(0.0, float((ts - first_ts).total_seconds()) / 86400.0)
        historical_tx_frequency = float(history_count / elapsed_days) if elapsed_days > 0 else 0.0
    else:
        historical_tx_frequency = 0.0

    recent_unique_receivers = len({x["receiver_id"] for x in recent_5 if x.get("receiver_id")})
    historical_unique_receivers = len({x["receiver_id"] for x in history if x.get("receiver_id")})
    recent_unique_merchants = len({x["merchant_id"] for x in recent_5 if x.get("merchant_id")})
    historical_unique_merchants = len({x["merchant_id"] for x in history if x.get("merchant_id")})

    if history and history[-1].get("device_id") and device_id:
        recent_device_changes = 1 if history[-1]["device_id"] != device_id else 0
    else:
        recent_device_changes = 0

    user_receiver_tx_count = receiver_tx_count

    # Entity burst features in windows
    new_receivers_5m = len([x for x in h_5m if x.get("is_new_receiver") == 1])
    new_receivers_15m = len([x for x in h_15m if x.get("is_new_receiver") == 1])
    new_receivers_1h = len([x for x in h_1h if x.get("is_new_receiver") == 1])

    new_merchants_5m = len([x for x in h_5m if x.get("is_new_merchant") == 1 and x.get("merchant_available") == 1])
    new_merchants_15m = len([x for x in h_15m if x.get("is_new_merchant") == 1 and x.get("merchant_available") == 1])
    new_merchants_1h = len([x for x in h_1h if x.get("is_new_merchant") == 1 and x.get("merchant_available") == 1])

    # Dictionary of all extracted features
    extracted = {
        "amount": amount,
        "log_amount": log_amount,
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "user_history_count": history_count,
        "user_avg_amount": user_avg_amount,
        "user_std_amount": user_std_amount,
        "amount_to_user_avg": amount_to_user_avg,
        "amount_zscore": amount_zscore,
        "is_new_receiver": is_new_receiver,
        "receiver_transaction_count": receiver_tx_count,
        "receiver_seen_before": receiver_seen_before,
        "merchant_available": merchant_available,
        "is_new_merchant": is_new_merchant,
        "merchant_transaction_count": merchant_tx_count,
        "merchant_seen_before": merchant_seen_before,
        "is_new_device": is_new_device,
        "device_transaction_count": device_tx_count,
        "device_seen_before": device_seen_before,
        "transactions_last_5min": tx_5m,
        "transactions_last_15min": tx_15m,
        "transactions_last_1hour": tx_1h,
        "transactions_last_24hour": tx_24h,
        "amount_last_1hour": amount_last_1h,
        "distance_from_usual_location": dist_usual,
        "distance_from_previous_transaction": distance_from_prev,
        "time_since_last_transaction_seconds": time_since_last_tx,
        "log_travel_speed": log_travel_speed,
        "has_user_amount_history": has_user_amount_history,
        "recent_avg_amount_5tx": recent_avg_5tx,
        "historical_avg_amount": historical_avg_amount,
        "recent_amount_ratio": recent_amount_ratio,
        "recent_tx_count_1h": recent_tx_count_1h,
        "recent_tx_count_24h": recent_tx_count_24h,
        "historical_tx_frequency": historical_tx_frequency,
        "recent_unique_receivers": recent_unique_receivers,
        "historical_unique_receivers": historical_unique_receivers,
        "recent_unique_merchants": recent_unique_merchants,
        "historical_unique_merchants": historical_unique_merchants,
        "recent_device_changes": recent_device_changes,
        "user_location_transaction_count": user_location_tx_count,
        "user_region_transaction_count": user_region_tx_count,
        "distance_from_user_median_location": dist_user_median,
        "distance_from_previous_location": dist_prev_loc,
        "location_frequency_score": loc_freq_score,
        "user_receiver_transaction_count": user_receiver_tx_count,
        "receiver_relationship_age": receiver_relationship_age,
        "time_since_receiver_last_transaction": time_since_receiver_last_tx,
        "new_receivers_last_5min": new_receivers_5m,
        "new_receivers_last_15min": new_receivers_15m,
        "new_receivers_last_1hour": new_receivers_1h,
        "new_merchants_last_5min": new_merchants_5m,
        "new_merchants_last_15min": new_merchants_15m,
        "new_merchants_last_1hour": new_merchants_1h,
    }
    return extracted


def build_feature_dataframe(
    feature_dict: Dict[str, Any],
    feature_list: List[str]
) -> pd.DataFrame:
    """
    Construct a DataFrame with 1 row containing features ordered strictly according to feature_list.
    Missing features are filled with 0.0.
    """
    row_data = {}
    for col in feature_list:
        val = feature_dict.get(col, 0.0)
        if val is None or not math.isfinite(val):
            val = 0.0
        row_data[col] = float(val)
    
    return pd.DataFrame([row_data], columns=feature_list, dtype=np.float32)
