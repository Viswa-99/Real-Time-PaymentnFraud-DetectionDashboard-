import time
import os
from fastapi.testclient import TestClient
import api.config as config
from api.main import app
from api.model_service import model_service


def run_tests():
    print("=" * 70)
    print("UPI ANOMALY DETECTION ML API — AUTOMATED VERIFICATION SUITE")
    print("=" * 70)

    # Initialize Lifespan (Load models)
    print("\n[1/9] Initializing Lifespan & Loading Models...")
    with TestClient(app) as client:
        
        # Test 1: GET /health
        print("\n[2/9] Testing GET /health...")
        res = client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["status"] == "ok"
        assert data["layer1"] == "loaded"
        assert data["layer2"] == "loaded"
        print(f"[OK] /health PASSED: {data}")

        # Test 2: GET /model-info
        print("\n[3/9] Testing GET /model-info...")
        res = client.get("/model-info")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["feature_count"] == 55
        assert data["threshold"] > 0
        assert data["status"] == "ready"
        print(f"[OK] /model-info PASSED: feature_count={data['feature_count']}, threshold={data['threshold']}")

        # Test 3: GET /demo/high-risk
        print("\n[4/9] Testing GET /demo/high-risk...")
        res = client.get("/demo/high-risk")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["decision"] == "ANOMALY"
        assert data["risk_level"] == "HIGH"
        assert len(data["reasons"]) > 0
        print(f"[OK] /demo/high-risk PASSED: Txn={data['transaction_id']}, Score={data['risk_score']}%, Decision={data['decision']}")

        # Test 4: GET /demo/normal
        print("\n[5/9] Testing GET /demo/normal...")
        res = client.get("/demo/normal")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["decision"] == "NORMAL"
        print(f"[OK] /demo/normal PASSED: Txn={data['transaction_id']}, Score={data['risk_score']}%, Decision={data['decision']}")

        # Test 5: POST /predict (Valid Request)
        print("\n[6/9] Testing POST /predict (Valid Request & History Accumulation)...")
        valid_payload = {
            "transaction_id": "TXN_TEST_001",
            "timestamp": "2025-12-10T08:49:59",
            "amount": 4237.14,
            "sender_id": "USER_DEMO_999",
            "receiver_id": "USER_REC_001",
            "receiver_type": "INDIVIDUAL",
            "merchant_id": None,
            "merchant_category": None,
            "transaction_type": "UPI_TRANSFER",
            "payment_method": "UPI",
            "location_latitude": 13.08,
            "location_longitude": 80.27,
            "location_region": "Chennai",
            "device_id": "DEVICE123",
            "device_type": "Android",
            "os": "Android"
        }
        res = client.post("/predict", json=valid_payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "risk_score" in data
        assert "risk_probability" in data
        assert data["transaction_id"] == "TXN_TEST_001"
        assert data["transaction"]["amount"] == 4237.14
        print(f"[OK] POST /predict PASSED: Risk Score={data['risk_score']}%, Decision={data['decision']}, Reasons Count={len(data['reasons'])}")

        # Sequential second request for same user to verify history integration
        payload_2 = dict(valid_payload)
        payload_2["transaction_id"] = "TXN_TEST_002"
        payload_2["amount"] = 85000.0  # Spike amount
        payload_2["timestamp"] = "2025-12-10T08:52:00"  # 2 minutes later
        res2 = client.post("/predict", json=payload_2)
        assert res2.status_code == 200
        data2 = res2.json()
        print(f"[OK] POST /predict (2nd Txn Spike) PASSED: Risk Score={data2['risk_score']}%, Decision={data2['decision']}")

        # Test 6: POST /predict Validation Errors
        print("\n[7/9] Testing Input Validation (Invalid Amount & Latitude)...")
        # Negative amount
        bad_amount = dict(valid_payload)
        bad_amount["amount"] = -50.0
        res_bad_amt = client.post("/predict", json=bad_amount)
        assert res_bad_amt.status_code == 422, f"Expected 422 for negative amount, got {res_bad_amt.status_code}"

        # Invalid latitude
        bad_lat = dict(valid_payload)
        bad_lat["location_latitude"] = 150.0
        res_bad_lat = client.post("/predict", json=bad_lat)
        assert res_bad_lat.status_code == 422, f"Expected 422 for latitude 150, got {res_bad_lat.status_code}"
        print("[OK] Validation Checks PASSED: Invalid amount and latitude properly rejected with HTTP 422.")

        # Test 7: API Key Authentication
        print("\n[8/9] Testing API Key Authentication...")
        config.ML_API_KEY = "test-secret-key"
        
        # Unauthorized without header
        res_no_key = client.post("/predict", json=valid_payload)
        assert res_no_key.status_code == 401, f"Expected 401 without API key, got {res_no_key.status_code}"
        
        # Unauthorized with wrong header
        res_wrong_key = client.post("/predict", json=valid_payload, headers={"X-API-Key": "wrong-key"})
        assert res_wrong_key.status_code == 401, f"Expected 401 with wrong key, got {res_wrong_key.status_code}"
        
        # Authorized with correct header
        res_auth = client.post("/predict", json=valid_payload, headers={"X-API-Key": "test-secret-key"})
        assert res_auth.status_code == 200, f"Expected 200 with valid key, got {res_auth.status_code}"
        
        # Reset ML_API_KEY
        config.ML_API_KEY = None
        print("[OK] API Key Authentication PASSED: 401 on missing/invalid key, 200 on valid key.")

        # Test 8: Latency Benchmark (<100ms requirement)
        print("\n[9/9] Testing Inference Latency Benchmark (50 requests)...")
        latencies = []
        for i in range(50):
            payload = dict(valid_payload)
            payload["transaction_id"] = f"TXN_BENCH_{i}"
            payload["amount"] = 1000.0 + (i * 50)
            
            t0 = time.perf_counter()
            client.post("/predict", json=payload)
            lat = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat)

        avg_lat = sum(latencies) / len(latencies)
        p95_lat = sorted(latencies)[int(0.95 * len(latencies))]
        print(f"[OK] Latency Benchmark PASSED: Average Latency = {avg_lat:.2f} ms | P95 Latency = {p95_lat:.2f} ms (Target < 100 ms)")

        assert avg_lat < 100.0, f"Average latency {avg_lat:.2f} ms exceeded 100 ms limit!"

    print("\n" + "=" * 70)
    print("ALL API VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
