# UPI Anomaly / Fraud Detection ML API

A high-performance FastAPI backend service providing real-time fraud probability, risk scoring, and human-readable risk explanations for UPI transactions.

The service integrates a 2-Layer Machine Learning pipeline:
- **Layer 1**: Isolation Forest (53 baseline transaction/behavioral features)
- **Layer 2**: XGBoost Classifier (56 features = 55 behavioral features + Layer 1 anomaly score)

---

## 1. Installation

Ensure Python 3.10+ is installed on your system. Navigate to the project root and install requirements:

```bash
cd "C:\Hackathon\model 1"
pip install -r api/requirements.txt
```

---

## 2. Environment Setup (Optional)

You can set custom environment variables or create a `.env` file:

```env
# Optional API Key security for external endpoints
ML_API_KEY=my-secret-api-key

# Configurable CORS origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

If `ML_API_KEY` is not set, the API runs without authentication (ideal for local development).

---

## 3. Running the API

Start the FastAPI application with Uvicorn:

```bash
cd "C:\Hackathon\model 1"
uvicorn api.main:app --host 0.0.0.0 --port 5001 --reload
```

---

## 4. Interactive Swagger Documentation

Once the server is running, interactive API documentation (Swagger UI) is available at:

👉 **http://localhost:5001/docs**

Alternative ReDoc documentation is available at:
👉 **http://localhost:5001/redoc**

---

## 5. API Endpoints

### 1. `GET /health`
Verifies backend service and ML model availability.

**Response:**
```json
{
    "status": "ok",
    "service": "upi-ml-api",
    "layer1": "loaded",
    "layer2": "loaded"
}
```

---

### 2. `GET /model-info`
Returns configuration info about the deployed ML pipeline.

**Response:**
```json
{
    "model": "Layer 1 Isolation Forest + Layer 2 XGBoost",
    "feature_count": 56,
    "threshold": 0.86,
    "device": "cuda",
    "status": "ready"
}
```

---

### 3. `POST /predict`
Processes a raw incoming transaction, extracts real-time behavioral features, passes through Layer 1 & Layer 2, and returns prediction details and reasons.

**Sample Curl Request:**
```bash
curl -X POST "http://localhost:5001/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret-api-key" \
  -d '{
    "transaction_id": "TXN_000942005",
    "timestamp": "2025-12-10T08:49:59",
    "amount": 4237.14,
    "sender_id": "USER001",
    "receiver_id": "USER092",
    "receiver_type": "INDIVIDUAL",
    "merchant_id": null,
    "merchant_category": null,
    "transaction_type": "UPI_TRANSFER",
    "payment_method": "UPI",
    "location_latitude": 13.08,
    "location_longitude": 80.27,
    "location_region": "Chennai",
    "device_id": "DEVICE123",
    "device_type": "Android",
    "os": "Android"
  }'
```

**Sample Response:**
```json
{
    "transaction_id": "TXN_000942005",
    "risk_score": 99.84,
    "risk_probability": 0.9984,
    "decision": "ANOMALY",
    "risk_level": "HIGH",
    "layer1_anomaly_score": 0.5502,
    "reasons": [
        {
            "title": "Amount significantly above recent behavior",
            "detail": "Transaction amount is 8.5x the user's recent average."
        },
        {
            "title": "Strong amount deviation",
            "detail": "Transaction amount strongly deviates from the user's historical behavior."
        },
        {
            "title": "New receiver detected",
            "detail": "This receiver has not previously appeared in the user's transaction history."
        },
        {
            "title": "New device detected",
            "detail": "The transaction is associated with a device not previously used by this user."
        }
    ],
    "transaction": {
        "amount": 4237.14,
        "transaction_type": "UPI_TRANSFER",
        "payment_method": "UPI",
        "receiver_type": "INDIVIDUAL",
        "location_region": "Chennai",
        "device_type": "Android"
    }
}
```

---

### 4. `GET /demo/high-risk` & `GET /demo/normal`
Pre-loaded demonstration endpoints serving real test dataset predictions.

---

## 6. Frontend Integration Instructions

Your frontend team can integrate with the API using standard `fetch`:

```javascript
// 1. Prepare raw transaction object from UI form
const transaction = {
  transaction_id: "TXN_" + Date.now(),
  timestamp: new Date().toISOString(),
  amount: 4237.14,
  sender_id: "USER001",
  receiver_id: "USER092",
  receiver_type: "INDIVIDUAL",
  merchant_id: null,
  merchant_category: null,
  transaction_type: "UPI_TRANSFER",
  payment_method: "UPI",
  location_latitude: 13.08,
  location_longitude: 80.27,
  location_region: "Chennai",
  device_id: "DEVICE123",
  device_type: "Android",
  os: "Android"
};

// 2. Call FastAPI POST /predict endpoint
const response = await fetch("http://localhost:5001/predict", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "<optional-key>"
  },
  body: JSON.stringify(transaction)
});

const result = await response.json();

// 3. Display prediction outputs in frontend components
console.log("Risk Score:", result.risk_score + "%");       // e.g. 99.84%
console.log("Decision:", result.decision);                 // "ANOMALY" or "NORMAL"
console.log("Risk Level:", result.risk_level);             // "HIGH", "MEDIUM", or "LOW"

// Render human-readable risk reasons list
result.reasons.forEach((reason) => {
  console.log(`- ${reason.title}: ${reason.detail}`);
});

// Render transaction details summary
console.log("Amount:", result.transaction.amount);
console.log("Type:", result.transaction.transaction_type);
console.log("Region:", result.transaction.location_region);
```
