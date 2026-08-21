from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# V2 FEATURE DIAGNOSTICS
# ============================================================

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"

DATA_FILE = OUTPUT_DIR / "transactions_features.parquet"
TEST_FILE = OUTPUT_DIR / "test_features.parquet"

print("=" * 76)
print("V2 FEATURE DIAGNOSTICS — WEAK ANOMALY TYPES")
print("=" * 76)

print("\nLoading feature dataset...")
df = pd.read_parquet(DATA_FILE)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

# ============================================================
# TARGET ANOMALY TYPES
# ============================================================

TARGETS = [
    "NEW_RECEIVER",
    "BEHAVIORAL_DRIFT",
    "UNUSUAL_LOCATION",
    "MULTIPLE_NEW_MERCHANTS",
]

FEATURE_GROUPS = {
    "NEW_RECEIVER": [
        "is_new_receiver",
        "receiver_transaction_count",
        "receiver_seen_before",
        "user_receiver_transaction_count",
        "receiver_relationship_age",
        "time_since_receiver_last_transaction",
        "new_receivers_last_5min",
        "new_receivers_last_15min",
        "new_receivers_last_1hour",
        "recent_unique_receivers",
        "historical_unique_receivers",
    ],

    "BEHAVIORAL_DRIFT": [
        "recent_avg_amount_5tx",
        "historical_avg_amount",
        "recent_amount_ratio",
        "amount_to_user_avg",
        "amount_zscore",
        "recent_tx_count_1h",
        "recent_tx_count_24h",
        "historical_tx_frequency",
        "recent_unique_receivers",
        "historical_unique_receivers",
        "recent_unique_merchants",
        "historical_unique_merchants",
        "recent_device_changes",
    ],

    "UNUSUAL_LOCATION": [
        "distance_from_usual_location",
        "distance_from_previous_transaction",
        "distance_from_user_median_location",
        "distance_from_previous_location",
        "location_frequency_score",
        "user_location_transaction_count",
        "user_region_transaction_count",
        "log_travel_speed",
        "implied_travel_speed_kmph",
    ],

    "MULTIPLE_NEW_MERCHANTS": [
        "is_new_merchant",
        "merchant_transaction_count",
        "merchant_seen_before",
        "recent_unique_merchants",
        "historical_unique_merchants",
        "new_merchants_last_5min",
        "new_merchants_last_15min",
        "new_merchants_last_1hour",
    ],
}

# ============================================================
# VALIDATION
# ============================================================

missing = {}

for group, features in FEATURE_GROUPS.items():
    missing[group] = [
        f for f in features
        if f not in df.columns
    ]

for group, cols in missing.items():
    if cols:
        print(f"\nWARNING — {group} missing:")
        for c in cols:
            print(f"  - {c}")

# ============================================================
# GLOBAL ANOMALY COUNTS
# ============================================================

print("\n" + "=" * 76)
print("ANOMALY TYPE COUNTS")
print("=" * 76)

print(
    df["anomaly_type"]
    .value_counts(dropna=False)
    .to_string()
)

# ============================================================
# DIAGNOSTIC FUNCTION
# ============================================================

all_rows = []

def summarize_group(target, features):

    anomaly = df["anomaly_type"].eq(target)
    normal = ~anomaly

    # Use only rows where the target anomaly type is explicitly present
    # for anomaly statistics. This avoids treating other anomaly types
    # as normal examples.
    anomaly_df = df.loc[anomaly]
    normal_df = df.loc[
        df["anomaly_type"].isna()
        | df["anomaly_type"].eq("NONE")
        | df["anomaly_type"].eq("NORMAL")
    ]

    print("\n" + "=" * 76)
    print(f"{target} FEATURE DIAGNOSTICS")
    print("=" * 76)

    print(
        f"Target rows: {len(anomaly_df):,} | "
        f"Clean normal rows: {len(normal_df):,}"
    )

    rows = []

    for feature in features:

        if feature not in df.columns:
            continue

        a = pd.to_numeric(
            anomaly_df[feature],
            errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).dropna()

        n = pd.to_numeric(
            normal_df[feature],
            errors="coerce"
        ).replace([np.inf, -np.inf], np.nan).dropna()

        if len(a) == 0 or len(n) == 0:
            continue

        a_mean = float(a.mean())
        n_mean = float(n.mean())
        a_median = float(a.median())
        n_median = float(n.median())

        a_p95 = float(a.quantile(0.95))
        n_p95 = float(n.quantile(0.95))

        pooled_std = float(
            np.sqrt(
                (
                    a.var(ddof=1) +
                    n.var(ddof=1)
                ) / 2
            )
        )

        if pooled_std > 1e-12:
            standardized_gap = abs(
                a_mean - n_mean
            ) / pooled_std
        else:
            standardized_gap = 0.0

        # A simple distribution-separation measure.
        # For count/binary features, this is still useful as a diagnostic,
        # but it is NOT a model feature-importance score.
        rows.append({
            "anomaly_type": target,
            "feature": feature,
            "anomaly_mean": a_mean,
            "normal_mean": n_mean,
            "anomaly_median": a_median,
            "normal_median": n_median,
            "anomaly_p95": a_p95,
            "normal_p95": n_p95,
            "standardized_gap": standardized_gap,
            "anomaly_nonzero_rate": float((a != 0).mean()),
            "normal_nonzero_rate": float((n != 0).mean()),
        })

    result = pd.DataFrame(rows)

    if result.empty:
        print("No usable numeric features found.")
        return result

    result = result.sort_values(
        "standardized_gap",
        ascending=False
    )

    display_cols = [
        "feature",
        "anomaly_mean",
        "normal_mean",
        "anomaly_median",
        "normal_median",
        "anomaly_p95",
        "normal_p95",
        "standardized_gap",
        "anomaly_nonzero_rate",
        "normal_nonzero_rate",
    ]

    print(
        result[display_cols]
        .round(4)
        .to_string(index=False)
    )

    print("\nTop separating features:")
    for _, row in result.head(5).iterrows():
        print(
            f"  {row['feature']}: "
            f"gap={row['standardized_gap']:.3f}"
        )

    return result


# ============================================================
# RUN DIAGNOSTICS
# ============================================================

for target in TARGETS:
    result = summarize_group(
        target,
        FEATURE_GROUPS[target]
    )

    if not result.empty:
        all_rows.append(result)

# ============================================================
# SAVE
# ============================================================

if all_rows:
    final = pd.concat(
        all_rows,
        ignore_index=True
    )

    output_file = (
        OUTPUT_DIR /
        "v2_feature_diagnostics.parquet"
    )

    final.to_parquet(
        output_file,
        index=False
    )

    print("\n" + "=" * 76)
    print("DIAGNOSTICS SAVED")
    print("=" * 76)
    print(output_file)

# ============================================================
# SPECIAL CHECKS
# ============================================================

print("\n" + "=" * 76)
print("LABEL / FEATURE CONSISTENCY CHECKS")
print("=" * 76)

# NEW_RECEIVER should normally have a strong relationship with
# is_new_receiver if that field is intended to encode the anomaly.
new_receiver_rows = df["anomaly_type"].eq("NEW_RECEIVER")

if new_receiver_rows.any():
    print("\nNEW_RECEIVER:")
    print(
        "is_new_receiver == 1:",
        f"{df.loc[new_receiver_rows, 'is_new_receiver'].mean():.2%}"
    )

# MULTIPLE_NEW_MERCHANTS should show a corresponding burst of
# new merchants if the label is feature-supported.
multi_merchant_rows = df["anomaly_type"].eq(
    "MULTIPLE_NEW_MERCHANTS"
)

if multi_merchant_rows.any():
    print("\nMULTIPLE_NEW_MERCHANTS:")
    for c in [
        "is_new_merchant",
        "new_merchants_last_5min",
        "new_merchants_last_15min",
        "new_merchants_last_1hour",
    ]:
        if c in df.columns:
            print(
                f"{c}: "
                f"mean={df.loc[multi_merchant_rows, c].mean():.4f}, "
                f"nonzero="
                f"{(df.loc[multi_merchant_rows, c] != 0).mean():.2%}"
            )

# Behavioral drift should have stronger recent-vs-history deviation.
drift_rows = df["anomaly_type"].eq(
    "BEHAVIORAL_DRIFT"
)

if drift_rows.any():
    print("\nBEHAVIORAL_DRIFT:")
    for c in [
        "recent_amount_ratio",
        "amount_zscore",
        "amount_to_user_avg",
        "recent_tx_count_1h",
        "recent_device_changes",
    ]:
        if c in df.columns:
            print(
                f"{c}: "
                f"mean={df.loc[drift_rows, c].mean():.4f}, "
                f"median={df.loc[drift_rows, c].median():.4f}"
            )

# Location anomalies should show meaningful distance / frequency changes.
location_rows = df["anomaly_type"].eq(
    "UNUSUAL_LOCATION"
)

if location_rows.any():
    print("\nUNUSUAL_LOCATION:")
    for c in [
        "distance_from_usual_location",
        "distance_from_user_median_location",
        "distance_from_previous_location",
        "location_frequency_score",
        "log_travel_speed",
    ]:
        if c in df.columns:
            print(
                f"{c}: "
                f"mean={df.loc[location_rows, c].mean():.4f}, "
                f"median={df.loc[location_rows, c].median():.4f}"
            )

print("\n" + "=" * 76)
print("V2 FEATURE DIAGNOSTICS COMPLETE")
print("=" * 76)