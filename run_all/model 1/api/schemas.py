import time
from datetime import datetime, timezone
from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class TransactionRequest(BaseModel):
    transaction_id: str = Field(default_factory=lambda: f"TXN_{int(time.time()*1000)}", description="Unique transaction ID")
    timestamp: Union[datetime, str, int, float] = Field(default_factory=datetime.now, description="Timestamp")
    amount: float = Field(..., description="Transaction amount in INR", gt=0)
    sender_id: Optional[str] = Field(None, description="Sender/User ID")
    user_id: Optional[str] = Field(None, description="User ID")
    receiver_id: Optional[str] = Field(None, description="Receiver ID")
    receiver_name: Optional[str] = Field(None, description="Receiver Name")
    receiver_type: Optional[str] = Field("INDIVIDUAL", description="Receiver type: INDIVIDUAL or MERCHANT")
    merchant_id: Optional[str] = Field(None, description="Merchant ID if applicable")
    merchant_category: Optional[str] = Field(None, description="Merchant category")
    transaction_type: Optional[str] = Field("UPI_TRANSFER", description="Transaction type")
    payment_method: Optional[str] = Field("UPI", description="Payment method")
    location_latitude: float = Field(13.08, description="Latitude", ge=-90.0, le=90.0)
    location_longitude: float = Field(80.27, description="Longitude", ge=-180.0, le=180.0)
    location_region: Optional[str] = Field(None, description="City/Region name")
    device_id: Optional[str] = Field(None, description="Device ID")
    device_type: Optional[str] = Field(None, description="Device type e.g. Android/iOS")
    os: Optional[str] = Field(None, description="Operating system")
    distance_from_usual_location: Optional[float] = Field(0.0, description="Distance from usual location in km", ge=0.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_simulator_payload(cls, data: Any) -> Any:
        """
        Flexibly accept raw payloads from Simulator bot, UI, or external HTTP clients.
        Maps alternate field keys (id, userId, merchant, location, device, ip, time, etc.)
        """
        if isinstance(data, dict):
            raw = dict(data)
            
            # If payload is wrapped inside a "transaction" sub-dict
            if "transaction" in raw and isinstance(raw["transaction"], dict):
                tx_sub = raw["transaction"]
                for k, v in tx_sub.items():
                    if k not in raw or raw[k] is None:
                        raw[k] = v

            # Map transaction ID aliases
            if "transaction_id" not in raw or not raw["transaction_id"]:
                if "id" in raw and raw["id"]:
                    raw["transaction_id"] = str(raw["id"])
                elif "transactionId" in raw and raw["transactionId"]:
                    raw["transaction_id"] = str(raw["transactionId"])

            # Map User ID / Sender ID aliases
            if "user_id" not in raw or not raw["user_id"]:
                if "userId" in raw and raw["userId"]:
                    raw["user_id"] = str(raw["userId"])
                elif "sender_id" in raw and raw["sender_id"]:
                    raw["user_id"] = str(raw["sender_id"])
            if "sender_id" not in raw or not raw["sender_id"]:
                raw["sender_id"] = raw.get("user_id", "USER_DEFAULT")

            # Map Receiver / Merchant aliases
            if "receiver_id" not in raw or not raw["receiver_id"]:
                if "receiverId" in raw and raw["receiverId"]:
                    raw["receiver_id"] = str(raw["receiverId"])
                elif "receiver" in raw and raw["receiver"]:
                    raw["receiver_id"] = str(raw["receiver"])
                elif "merchant" in raw and raw["merchant"]:
                    raw["receiver_id"] = str(raw["merchant"])

            if "merchant_id" not in raw or not raw["merchant_id"]:
                if "merchantId" in raw and raw["merchantId"]:
                    raw["merchant_id"] = str(raw["merchantId"])
                elif "merchant" in raw and raw["merchant"]:
                    raw["merchant_id"] = str(raw["merchant"])

            # Map Location aliases
            if "location_region" not in raw or not raw["location_region"]:
                if "location" in raw and isinstance(raw["location"], str):
                    raw["location_region"] = raw["location"]
            if "location_latitude" not in raw or raw["location_latitude"] is None:
                raw["location_latitude"] = 13.08
            if "location_longitude" not in raw or raw["location_longitude"] is None:
                raw["location_longitude"] = 80.27

            # Map Device aliases
            if "device_id" not in raw or not raw["device_id"]:
                if "deviceId" in raw and raw["deviceId"]:
                    raw["device_id"] = str(raw["deviceId"])
                elif "device" in raw and isinstance(raw["device"], str):
                    raw["device_id"] = raw["device"]
            if "device_type" not in raw or not raw["device_type"]:
                if "deviceType" in raw and raw["deviceType"]:
                    raw["device_type"] = str(raw["deviceType"])
                elif "device" in raw and isinstance(raw["device"], str):
                    raw["device_type"] = raw["device"]

            # Safe amount parsing
            if "amount" in raw:
                try:
                    raw["amount"] = float(raw["amount"])
                except (ValueError, TypeError):
                    pass

            return raw
        return data

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, (int, float)):
            # Epoch milliseconds or seconds
            if value > 1e11:
                return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc).replace(tzinfo=None)
            return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)
        if isinstance(value, str):
            try:
                clean_str = value.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_str).replace(tzinfo=None)
            except Exception:
                try:
                    # Time format string e.g. "10:42:36"
                    now = datetime.now()
                    parts = [int(p) for p in value.split(":")]
                    return datetime(now.year, now.month, now.day, parts[0], parts[1], parts[2])
                except Exception:
                    return datetime.now().replace(tzinfo=None)
        return datetime.now().replace(tzinfo=None)

    @model_validator(mode="after")
    def populate_user_id(self) -> "TransactionRequest":
        if not self.user_id and self.sender_id:
            self.user_id = self.sender_id
        elif not self.sender_id and self.user_id:
            self.sender_id = self.user_id
        elif not self.user_id and not self.sender_id:
            self.user_id = "USER_DEFAULT"
            self.sender_id = "USER_DEFAULT"
        return self


class Reason(BaseModel):
    title: str = Field(..., description="Human-readable reason title")
    detail: str = Field(..., description="Detailed explanation")


class TransactionDetails(BaseModel):
    amount: float
    transaction_type: Optional[str] = "UPI_TRANSFER"
    payment_method: Optional[str] = "UPI"
    receiver_type: Optional[str] = "INDIVIDUAL"
    location_region: Optional[str] = None
    device_type: Optional[str] = None
    user_id: Optional[str] = None
    receiver_id: Optional[str] = None
    merchant_id: Optional[str] = None
    timestamp: Optional[str] = None


class PredictionResponse(BaseModel):
    transaction_id: str
    risk_score: float = Field(..., description="Risk score scaled from 0 to 100")
    risk_probability: float = Field(..., description="Model risk probability from 0.0 to 1.0")
    decision: str = Field(..., description="ANOMALY or NORMAL")
    risk_level: str = Field(..., description="LOW, MEDIUM, or HIGH")
    layer1_anomaly_score: float = Field(..., description="Isolation Forest anomaly score")
    reasons: List[Reason] = Field(default_factory=list, description="Top risk reasons")
    transaction: TransactionDetails


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "upi-ml-api"
    layer1: str = "loaded"
    layer2: str = "loaded"


class ModelInfoResponse(BaseModel):
    model: str = "Layer 1 Isolation Forest + Layer 2 XGBoost"
    feature_count: int = 56
    threshold: float
    device: str = "cuda"
    status: str = "ready"
