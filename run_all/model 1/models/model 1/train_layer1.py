from pathlib import Path
import json
import time

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    confusion_matrix,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"
MODEL_DIR = BASE_DIR / "model 1" / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = OUTPUT_DIR / "train_features.parquet"
VAL_FILE = OUTPUT_DIR / "validation_features.parquet"
TEST_FILE = OUTPUT_DIR / "test_features.parquet"

MODEL_FILE = MODEL_DIR / "layer1_isolation_forest.pkl"
CONFIG_FILE = MODEL_DIR / "layer1_config.json"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    # Transaction
    "log_amount",
    "hour",
    "day_of_week",
    "is_weekend",

    # User behavior
    "user_history_count",
    "user_avg_amount",
    "user_std_amount",
    "amount_to_user_avg",
    "amount_zscore",

    # Receiver
    "is_new_receiver",
    "receiver_transaction_count",
    "receiver_seen_before",

    # Merchant
    "merchant_available",
    "is_new_merchant",
    "merchant_transaction_count",
    "merchant_seen_before",

    # Device
    "is_new_device",
    "device_transaction_count",
    "device_seen_before",

    # Velocity
    "transactions_last_5min",
    "transactions_last_15min",
    "transactions_last_1hour",
    "amount_last_1hour",

    # Location
    "distance_from_usual_location",
    "distance_from_previous_transaction",
    "time_since_last_transaction_seconds",
    "log_travel_speed",

    # History availability
    "has_user_amount_history",

    # ========================================================
    # V2 BEHAVIORAL DRIFT
    # ========================================================
    "recent_avg_amount_5tx",
    "historical_avg_amount",
    "recent_amount_ratio",
    "recent_tx_count_1h",
    "recent_tx_count_24h",
    "historical_tx_frequency",
    "recent_unique_receivers",
    "historical_unique_receivers",
    "recent_unique_merchants",
    "historical_unique_merchants",
    "recent_device_changes",

    # ========================================================
    # V2 LOCATION CONTEXT
    # ========================================================
    "user_location_transaction_count",
    "user_region_transaction_count",
    "distance_from_user_median_location",
    "distance_from_previous_location",
    "location_frequency_score",

    # ========================================================
    # V2 RECEIVER RELATIONSHIP
    # ========================================================
    "user_receiver_transaction_count",
    "receiver_relationship_age",
    "time_since_receiver_last_transaction",

    # ========================================================
    # V2 ENTITY BURSTS
    # ========================================================
    "new_receivers_last_5min",
    "new_receivers_last_15min",
    "new_receivers_last_1hour",
    "new_merchants_last_5min",
    "new_merchants_last_15min",
    "new_merchants_last_1hour",
]


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("LAYER 1 — ISOLATION FOREST")
print("=" * 70)

print("\nLoading feature datasets...")

train = pd.read_parquet(TRAIN_FILE)
val = pd.read_parquet(VAL_FILE)
test = pd.read_parquet(TEST_FILE)

print(f"Train:      {len(train):,}")
print(f"Validation: {len(val):,}")
print(f"Test:       {len(test):,}")


# ============================================================
# VALIDATION
# ============================================================

print("\nChecking feature schema...")

missing_features = [
    feature
    for feature in FEATURES
    if feature not in train.columns
]

if missing_features:
    raise ValueError(
        f"Missing features: {missing_features}"
    )

missing_values = train[FEATURES].isna().sum()

if missing_values.sum() > 0:
    print("\nMissing values detected:")

    print(
        missing_values[
            missing_values > 0
        ]
    )

    raise ValueError(
        "Layer 1 cannot start with missing feature values."
    )

print("Feature schema: PASSED")
print(f"Number of features: {len(FEATURES)}")

if len(FEATURES) != 53:
    raise ValueError(
        f"Expected 53 V2 features, but Layer 1 is configured with "
        f"{len(FEATURES)} features."
    )


# ============================================================
# PREPARE ARRAYS
# ============================================================

X_train = train[FEATURES].astype(np.float32).to_numpy()
X_val = val[FEATURES].astype(np.float32).to_numpy()
X_test = test[FEATURES].astype(np.float32).to_numpy()

y_val = val["is_anomaly"].astype(np.int8).to_numpy()
y_test = test["is_anomaly"].astype(np.int8).to_numpy()


# ============================================================
# TRAIN ISOLATION FOREST
# ============================================================

print("\nTraining Isolation Forest...")

start = time.perf_counter()

model = IsolationForest(
    n_estimators=300,
    max_samples=8192,
    contamination="auto",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train)

training_time = time.perf_counter() - start

print(
    f"Training completed in "
    f"{training_time:.2f} seconds"
)


# ============================================================
# GENERATE SCORES
# ============================================================

print("\nGenerating anomaly scores...")

# IsolationForest:
# score_samples() -> higher = more normal
#
# Therefore negate it:
# higher = more anomalous

val_scores = -model.score_samples(X_val)
test_scores = -model.score_samples(X_test)


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

print("\nAnomaly score distribution:")

val_score_stats = pd.Series(
    val_scores,
    name="validation"
).describe(
    percentiles=[
        0.01,
        0.05,
        0.50,
        0.95,
        0.99,
    ]
)

test_score_stats = pd.Series(
    test_scores,
    name="test"
).describe(
    percentiles=[
        0.01,
        0.05,
        0.50,
        0.95,
        0.99,
    ]
)

score_stats = pd.concat(
    [val_score_stats, test_score_stats],
    axis=1
)

print(score_stats)


# ============================================================
# VALIDATION THRESHOLD
# ============================================================

print("\nFinding validation threshold...")

"""
We deliberately do NOT choose a threshold using the test set.

Use the validation set to find a threshold.

We search thresholds based on score quantiles.
"""

threshold_candidates = np.quantile(
    val_scores,
    np.linspace(
        0.90,
        0.995,
        100
    )
)

best_threshold = None
best_f1 = -1

threshold_results = []

for threshold in threshold_candidates:

    predictions = (
        val_scores >= threshold
    ).astype(np.int8)

    precision = precision_score(
        y_val,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_val,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_val,
        predictions,
        zero_division=0,
    )

    threshold_results.append({
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    })

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold


print(
    f"\nBest validation threshold: "
    f"{best_threshold:.6f}"
)

print(
    f"Best validation F1: "
    f"{best_f1:.4f}"
)


# ============================================================
# VALIDATION METRICS
# ============================================================

val_predictions = (
    val_scores >= best_threshold
).astype(np.int8)

val_precision = precision_score(
    y_val,
    val_predictions,
    zero_division=0,
)

val_recall = recall_score(
    y_val,
    val_predictions,
    zero_division=0,
)

val_f1 = f1_score(
    y_val,
    val_predictions,
    zero_division=0,
)

val_pr_auc = average_precision_score(
    y_val,
    val_scores,
)

val_cm = confusion_matrix(
    y_val,
    val_predictions,
)


print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(f"Precision : {val_precision:.4f}")
print(f"Recall    : {val_recall:.4f}")
print(f"F1        : {val_f1:.4f}")
print(f"PR-AUC    : {val_pr_auc:.4f}")

print("\nConfusion Matrix:")
print(val_cm)


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

print("\nEvaluating untouched test set...")

test_predictions = (
    test_scores >= best_threshold
).astype(np.int8)

test_precision = precision_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_recall = recall_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_f1 = f1_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_pr_auc = average_precision_score(
    y_test,
    test_scores,
)

test_cm = confusion_matrix(
    y_test,
    test_predictions,
)


print("\n" + "=" * 70)
print("TEST RESULTS")
print("=" * 70)

print(f"Precision : {test_precision:.4f}")
print(f"Recall    : {test_recall:.4f}")
print(f"F1        : {test_f1:.4f}")
print(f"PR-AUC    : {test_pr_auc:.4f}")

print("\nConfusion Matrix:")
print(test_cm)


# ============================================================
# SAVE MODEL
# ============================================================

print("\nSaving Layer 1 model...")

joblib.dump(
    model,
    MODEL_FILE
)

config = {
    "model": "IsolationForest",
    "n_estimators": 300,
    "max_samples": 8192,
    "random_state": 42,
    "features": FEATURES,
    "threshold": float(best_threshold),
    "training_time_seconds": training_time,
    "validation": {
        "precision": float(val_precision),
        "recall": float(val_recall),
        "f1": float(val_f1),
        "pr_auc": float(val_pr_auc),
    },
    "test": {
        "precision": float(test_precision),
        "recall": float(test_recall),
        "f1": float(test_f1),
        "pr_auc": float(test_pr_auc),
    },
}

with open(
    CONFIG_FILE,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        config,
        f,
        indent=4,
    )


# ============================================================
# SAVE SCORES FOR LAYER 2
# ============================================================

print("\nSaving Layer 1 scores...")

val_output = val[
    [
        "transaction_id",
        "user_id",
        "timestamp",
        "is_anomaly",
        "anomaly_type",
        "anomaly_severity",
    ]
].copy()

val_output["layer1_anomaly_score"] = val_scores
val_output["layer1_prediction"] = val_predictions

test_output = test[
    [
        "transaction_id",
        "user_id",
        "timestamp",
        "is_anomaly",
        "anomaly_type",
        "anomaly_severity",
    ]
].copy()

test_output["layer1_anomaly_score"] = test_scores
test_output["layer1_prediction"] = test_predictions

val_output.to_parquet(
    OUTPUT_DIR / "layer1_validation_scores.parquet",
    index=False,
)

test_output.to_parquet(
    OUTPUT_DIR / "layer1_test_scores.parquet",
    index=False,
)


print("\n" + "=" * 70)
print("LAYER 1 COMPLETE")
print("=" * 70)

print(f"Model: {MODEL_FILE}")
print(f"Config: {CONFIG_FILE}")
print(
    "Validation scores saved to:",
    OUTPUT_DIR / "layer1_validation_scores.parquet"
)
print(
    "Test scores saved to:",
    OUTPUT_DIR / "layer1_test_scores.parquet"
)