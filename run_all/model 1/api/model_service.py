import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import HTTPException, status

from .config import (
    LAYER1_MODEL_PATH,
    LAYER1_CONFIG_PATH,
    LAYER2_MODEL_PATH,
    LAYER2_CONFIG_PATH,
    TEST_RESULTS_PATH,
    TEST_FEATURES_PATH,
)
from .schemas import (
    TransactionRequest,
    PredictionResponse,
    TransactionDetails,
    Reason,
)
from .history_store import history_store
from .feature_service import extract_raw_features, build_feature_dataframe
from .reason_engine import generate_reasons

logger = logging.getLogger("upi-ml-api")


class ModelService:
    def __init__(self):
        self.layer1_model: Optional[Any] = None
        self.layer1_config: Optional[Dict[str, Any]] = None
        self.layer2_model: Optional[xgb.XGBClassifier] = None
        self.layer2_config: Optional[Dict[str, Any]] = None
        
        self.demo_test_results: Optional[pd.DataFrame] = None
        self.demo_test_features: Optional[pd.DataFrame] = None
        
        self.is_loaded: bool = False

    def load_models(self) -> None:
        """
        Load ML models and configurations ONCE at startup.
        """
        logger.info("Loading Layer 1 Isolation Forest model...")
        if not LAYER1_MODEL_PATH.exists() or not LAYER1_CONFIG_PATH.exists():
            raise FileNotFoundError(f"Layer 1 files missing at {LAYER1_MODEL_PATH} or {LAYER1_CONFIG_PATH}")
        
        self.layer1_model = joblib.load(LAYER1_MODEL_PATH)
        with open(LAYER1_CONFIG_PATH, "r", encoding="utf-8") as f:
            self.layer1_config = json.load(f)

        logger.info("Loading Layer 2 XGBoost model...")
        if not LAYER2_MODEL_PATH.exists() or not LAYER2_CONFIG_PATH.exists():
            raise FileNotFoundError(f"Layer 2 files missing at {LAYER2_MODEL_PATH} or {LAYER2_CONFIG_PATH}")

        self.layer2_model = xgb.XGBClassifier()
        self.layer2_model.load_model(str(LAYER2_MODEL_PATH))
        with open(LAYER2_CONFIG_PATH, "r", encoding="utf-8") as f:
            self.layer2_config = json.load(f)

        # Pre-load demo test datasets if available
        if TEST_RESULTS_PATH.exists() and TEST_FEATURES_PATH.exists():
            logger.info("Pre-loading demo test datasets...")
            self.demo_test_results = pd.read_parquet(TEST_RESULTS_PATH)
            self.demo_test_features = pd.read_parquet(TEST_FEATURES_PATH)

        self.is_loaded = True
        logger.info("All ML models loaded successfully!")

    def predict(self, req: TransactionRequest) -> PredictionResponse:
        if not self.is_loaded or self.layer1_model is None or self.layer2_model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML models are not loaded or unavailable."
            )

        user_id = req.user_id or req.sender_id or "USER_DEFAULT"

        # 1. Fetch historical transactions for user
        history = history_store.get_user_history(user_id)

        # 2. Extract raw behavioral features
        raw_feats = extract_raw_features(req, history)

        # 3. Construct Layer 1 feature vector dynamically from config
        l1_features = self.layer1_config["features"]
        X_l1 = build_feature_dataframe(raw_feats, l1_features)

        # 4. Compute Layer 1 anomaly score (-score_samples)
        l1_raw = self.layer1_model.score_samples(X_l1.values)[0]
        layer1_anomaly_score = float(-l1_raw)

        # 5. Append Layer 1 anomaly score to feature dict
        raw_feats["layer1_anomaly_score"] = layer1_anomaly_score

        # 6. Construct Layer 2 feature vector dynamically from config
        l2_features = self.layer2_config["features"]
        X_l2 = build_feature_dataframe(raw_feats, l2_features)

        # 7. Compute Layer 2 fraud probability
        risk_probability = float(self.layer2_model.predict_proba(X_l2)[0, 1])
        risk_score = round(risk_probability * 100.0, 2)

        # 8. Decision & Risk Level
        threshold = float(self.layer2_config.get("threshold", 0.86))
        decision = "ANOMALY" if risk_probability >= threshold else "NORMAL"

        if risk_probability < 0.30:
            risk_level = "LOW"
        elif risk_probability < threshold:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # 9. Human-readable reasons
        l1_thresh = float(self.layer1_config.get("threshold", 0.51356))
        reasons = generate_reasons(raw_feats, layer1_anomaly_score, risk_probability, l1_thresh)

        # 10. Transaction summary details
        ts_str = req.timestamp.isoformat() if isinstance(req.timestamp, datetime) else str(req.timestamp)
        tx_details = TransactionDetails(
            amount=req.amount,
            transaction_type=req.transaction_type or "UPI_TRANSFER",
            payment_method=req.payment_method or "UPI",
            receiver_type=req.receiver_type or "INDIVIDUAL",
            location_region=req.location_region or "Chennai",
            device_type=req.device_type or "Android",
            user_id=user_id,
            receiver_id=req.receiver_id,
            merchant_id=req.merchant_id,
            timestamp=ts_str,
        )

        # 11. Update history store for subsequent user requests
        history_store.add_user_transaction(user_id, {
            "timestamp": req.timestamp,
            "amount": req.amount,
            "receiver_id": req.receiver_id,
            "merchant_id": req.merchant_id,
            "device_id": req.device_id,
            "location_latitude": req.location_latitude,
            "location_longitude": req.location_longitude,
            "location_region": req.location_region,
            "is_new_receiver": raw_feats.get("is_new_receiver", 0),
            "is_new_merchant": raw_feats.get("is_new_merchant", 0),
            "merchant_available": raw_feats.get("merchant_available", 0),
            "distance_from_usual_location": req.distance_from_usual_location or 0.0,
        })

        return PredictionResponse(
            transaction_id=req.transaction_id,
            risk_score=risk_score,
            risk_probability=risk_probability,
            decision=decision,
            risk_level=risk_level,
            layer1_anomaly_score=round(layer1_anomaly_score, 4),
            reasons=reasons,
            transaction=tx_details,
        )

    def get_demo_prediction(self, high_risk: bool = True) -> PredictionResponse:
        """
        Fetch a pre-calculated test result from the test dataset for demo purposes.
        """
        if self.demo_test_results is None or self.demo_test_features is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demo datasets are not pre-loaded."
            )

        threshold = float(self.layer2_config.get("threshold", 0.86))
        
        if high_risk:
            subset = self.demo_test_results[self.demo_test_results["risk_probability"] >= threshold]
            if subset.empty:
                subset = self.demo_test_results.sort_values("risk_probability", ascending=False)
            selected = subset.sort_values("risk_probability", ascending=False).iloc[0]
        else:
            subset = self.demo_test_results[self.demo_test_results["risk_probability"] < threshold]
            if subset.empty:
                subset = self.demo_test_results.sort_values("risk_probability", ascending=True)
            selected = subset.sort_values("risk_probability", ascending=True).iloc[0]

        tx_id = str(selected["transaction_id"])
        feat_rows = self.demo_test_features[self.demo_test_features["transaction_id"] == tx_id]
        if feat_rows.empty:
            feat_row = selected
        else:
            feat_row = feat_rows.iloc[0]

        feat_dict = feat_row.to_dict()
        risk_probability = float(selected["risk_probability"])
        risk_score = round(risk_probability * 100.0, 2)
        l1_score = float(selected["layer1_anomaly_score"])
        decision = "ANOMALY" if risk_probability >= threshold else "NORMAL"

        if risk_probability < 0.30:
            risk_level = "LOW"
        elif risk_probability < threshold:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        l1_thresh = float(self.layer1_config.get("threshold", 0.51356))
        reasons = generate_reasons(feat_dict, l1_score, risk_probability, l1_thresh)

        tx_details = TransactionDetails(
            amount=float(feat_dict.get("amount", selected.get("amount", 1000.0))),
            transaction_type=str(feat_dict.get("transaction_type", "UPI_TRANSFER")),
            payment_method=str(feat_dict.get("payment_method", "UPI")),
            receiver_type=str(feat_dict.get("receiver_type", "INDIVIDUAL")),
            location_region=str(feat_dict.get("location_region", "Chennai")),
            device_type=str(feat_dict.get("device_type", "Android")),
        )

        return PredictionResponse(
            transaction_id=tx_id,
            risk_score=risk_score,
            risk_probability=risk_probability,
            decision=decision,
            risk_level=risk_level,
            layer1_anomaly_score=round(l1_score, 4),
            reasons=reasons,
            transaction=tx_details,
        )


model_service = ModelService()
