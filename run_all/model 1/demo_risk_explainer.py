from pathlib import Path
import argparse
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"
MODEL_DIR = BASE_DIR / "model 1" / "models"

TEST_FEATURES = OUTPUT_DIR / "test_features.parquet"
TEST_RESULTS = OUTPUT_DIR / "layer2_test_results.parquet"
CONFIG_FILE = MODEL_DIR / "layer2_config.json"

# ---------------------------------------------------------------------
# Human-readable reason engine
# These reasons are generated from transaction features, NOT anomaly_type.
# ---------------------------------------------------------------------

def build_reasons(row, layer1_score, risk_probability):
    reasons = []

    amount = float(row.get("amount", 0))
    amount_ratio = float(row.get("recent_amount_ratio", np.nan))
    amount_z = float(row.get("amount_zscore", np.nan))
    user_avg = float(row.get("user_avg_amount", np.nan))

    if row.get("is_new_receiver", 0) == 1:
        reasons.append((
            4,
            "New receiver detected",
            "This receiver has not previously appeared in the user's transaction history."
        ))

    if row.get("is_new_device", 0) == 1:
        reasons.append((
            4,
            "New device detected",
            "The transaction is associated with a device not previously used by this user."
        ))

    distance = float(row.get("distance_from_usual_location", 0))
    if distance >= 200:
        reasons.append((
            5,
            "Unusual transaction location",
            f"Transaction is approximately {distance:,.0f} km from the user's usual location."
        ))

    if np.isfinite(amount_ratio):
        if amount_ratio >= 3:
            reasons.append((
                5,
                "Amount significantly above recent behavior",
                f"Transaction amount is {amount_ratio:.1f}× the user's recent average."
            ))
        elif amount_ratio >= 2:
            reasons.append((
                3,
                "Amount above recent behavior",
                f"Transaction amount is {amount_ratio:.1f}× the user's recent average."
            ))

    if np.isfinite(amount_z) and amount_z >= 3:
        reasons.append((
            5,
            "Strong amount deviation",
            f"Amount z-score is {amount_z:.1f}, indicating a strong deviation from normal behavior."
        ))

    tx_1h = int(row.get("transactions_last_1hour", 0))
    if tx_1h >= 5:
        reasons.append((
            4,
            "High transaction velocity",
            f"{tx_1h} transactions occurred in the previous hour."
        ))
    elif tx_1h >= 3:
        reasons.append((
            2,
            "Elevated transaction velocity",
            f"{tx_1h} transactions occurred in the previous hour."
        ))

    new_m15 = int(row.get("new_merchants_last_15min", 0))
    new_m1h = int(row.get("new_merchants_last_1hour", 0))
    if new_m15 >= 2:
        reasons.append((
            5,
            "Multiple new merchants recently",
            f"{new_m15} new merchant interactions occurred in the previous 15 minutes."
        ))
    elif new_m1h >= 3:
        reasons.append((
            3,
            "Several new merchant interactions",
            f"{new_m1h} new merchant interactions occurred in the previous hour."
        ))

    layer1_threshold = 0.51356
    if layer1_score >= layer1_threshold:
        reasons.append((
            3,
            "Unusual overall transaction behavior",
            f"Layer 1 anomaly score is {layer1_score:.3f}, above the anomaly threshold."
        ))

    if not reasons:
        reasons.append((
            1,
            "Model-detected behavioral risk",
            "The combined transaction features indicate elevated risk."
        ))

    reasons.sort(key=lambda x: x[0], reverse=True)
    return reasons[:4]


def format_transaction(row):
    return {
        "transaction_id": str(row.get("transaction_id", "")),
        "timestamp": str(row.get("timestamp", "")),
        "amount": f"₹{float(row.get('amount', 0)):,.2f}",
        "transaction_type": str(row.get("transaction_type", "")),
        "payment_method": str(row.get("payment_method", "")),
        "receiver_name": str(row.get("receiver_name", "")),
        "receiver_type": str(row.get("receiver_type", "")),
        "merchant_category": str(row.get("merchant_category", "")),
        "location_region": str(row.get("location_region", "")),
        "device_type": str(row.get("device_type", "")),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Explain a Layer 2 UPI anomaly using the saved test results."
    )
    parser.add_argument(
        "--transaction-id",
        help="Transaction ID to inspect."
    )
    parser.add_argument(
        "--anomaly",
        action="store_true",
        help="Automatically select the highest-risk flagged test transaction."
    )
    args = parser.parse_args()

    if not TEST_FEATURES.exists():
        raise FileNotFoundError(TEST_FEATURES)
    if not TEST_RESULTS.exists():
        raise FileNotFoundError(TEST_RESULTS)
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(CONFIG_FILE)

    features = pd.read_parquet(TEST_FEATURES)
    results = pd.read_parquet(TEST_RESULTS)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    threshold = float(config["threshold"])

    if args.transaction_id:
        matches = results[
            results["transaction_id"].astype(str) == str(args.transaction_id)
        ]
        if matches.empty:
            raise ValueError(f"Transaction not found: {args.transaction_id}")
        result = matches.iloc[0]

    elif args.anomaly:
        flagged = results[results["risk_probability"] >= threshold]
        if flagged.empty:
            raise RuntimeError("No flagged anomalies found in the test results.")
        result = flagged.sort_values(
            "risk_probability", ascending=False
        ).iloc[0]

    else:
        # Default: highest-risk transaction in the untouched test set.
        result = results.sort_values(
            "risk_probability", ascending=False
        ).iloc[0]

    txid = result["transaction_id"]

    feature_rows = features[
        features["transaction_id"] == txid
    ]
    if feature_rows.empty:
        raise ValueError(f"Feature row not found for transaction: {txid}")

    row = feature_rows.iloc[0]

    risk_probability = float(result["risk_probability"])
    risk_score = risk_probability * 100.0
    layer1_score = float(result["layer1_anomaly_score"])

    flagged = risk_probability >= threshold

    reasons = build_reasons(row, layer1_score, risk_probability)

    print("\n" + "=" * 72)
    print("UPI TRANSACTION RISK ANALYSIS")
    print("=" * 72)

    print("\nTRANSACTION")
    print("-" * 72)
    tx = format_transaction(row)
    for key, value in tx.items():
        print(f"{key.replace('_', ' ').title():25}: {value}")

    print("\nMODEL RESULT")
    print("-" * 72)
    print(f"Layer 1 anomaly score    : {layer1_score:.4f}")
    print(f"Layer 2 risk probability  : {risk_probability:.4f}")
    print(f"Risk score                : {risk_score:.2f}%")
    print(f"Decision threshold        : {threshold:.3f}")
    print(
        f"Decision                  : "
        f"{'🚨 ANOMALY / HIGH RISK' if flagged else 'NORMAL / LOW RISK'}"
    )

    print("\nREASONS")
    print("-" * 72)
    for i, (_, title, explanation) in enumerate(reasons, 1):
        print(f"{i}. {title}")
        print(f"   {explanation}")

    print("\n" + "=" * 72)
    print("ANALYSIS COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()