from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"

TEST_FILE = OUTPUT_DIR / "test_features.parquet"
SCORES_FILE = OUTPUT_DIR / "layer1_test_scores.parquet"

test = pd.read_parquet(TEST_FILE)

scores = pd.read_parquet(SCORES_FILE)

threshold = scores.loc[
    scores["layer1_prediction"] == 1,
    "layer1_anomaly_score"
].min()

test = test.merge(
    scores[
        [
            "transaction_id",
            "layer1_anomaly_score",
            "layer1_prediction",
        ]
    ],
    on="transaction_id",
    how="left",
)

print("=" * 70)
print("LAYER 1 — ANOMALY TYPE ANALYSIS")
print("=" * 70)

print(f"\nThreshold: {threshold:.6f}")

print("\nPerformance by anomaly type:")
print("-" * 70)

rows = []

for anomaly_type, group in test[
    test["is_anomaly"] == 1
].groupby("anomaly_type"):

    actual = group["is_anomaly"].values
    predicted = group["layer1_prediction"].values

    rows.append({
        "anomaly_type": anomaly_type,
        "transactions": len(group),
        "detected": int(predicted.sum()),
        "detection_rate": predicted.mean(),
        "mean_score": group["layer1_anomaly_score"].mean(),
    })

result = pd.DataFrame(rows)

result = result.sort_values(
    "detection_rate",
    ascending=False
)

print(
    result.to_string(
        index=False,
        formatters={
            "detection_rate": "{:.2%}".format,
            "mean_score": "{:.4f}".format,
        }
    )
)

print("\n" + "=" * 70)
print("NORMAL TRANSACTION SCORE")
print("=" * 70)

normal = test[test["is_anomaly"] == 0]

print(
    normal["layer1_anomaly_score"].describe(
        percentiles=[
            0.90,
            0.95,
            0.99,
        ]
    )
)

print("\n" + "=" * 70)
print("ANOMALOUS TRANSACTION SCORE")
print("=" * 70)

anomalies = test[test["is_anomaly"] == 1]

print(
    anomalies["layer1_anomaly_score"].describe(
        percentiles=[
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

print("\n" + "=" * 70)
print("LAYER 1 ANALYSIS COMPLETE")
print("=" * 70)