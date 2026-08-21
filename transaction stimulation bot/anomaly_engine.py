import random
import time
from datetime import datetime, timezone

# Layer 2 Anomaly Specifications & Probability Generators
ANOMALY_SPECS = {
    "COMBINED_ANOMALY": {
        "mean_risk": 0.9881, "median_risk": 0.9893, "std_risk": 0.005,
        "reasons": ["Multiple anomalies detected: Device + Location + Amount + High Velocity"],
        "severity": "CRITICAL"
    },
    "HIGH_VELOCITY": {
        "mean_risk": 0.8870, "median_risk": 0.9895, "std_risk": 0.08,
        "reasons": ["High velocity: 12 transactions in 3 minutes exceeding user baseline"],
        "severity": "HIGH"
    },
    "NEW_DEVICE": {
        "mean_risk": 0.9188, "median_risk": 0.9352, "std_risk": 0.04,
        "reasons": ["Transaction initiated from unrecognized new device fingerprint"],
        "severity": "HIGH"
    },
    "UNUSUAL_AMOUNT": {
        "mean_risk": 0.8066, "median_risk": 0.9253, "std_risk": 0.12,
        "reasons": ["Transaction amount is 9.4x higher than standard user ticket size"],
        "severity": "HIGH"
    },
    "REPEATED_TRANSACTION": {
        "mean_risk": 0.6318, "median_risk": 0.9111, "std_risk": 0.15,
        "reasons": ["Identical payment amount repeated within 45 seconds"],
        "severity": "MEDIUM"
    },
    "BEHAVIORAL_DRIFT": {
        "mean_risk": 0.4616, "median_risk": 0.3952, "std_risk": 0.10,
        "reasons": ["Gradual behavioral shift from normal category spending pattern"],
        "severity": "MEDIUM"
    },
    "UNUSUAL_LOCATION": {
        "mean_risk": 0.8270, "median_risk": 0.8644, "std_risk": 0.09,
        "reasons": ["Impossible travel: Geographic displacement of 650km in 6 minutes"],
        "severity": "HIGH"
    },
    "MULTIPLE_NEW_MERCHANTS": {
        "mean_risk": 0.3780, "median_risk": 0.3487, "std_risk": 0.08,
        "reasons": ["Sequential rapid transactions across multiple newly added merchants"],
        "severity": "MEDIUM"
    },
    "NEW_RECEIVER": {
        "mean_risk": 0.4551, "median_risk": 0.4559, "std_risk": 0.07,
        "reasons": ["First transaction sent to unknown non-verified VPA receiver"],
        "severity": "LOW"
    },
    "UNUSUAL_TIME": {
        "mean_risk": 0.3729, "median_risk": 0.3722, "std_risk": 0.06,
        "reasons": ["Transaction attempt outside normal active user timezone hours (03:15 AM)"],
        "severity": "LOW"
    }
}

CITIES = ["Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi", "Pune", "Kolkata"]

class AnomalyEngine:
    def __init__(self, anomaly_distribution: dict = None):
        self.anomaly_distribution = anomaly_distribution or {
            "COMBINED_ANOMALY": 0.0019,
            "HIGH_VELOCITY": 0.0155,
            "NEW_DEVICE": 0.0021,
            "UNUSUAL_AMOUNT": 0.0020,
            "REPEATED_TRANSACTION": 0.0045,
            "BEHAVIORAL_DRIFT": 0.0020,
            "UNUSUAL_LOCATION": 0.0019,
            "MULTIPLE_NEW_MERCHANTS": 0.0018,
            "NEW_RECEIVER": 0.0023,
            "UNUSUAL_TIME": 0.0020,
            "NONE": 0.9639
        }

    def sample_anomaly_type(self) -> str:
        r = random.random()
        cumulative = 0.0
        for atype, prob in self.anomaly_distribution.items():
            cumulative += prob
            if r <= cumulative:
                return atype
        return "NONE"

    def calculate_risk_probability(self, anomaly_type: str, raw_prob: float = None) -> float:
        if anomaly_type == "NONE":
            # Normal transactions low risk (min ~0.045, 50% ~0.24, 75% ~0.35)
            return round(min(0.44, max(0.045, random.gauss(0.22, 0.08))), 4)

        spec = ANOMALY_SPECS.get(anomaly_type)
        if not spec:
            return 0.5000

        prob = random.gauss(spec["mean_risk"], spec["std_risk"])
        # Enforce realistic bounds [0.05, 0.99]
        return round(min(0.9905, max(0.05, prob)), 4)

    def apply_anomaly_constraints(self, txn: dict, forced_anomaly: str = None) -> dict:
        anomaly_type = forced_anomaly or txn.get("anomaly_type")
        if not anomaly_type or anomaly_type == "NONE":
            # Randomly sample based on Layer 2 distribution if missing
            anomaly_type = self.sample_anomaly_type()

        txn["anomaly_type"] = anomaly_type
        risk_prob = self.calculate_risk_probability(anomaly_type)
        risk_score = round(risk_prob * 100.0, 2)
        txn["risk_probability"] = risk_prob
        txn["risk_score"] = risk_score

        if anomaly_type == "NONE":
            txn["is_anomaly"] = 0
            txn["anomaly_severity"] = "NONE"
            txn["status"] = "SAFE" if risk_score < 45 else ("REVIEW" if risk_score < 70 else "SUSPICIOUS")
            return txn

        txn["is_anomaly"] = 1
        spec = ANOMALY_SPECS.get(anomaly_type, {
            "severity": "HIGH", "reasons": ["Detected anomalous transaction pattern"]
        })
        txn["anomaly_severity"] = spec["severity"]

        # Adjust status based on risk score
        if risk_score >= 85:
            txn["status"] = "BLOCKED"
        elif risk_score >= 70:
            txn["status"] = "SUSPICIOUS"
        elif risk_score >= 45:
            txn["status"] = "REVIEW"
        else:
            txn["status"] = "SAFE"

        # Specific field mutations based on anomaly constraint
        if anomaly_type == "UNUSUAL_AMOUNT":
            txn["amount"] = round(txn["amount"] * random.uniform(8.0, 15.0), 2)
        elif anomaly_type == "NEW_DEVICE":
            txn["is_new_device"] = 1
            txn["device_id"] = f"DEV_NEW_{random.randint(1000, 9999)}"
        elif anomaly_type == "UNUSUAL_LOCATION":
            txn["distance_from_usual_location"] = round(random.uniform(400.0, 1200.0), 2)
            txn["distance_from_previous_transaction"] = round(random.uniform(500.0, 900.0), 2)
            txn["time_since_last_transaction_seconds"] = round(random.uniform(120.0, 400.0), 2)
            txn["implied_travel_speed_kmph"] = round(random.uniform(2500.0, 5000.0), 2)
        elif anomaly_type == "HIGH_VELOCITY":
            txn["time_since_last_transaction_seconds"] = round(random.uniform(1.0, 5.0), 2)
            txn["user_history_count"] = random.randint(25, 60)
        elif anomaly_type == "COMBINED_ANOMALY":
            txn["amount"] = round(txn["amount"] * 12.0, 2)
            txn["is_new_device"] = 1
            txn["distance_from_usual_location"] = 750.0
            txn["implied_travel_speed_kmph"] = 4500.0

        return txn

    def build_lovable_frontend_payload(self, txn: dict) -> dict:
        """Converts internal/dataset transaction dictionary into Lovable Frontend JSON Schema"""
        ts_ms = int(time.time() * 1000)
        dt = datetime.now()
        time_str = dt.strftime("%H:%M:%S")

        risk_score = float(txn.get("risk_score", 15.0))
        status = txn.get("status") or ("BLOCKED" if risk_score >= 85 else ("SUSPICIOUS" if risk_score >= 70 else ("REVIEW" if risk_score >= 45 else "SAFE")))
        anomaly_type = txn.get("anomaly_type", "NONE")
        spec = ANOMALY_SPECS.get(anomaly_type, {})
        reason = spec.get("reasons", ["Normal transaction"])[0] if anomaly_type != "NONE" else None

        location_city = random.choice(CITIES)

        # Base transaction
        fe_txn = {
            "id": txn.get("transaction_id"),
            "timestamp": ts_ms,
            "time": time_str,
            "userId": txn.get("user_id"),
            "merchant": txn.get("receiver_name") or txn.get("merchant_id") or "UPI Merchant",
            "amount": float(txn.get("amount", 0)),
            "location": location_city,
            "device": "New Device" if txn.get("is_new_device") == 1 else "Known Device",
            "deviceKnown": txn.get("is_new_device") != 1,
            "ip": txn.get("ip_address_simulated", "49.205.12.4"),
            "paymentMethod": txn.get("payment_method", "UPI"),
            "riskScore": risk_score,
            "status": status,
            "reason": reason,
            # Complete raw payload included so backend/replica DB receives full dataset features
            "raw_dataset_features": txn
        }

        # Rich Risk Breakdown Object
        fe_risk = {
            "transactionId": txn.get("transaction_id"),
            "score": risk_score,
            "probability": round(float(txn.get("risk_probability", risk_score/100.0)) * 100.0, 1),
            "level": "CRITICAL" if risk_score >= 85 else ("HIGH" if risk_score >= 70 else ("MEDIUM" if risk_score >= 45 else "LOW")),
            "mlProbability": round(float(txn.get("risk_probability", 0.2)) * 100.0, 1),
            "anomalyScore": round(risk_score * 0.95, 1),
            "ruleScore": round(risk_score * 0.9, 1),
            "factors": [
                {"label": "Anomaly Type", "weight": risk_score, "detail": anomaly_type},
                {"label": "Amount Deviation", "weight": min(95, risk_score * 0.9), "detail": f"Amount ₹{txn.get('amount')}"},
                {"label": "Device Risk", "weight": 85 if txn.get("is_new_device") == 1 else 15, "detail": "New Device" if txn.get("is_new_device") == 1 else "Known Device"}
            ]
        }

        # Fraud Alert Object if flagged
        fe_alert = None
        if status in ["BLOCKED", "SUSPICIOUS"]:
            fe_alert = {
                "id": f"FA-{random.randint(10000, 99999)}",
                "type": anomaly_type.replace("_", " ").title(),
                "severity": fe_risk["level"],
                "transactionId": txn.get("transaction_id"),
                "userId": txn.get("user_id"),
                "amount": float(txn.get("amount", 0)),
                "detectedAt": time_str,
                "ago": "Just now",
                "reason": reason or "Flagged by ML Model Replica Engine",
                "reasons": spec.get("reasons", ["Anomaly detected"]),
                "status": "Open",
                "riskScore": risk_score,
                "probability": fe_risk["probability"],
                "recommendedAction": "Block transaction and initiate verification." if risk_score >= 85 else "Review account activity."
            }

        return {
            "transaction": fe_txn,
            "risk_score_details": fe_risk,
            "alert": fe_alert,
            "raw_dataset": txn
        }
