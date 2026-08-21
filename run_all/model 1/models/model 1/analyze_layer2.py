from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"

RESULT_FILE = (
    OUTPUT_DIR /
    "layer2_test_results.parquet"
)

results = pd.read_parquet(RESULT_FILE)

THRESHOLD = 0.900

print("=" * 75)
print("LAYER 2 — ERROR ANALYSIS")
print("=" * 75)

# ------------------------------------------------------------
# Basic distribution
# ------------------------------------------------------------

print("\nRisk probability distribution:")

print(
    results["risk_probability"].describe(
        percentiles=[
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99,
        ]
    )
)

# ------------------------------------------------------------
# Performance by anomaly type
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("DETECTION BY ANOMALY TYPE")
print("=" * 75)

anomalies = results[
    results["is_anomaly"] == 1
].copy()

rows = []

for anomaly_type, group in anomalies.groupby(
    "anomaly_type"
):

    detected = (
        group["risk_probability"] >= THRESHOLD
    )

    rows.append({
        "anomaly_type": anomaly_type,
        "count": len(group),
        "detected": int(detected.sum()),
        "detection_rate": detected.mean(),
        "mean_risk": group["risk_probability"].mean(),
        "median_risk": group["risk_probability"].median(),
    })

type_results = pd.DataFrame(rows)

type_results = type_results.sort_values(
    "detection_rate",
    ascending=False
)

print(
    type_results.to_string(
        index=False,
        formatters={
            "detection_rate": "{:.2%}".format,
            "mean_risk": "{:.4f}".format,
            "median_risk": "{:.4f}".format,
        }
    )
)

# ------------------------------------------------------------
# False positives
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("FALSE POSITIVE ANALYSIS")
print("=" * 75)

false_positives = results[
    (results["is_anomaly"] == 0)
    &
    (results["risk_probability"] >= THRESHOLD)
].copy()

print(
    f"False positives: {len(false_positives):,}"
)

print(
    "\nFalse-positive risk distribution:"
)

print(
    false_positives[
        "risk_probability"
    ].describe()
)

# ------------------------------------------------------------
# False negatives
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("FALSE NEGATIVE ANALYSIS")
print("=" * 75)

false_negatives = results[
    (results["is_anomaly"] == 1)
    &
    (results["risk_probability"] < THRESHOLD)
].copy()

print(
    f"False negatives: {len(false_negatives):,}"
)

print(
    "\nFalse-negative risk distribution:"
)

print(
    false_negatives[
        "risk_probability"
    ].describe()
)

# ------------------------------------------------------------
# High-risk normal transactions
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("TOP LEGITIMATE HIGH-RISK TRANSACTIONS")
print("=" * 75)

top_legitimate = (
    results[
        results["is_anomaly"] == 0
    ]
    .sort_values(
        "risk_probability",
        ascending=False
    )
    .head(20)
)

print(
    top_legitimate[
        [
            "transaction_id",
            "user_id",
            "risk_probability",
            "risk_score",
            "layer1_anomaly_score",
        ]
    ].to_string(index=False)
)

# ------------------------------------------------------------
# Missed anomalies
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("TOP MISSED ANOMALIES")
print("=" * 75)

top_missed = (
    false_negatives
    .sort_values(
        "risk_probability",
        ascending=False
    )
    .head(30)
)

print(
    top_missed[
        [
            "transaction_id",
            "user_id",
            "anomaly_type",
            "risk_probability",
            "risk_score",
            "layer1_anomaly_score",
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 75)
print("ERROR ANALYSIS COMPLETE")
print("=" * 75)
