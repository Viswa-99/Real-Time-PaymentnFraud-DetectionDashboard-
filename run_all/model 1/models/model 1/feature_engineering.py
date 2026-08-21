from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Hackathon")
DATA_PATH = BASE_DIR / "Dataset" / "synthetic_upi_transactions_v2.csv"

OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_FILE = OUTPUT_DIR / "transactions_features.parquet"

TRAIN_FILE = OUTPUT_DIR / "train_features.parquet"
VAL_FILE = OUTPUT_DIR / "validation_features.parquet"
TEST_FILE = OUTPUT_DIR / "test_features.parquet"


# ============================================================
# EXPECTED RAW COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "transaction_id",
    "user_id",
    "account_id",
    "timestamp",
    "amount",
    "currency",
    "sender_id",
    "sender_type",
    "receiver_id",
    "receiver_name",
    "receiver_type",
    "merchant_id",
    "merchant_category",
    "transaction_type",
    "payment_method",
    "location_latitude",
    "location_longitude",
    "location_region",
    "device_id",
    "device_type",
    "os",
    "ip_address_simulated",
    "is_new_receiver",
    "is_new_device",
    "is_new_merchant",
    "distance_from_usual_location",
    "is_anomaly",
    "anomaly_type",
    "anomaly_severity",

    # V2 precomputed behavioral / contextual features
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
    "user_location_transaction_count",
    "user_region_transaction_count",
    "distance_from_user_median_location",
    "distance_from_previous_location",
    "location_frequency_score",
    "user_receiver_transaction_count",
    "receiver_relationship_age",
    "time_since_receiver_last_transaction",
    "new_receivers_last_5min",
    "new_receivers_last_15min",
    "new_receivers_last_1hour",
    "new_merchants_last_5min",
    "new_merchants_last_15min",
    "new_merchants_last_1hour",
]


TARGET_COLUMNS = [
    "is_anomaly",
    "anomaly_type",
    "anomaly_severity",
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("UPI ANOMALY DETECTION - V2 FEATURE ENGINEERING")
print("=" * 70)

print("\n[1/8] Loading dataset...")

df = pd.read_csv(
    DATA_PATH,
    parse_dates=["timestamp"]
)

print(f"Rows loaded: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# COLUMN VALIDATION
# ============================================================

print("\n[2/8] Validating schema...")

missing_columns = [
    col for col in REQUIRED_COLUMNS
    if col not in df.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    for col in missing_columns:
        print(f"  - {col}")

    print("\nAvailable columns:")
    for col in df.columns:
        print(f"  - {col}")

    raise ValueError("Dataset schema validation failed.")

print("Schema validation: PASSED")


# ============================================================
# BASIC CLEANING / SORTING
# ============================================================

print("\n[3/8] Preparing chronological transaction stream...")

# Remove accidental duplicate transaction IDs if any.
duplicate_count = df["transaction_id"].duplicated().sum()

if duplicate_count:
    print(f"WARNING: Removing {duplicate_count:,} duplicate transaction IDs.")
    df = df.drop_duplicates(
        subset="transaction_id",
        keep="first"
    )

# Sort globally by time.
df = df.sort_values(
    "timestamp",
    kind="mergesort"
).reset_index(drop=True)

# Make sure amount is numeric.
df["amount"] = pd.to_numeric(
    df["amount"],
    errors="coerce"
)

if df["amount"].isna().any():
    raise ValueError("Invalid amount values detected.")

if (df["amount"] <= 0).any():
    raise ValueError("Non-positive transaction amounts detected.")

print(
    f"Date range: "
    f"{df['timestamp'].min()} → {df['timestamp'].max()}"
)


# ============================================================
# 4. BASIC TEMPORAL FEATURES
# ============================================================

print("\n[4/8] Creating transaction-level features...")

df["hour"] = df["timestamp"].dt.hour.astype(np.int8)

df["day_of_week"] = (
    df["timestamp"].dt.dayofweek.astype(np.int8)
)

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(np.int8)

df["log_amount"] = np.log1p(
    df["amount"]
).astype(np.float32)


# ============================================================
# 5. HISTORICAL USER / ENTITY FEATURES
# ============================================================

print("\n[5/8] Creating historical behavioral features...")

# ------------------------------------------------------------
# USER HISTORY
# ------------------------------------------------------------

# Number of transactions BEFORE current transaction.
df["user_history_count"] = (
    df.groupby("user_id", sort=False)
      .cumcount()
      .astype(np.int32)
)

# Previous transaction timestamp.
df["previous_timestamp"] = (
    df.groupby("user_id", sort=False)["timestamp"]
      .shift(1)
)

df["time_since_last_transaction_seconds"] = (
    df["timestamp"] - df["previous_timestamp"]
).dt.total_seconds()

df["has_previous_transaction"] = (
    df["previous_timestamp"].notna()
).astype(np.int8)


# ------------------------------------------------------------
# HISTORICAL USER AMOUNT STATISTICS
# ------------------------------------------------------------

user_group = df.groupby("user_id", sort=False)

# Previous count
count_before = df["user_history_count"].astype(np.float64)

# Cumulative sum INCLUDING current
cumsum_amount = user_group["amount"].cumsum()

# Previous sum = cumulative sum - current amount
sum_before = cumsum_amount - df["amount"]

# Previous average
df["user_avg_amount"] = (
    sum_before / count_before.replace(0, np.nan)
)

# Cumulative squared amount
amount_squared = df["amount"] ** 2

cumsum_squared = (
    amount_squared.groupby(df["user_id"], sort=False)
    .cumsum()
)

sum_squared_before = (
    cumsum_squared - amount_squared
)

# Population variance from historical observations.
variance_before = (
    sum_squared_before / count_before.replace(0, np.nan)
    - df["user_avg_amount"] ** 2
)

variance_before = variance_before.clip(lower=0)

df["user_std_amount"] = np.sqrt(
    variance_before
)

# Amount relative to historical average.
df["amount_to_user_avg"] = (
    df["amount"] /
    df["user_avg_amount"].replace(0, np.nan)
)

# Historical z-score.
df["amount_zscore"] = (
    (df["amount"] - df["user_avg_amount"]) /
    df["user_std_amount"].replace(0, np.nan)
)

# Robustness: z-scores are meaningful only with enough historical
# observations and non-negligible variance. This prevents tiny
# denominators from producing extreme synthetic values.
df.loc[df["user_history_count"] < 2, "amount_zscore"] = np.nan
df.loc[df["user_std_amount"] < 1e-6, "amount_zscore"] = np.nan

# Keep the feature numerically bounded. XGBoost can handle large values,
# but extreme z-scores from sparse histories are not useful behavior signals.
df["amount_zscore"] = df["amount_zscore"].clip(-20, 20)


# ------------------------------------------------------------
# RECEIVER HISTORY
# ------------------------------------------------------------

df["receiver_transaction_count"] = (
    df.groupby(
        ["user_id", "receiver_id"],
        sort=False
    ).cumcount()
    .astype(np.int32)
)

df["receiver_seen_before"] = (
    df["receiver_transaction_count"] > 0
).astype(np.int8)



# ------------------------------------------------------------
# MERCHANT HISTORY
# ------------------------------------------------------------

# Missing merchant IDs should not create a fake merchant entity.
merchant_valid = df["merchant_id"].notna()

df["merchant_transaction_count"] = 0

df.loc[merchant_valid, "merchant_transaction_count"] = (
    df.loc[merchant_valid]
      .groupby(
          ["user_id", "merchant_id"],
          sort=False
      )
      .cumcount()
      .astype(np.int32)
)

df["merchant_seen_before"] = (
    df["merchant_transaction_count"] > 0
).astype(np.int8)

# Respect the dataset's merchant availability flag.
if "merchant_available" in df.columns:
    merchant_available = df["merchant_available"].fillna(0).astype(np.int8)
else:
    merchant_available = merchant_valid.astype(np.int8)

df["merchant_available"] = merchant_available


# ------------------------------------------------------------
# DEVICE HISTORY
# ------------------------------------------------------------

df["device_transaction_count"] = (
    df.groupby(
        ["user_id", "device_id"],
        sort=False
    ).cumcount()
    .astype(np.int32)
)

df["device_seen_before"] = (
    df["device_transaction_count"] > 0
).astype(np.int8)


# ============================================================
# 6. FAST TEMPORAL VELOCITY FEATURES
# ============================================================

print("[6/8] Creating transaction velocity features...")

"""
For each user we calculate historical activity using ONLY
transactions before the current transaction.

Example:

T1 → count in previous 5 minutes = 0
T2 → count based on T1
T3 → count based on T1,T2
...

The current transaction is never included.
"""

df["transactions_last_5min"] = 0
df["transactions_last_15min"] = 0
df["transactions_last_1hour"] = 0
df["amount_last_1hour"] = 0.0


def calculate_user_windows(group):
    """
    Calculate rolling historical counts/sums for one user.

    Uses only transactions strictly before each current
    transaction.
    """

    idx = group.index.to_numpy()

    timestamps = (
        group["timestamp"]
        .astype("int64")
        .to_numpy()
    )

    amounts = (
        group["amount"]
        .to_numpy(dtype=np.float64)
    )

    # nanoseconds
    FIVE_MIN = 5 * 60 * 1_000_000_000
    FIFTEEN_MIN = 15 * 60 * 1_000_000_000
    ONE_HOUR = 60 * 60 * 1_000_000_000

    cumulative_amount = np.concatenate(
        ([0.0], np.cumsum(amounts))
    )

    # Current transaction excluded because right boundary is i.
    left_5 = np.searchsorted(
        timestamps,
        timestamps - FIVE_MIN,
        side="left"
    )

    left_15 = np.searchsorted(
        timestamps,
        timestamps - FIFTEEN_MIN,
        side="left"
    )

    left_60 = np.searchsorted(
        timestamps,
        timestamps - ONE_HOUR,
        side="left"
    )

    positions = np.arange(len(group))

    count_5 = positions - left_5
    count_15 = positions - left_15
    count_60 = positions - left_60

    amount_60 = (
        cumulative_amount[positions]
        - cumulative_amount[left_60]
    )

    return (
        idx,
        count_5,
        count_15,
        count_60,
        amount_60
    )


print("Calculating per-user rolling windows...")

for user_id, group in df.groupby("user_id", sort=False):
    (
        idx,
        count_5,
        count_15,
        count_60,
        amount_60
    ) = calculate_user_windows(group)

    df.loc[idx, "transactions_last_5min"] = count_5
    df.loc[idx, "transactions_last_15min"] = count_15
    df.loc[idx, "transactions_last_1hour"] = count_60
    df.loc[idx, "amount_last_1hour"] = amount_60


# ============================================================
# 7. LOCATION / TRAVEL FEATURES
# ============================================================

print("\n[7/8] Creating location/travel features...")

# Use dataset-provided historical distance if available.
df["distance_from_usual_location"] = pd.to_numeric(
    df["distance_from_usual_location"],
    errors="coerce"
)

df["distance_from_previous_transaction"] = pd.to_numeric(
    df.get(
        "distance_from_previous_transaction",
        pd.Series(np.nan, index=df.index)
    ),
    errors="coerce"
)

# Time between transactions already calculated.
df["time_since_last_transaction_seconds"] = (
    df["time_since_last_transaction_seconds"]
    .astype(float)
)

# Use provided travel speed if present.
if "implied_travel_speed_kmph" in df.columns:

    travel_speed = pd.to_numeric(
        df["implied_travel_speed_kmph"],
        errors="coerce"
    )

else:

    travel_speed = pd.Series(
        np.nan,
        index=df.index
    )

# Never allow negative values.
travel_speed = travel_speed.clip(lower=0)

# Log transformation prevents extreme synthetic speeds from
# dominating the model.
df["log_travel_speed"] = np.log1p(
    travel_speed
).astype(np.float32)


# ============================================================
# 8. FINAL FEATURE SELECTION
# ============================================================

print("\n[8/8] Preparing final feature matrix...")

FEATURE_COLUMNS = [
    # Transaction
    "amount",
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


# Check every feature exists.
missing_features = [
    col for col in FEATURE_COLUMNS
    if col not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing engineered features: {missing_features}"
    )


# ------------------------------------------------------------
# CLEAN NUMERIC VALUES
# ------------------------------------------------------------

feature_df = df[
    ["transaction_id", "user_id", "timestamp"]
    + FEATURE_COLUMNS
    + TARGET_COLUMNS
].copy()

# Merchant metadata is unavailable for these transactions.
# Keep merchant_available to distinguish "unknown merchant"
# from "known merchant that is new".
feature_df["is_new_merchant"] = (
    feature_df["is_new_merchant"]
    .fillna(0)
    .astype(np.int8)
)
# Replace infinities generated by divisions.
feature_df.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)


# First transaction has no historical average/std.
# These will be handled using explicit history availability.
feature_df["has_user_amount_history"] = (
    feature_df["user_history_count"] > 0
).astype(np.int8)


# Fill historical amount features for cold-start users.
# Neutral values are preferable to inventing historical behavior.
for col in [
    "user_avg_amount",
    "user_std_amount",
    "amount_to_user_avg",
    "amount_zscore",
]:
    feature_df[col] = feature_df[col].fillna(0)


feature_df["time_since_last_transaction_seconds"] = (
    feature_df["time_since_last_transaction_seconds"]
    .fillna(0)
)

feature_df["distance_from_previous_transaction"] = (
    feature_df["distance_from_previous_transaction"]
    .fillna(0)
)

feature_df["log_travel_speed"] = (
    feature_df["log_travel_speed"]
    .fillna(0)
)

# ------------------------------------------------------------
# V2 behavioral feature cleaning
# ------------------------------------------------------------
V2_COUNT_FEATURES = [
    "recent_tx_count_1h",
    "recent_tx_count_24h",
    "recent_unique_receivers",
    "historical_unique_receivers",
    "recent_unique_merchants",
    "historical_unique_merchants",
    "recent_device_changes",
    "user_location_transaction_count",
    "user_region_transaction_count",
    "user_receiver_transaction_count",
    "new_receivers_last_5min",
    "new_receivers_last_15min",
    "new_receivers_last_1hour",
    "new_merchants_last_5min",
    "new_merchants_last_15min",
    "new_merchants_last_1hour",
]

V2_NUMERIC_FEATURES = [
    "recent_avg_amount_5tx",
    "historical_avg_amount",
    "recent_amount_ratio",
    "historical_tx_frequency",
    "distance_from_user_median_location",
    "distance_from_previous_location",
    "location_frequency_score",
    "receiver_relationship_age",
    "time_since_receiver_last_transaction",
]

# Cold-start / unavailable-history values are represented explicitly by
# neutral values. The history/count features above tell the model how much
# history actually exists.
for col in V2_COUNT_FEATURES:
    feature_df[col] = pd.to_numeric(
        feature_df[col], errors="coerce"
    ).fillna(0)

for col in V2_NUMERIC_FEATURES:
    feature_df[col] = pd.to_numeric(
        feature_df[col], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

# Neutral cold-start values.
for col in [
    "recent_avg_amount_5tx",
    "historical_avg_amount",
    "recent_amount_ratio",
    "historical_tx_frequency",
    "distance_from_user_median_location",
    "distance_from_previous_location",
    "location_frequency_score",
    "receiver_relationship_age",
    "time_since_receiver_last_transaction",
]:
    feature_df[col] = feature_df[col].fillna(0)

# Ratios can explode for tiny historical averages. Bound them to a
# numerically useful range while retaining strong drift information.
feature_df["recent_amount_ratio"] = (
    feature_df["recent_amount_ratio"].clip(0, 100)
)

# Validate that all model features are finite after cleaning.
nonfinite = ~np.isfinite(
    feature_df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
)

if nonfinite.any():
    bad_rows, bad_cols = np.where(nonfinite)
    raise ValueError(
        f"Non-finite V2 feature values remain: "
        f"{len(bad_rows):,} cells."
    )


# ------------------------------------------------------------
# TEMPORAL SPLIT
# ------------------------------------------------------------

TRAIN_END = pd.Timestamp("2025-08-31 23:59:59")
VAL_END = pd.Timestamp("2025-10-31 23:59:59")

train_mask = feature_df["timestamp"] <= TRAIN_END

val_mask = (
    (feature_df["timestamp"] > TRAIN_END)
    & (feature_df["timestamp"] <= VAL_END)
)

test_mask = feature_df["timestamp"] > VAL_END


train_df = feature_df.loc[train_mask].copy()
val_df = feature_df.loc[val_mask].copy()
test_df = feature_df.loc[test_mask].copy()


# ============================================================
# SAVE
# ============================================================

print("\nSaving feature datasets...")

feature_df.to_parquet(
    FEATURE_FILE,
    index=False
)

train_df.to_parquet(
    TRAIN_FILE,
    index=False
)

val_df.to_parquet(
    VAL_FILE,
    index=False
)

test_df.to_parquet(
    TEST_FILE,
    index=False
)


# ============================================================
# VALIDATION REPORT
# ============================================================

print("\n" + "=" * 70)
print("FEATURE ENGINEERING VALIDATION")
print("=" * 70)

print(f"\nTotal rows:       {len(feature_df):,}")
print(f"Training rows:    {len(train_df):,}")
print(f"Validation rows:  {len(val_df):,}")
print(f"Test rows:        {len(test_df):,}")

print("\nSplit dates:")

print(
    f"Train: "
    f"{train_df['timestamp'].min()} → "
    f"{train_df['timestamp'].max()}"
)

print(
    f"Validation: "
    f"{val_df['timestamp'].min()} → "
    f"{val_df['timestamp'].max()}"
)

print(
    f"Test: "
    f"{test_df['timestamp'].min()} → "
    f"{test_df['timestamp'].max()}"
)

print("\nFeature count:")
print(len(FEATURE_COLUMNS))

print("\nFeature missing values:")

missing_report = (
    feature_df[FEATURE_COLUMNS]
    .isna()
    .sum()
    .sort_values(ascending=False)
)

print(
    missing_report[
        missing_report > 0
    ].to_string()
    if (missing_report > 0).any()
    else "No missing feature values."
)


print("\nAnomaly distribution:")

print(
    feature_df["is_anomaly"]
    .value_counts(normalize=True)
    .sort_index()
)


print("\nSelected feature statistics:")

print(
    feature_df[
        [
            "amount",
            "user_history_count",
            "amount_to_user_avg",
            "amount_zscore",
            "transactions_last_5min",
            "transactions_last_15min",
            "transactions_last_1hour",
            "distance_from_usual_location",
            "log_travel_speed",
            "recent_amount_ratio",
            "recent_tx_count_1h",
            "recent_unique_receivers",
            "user_receiver_transaction_count",
            "new_receivers_last_15min",
            "new_merchants_last_15min",
            "location_frequency_score",
            "distance_from_user_median_location",
        ]
    ].describe().round(3)
)


print("\nOutput files:")

print(FEATURE_FILE)
print(TRAIN_FILE)
print(VAL_FILE)
print(TEST_FILE)

print("\n" + "=" * 70)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 70)