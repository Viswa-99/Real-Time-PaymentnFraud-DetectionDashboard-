from pathlib import Path

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(r"C:\Hackathon")

OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"
MODEL_DIR = BASE_DIR / "model 1" / "models"

TRAIN_FILE = OUTPUT_DIR / "train_features.parquet"
MODEL_FILE = MODEL_DIR / "layer1_isolation_forest.pkl"

OUTPUT_FILE = (
    OUTPUT_DIR /
    "layer1_train_scores.parquet"
)


FEATURES = [
    "log_amount",
    "hour",
    "day_of_week",
    "is_weekend",

    "user_history_count",
    "user_avg_amount",
    "user_std_amount",
    "amount_to_user_avg",
    "amount_zscore",

    "is_new_receiver",
    "receiver_transaction_count",
    "receiver_seen_before",

    "merchant_available",
    "is_new_merchant",
    "merchant_transaction_count",
    "merchant_seen_before",

    "is_new_device",
    "device_transaction_count",
    "device_seen_before",

    "transactions_last_5min",
    "transactions_last_15min",
    "transactions_last_1hour",
    "amount_last_1hour",

    "distance_from_usual_location",
    "distance_from_previous_transaction",
    "time_since_last_transaction_seconds",
    "log_travel_speed",

    "has_user_amount_history",
]


print("=" * 70)
print("GENERATING LAYER 1 TRAINING SCORES")
print("=" * 70)

train = pd.read_parquet(TRAIN_FILE)

model = joblib.load(MODEL_FILE)

X_train = (
    train[FEATURES]
    .astype(np.float32)
    .to_numpy()
)

print(f"Training rows: {len(train):,}")

scores = -model.score_samples(X_train)

output = train[
    [
        "transaction_id",
        "user_id",
        "timestamp",
        "is_anomaly",
        "anomaly_type",
        "anomaly_severity",
    ]
].copy()

output["layer1_anomaly_score"] = scores

output.to_parquet(
    OUTPUT_FILE,
    index=False
)

print(f"\nSaved: {OUTPUT_FILE}")

print("\nLayer 1 training score statistics:")
print(
    pd.Series(scores).describe(
        percentiles=[
            0.01,
            0.05,
            0.50,
            0.95,
            0.99,
        ]
    )
)

print("\nCOMPLETE")