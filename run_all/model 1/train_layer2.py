from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, roc_auc_score, confusion_matrix

BASE_DIR = Path(r"C:\Hackathon")
OUTPUT_DIR = BASE_DIR / "model 1" / "outputs"
MODEL_DIR = BASE_DIR / "model 1" / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = OUTPUT_DIR / "train_features.parquet"
VAL_FILE = OUTPUT_DIR / "validation_features.parquet"
TEST_FILE = OUTPUT_DIR / "test_features.parquet"
L1_TRAIN_FILE = OUTPUT_DIR / "layer1_train_scores.parquet"
L1_VAL_FILE = OUTPUT_DIR / "layer1_validation_scores.parquet"
L1_TEST_FILE = OUTPUT_DIR / "layer1_test_scores.parquet"

MODEL_FILE = MODEL_DIR / "layer2_xgboost.json"
CONFIG_FILE = MODEL_DIR / "layer2_config.json"
VAL_RESULT_FILE = OUTPUT_DIR / "layer2_validation_results.parquet"
TEST_RESULT_FILE = OUTPUT_DIR / "layer2_test_results.parquet"

print("=" * 70)
print("LAYER 2 — XGBOOST RISK MODEL")
print("=" * 70)

print("\nLoading datasets...")
train = pd.read_parquet(TRAIN_FILE)
val = pd.read_parquet(VAL_FILE)
test = pd.read_parquet(TEST_FILE)
l1_train = pd.read_parquet(L1_TRAIN_FILE)
l1_val = pd.read_parquet(L1_VAL_FILE)
l1_test = pd.read_parquet(L1_TEST_FILE)

print(f"Train:      {len(train):,}")
print(f"Validation: {len(val):,}")
print(f"Test:       {len(test):,}")

print("\nMerging Layer 1 scores...")

def merge_l1(base, scores, name):
    required = {"transaction_id", "layer1_anomaly_score"}
    missing = required - set(scores.columns)
    if missing:
        raise ValueError(f"{name} missing: {sorted(missing)}")
    if scores["transaction_id"].duplicated().any():
        raise ValueError(f"{name} contains duplicate transaction_id values.")
    out = base.merge(
        scores[["transaction_id", "layer1_anomaly_score"]],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    if out["layer1_anomaly_score"].isna().any():
        raise ValueError(f"{name}: missing Layer 1 scores after merge.")
    return out

train = merge_l1(train, l1_train, "Train")
val = merge_l1(val, l1_val, "Validation")
test = merge_l1(test, l1_test, "Test")

# Automatically use all numeric V2 engineered features plus Layer 1 score.
# Exclude identifiers, labels, timestamps, and anomaly metadata.
EXCLUDE = {
    "transaction_id", "user_id", "account_id", "timestamp",
    "is_anomaly", "anomaly_type", "anomaly_severity",
    "layer1_prediction",
}

FEATURES = [
    c for c in train.columns
    if c not in EXCLUDE and pd.api.types.is_numeric_dtype(train[c])
]

print(f"\nFeature count: {len(FEATURES)}")

if len(FEATURES) != 55:
    raise ValueError(
        f"Expected 55 Layer 2 features "
        f"(54 transaction/behavioral + Layer 1 score), "
        f"got {len(FEATURES)}.\nFeatures: {FEATURES}"
    )

for name, frame in [("Train", train), ("Validation", val), ("Test", test)]:
    missing = [c for c in FEATURES if c not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing features: {missing}")
    values = frame[FEATURES].astype(np.float64).to_numpy()
    if not np.isfinite(values).all():
        raise ValueError(f"{name} contains non-finite feature values.")

print("Feature schema: PASSED")

X_train = train[FEATURES].astype(np.float32)
X_val = val[FEATURES].astype(np.float32)
X_test = test[FEATURES].astype(np.float32)

y_train = train["is_anomaly"].astype(np.int8).to_numpy()
y_val = val["is_anomaly"].astype(np.int8).to_numpy()
y_test = test["is_anomaly"].astype(np.int8).to_numpy()

negative = int((y_train == 0).sum())
positive = int((y_train == 1).sum())
scale_pos_weight = negative / positive

print(f"\nTraining anomaly rate: {y_train.mean():.4%}")
print(f"Validation anomaly rate: {y_val.mean():.4%}")
print(f"Test anomaly rate: {y_test.mean():.4%}")
print(f"scale_pos_weight: {scale_pos_weight:.2f}")

print("\nCreating XGBoost model...")

model = xgb.XGBClassifier(
    n_estimators=600,
    max_depth=7,
    learning_rate=0.08,
    min_child_weight=3,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_alpha=0.05,
    reg_lambda=1.0,
    objective="binary:logistic",
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    tree_method="hist",
    device="cuda",
    random_state=42,
    n_jobs=8,
    early_stopping_rounds=40,
)

print("\nStarting GPU training...")
print("Device: CUDA")
start = time.perf_counter()

model.fit(
    X_train,
    y_train,
    eval_set=[(X_train, y_train), (X_val, y_val)],
    verbose=False,
)

training_time = time.perf_counter() - start
print(f"Training time: {training_time:.2f} seconds")

best_iteration = getattr(model, "best_iteration", None)
if best_iteration is not None:
    print(f"Best iteration: {best_iteration}")

print("\nGenerating predictions...")

# Use CUDA-backed DMatrix for inference to avoid the CPU/CUDA mismatch warning.
booster = model.get_booster()

# XGBoost 3.4.1: DMatrix does not accept device=.
# The model itself is already configured for CUDA.
val_probability = model.predict_proba(
    X_val,
    validate_features=True
)[:, 1]

test_probability = model.predict_proba(
    X_test,
    validate_features=True
)[:, 1]

print("\nSearching validation threshold...")

thresholds = np.linspace(0.05, 0.99, 189)
best_threshold = None
best_f1 = -1.0
threshold_rows = []

for threshold in thresholds:
    pred = (val_probability >= threshold).astype(np.int8)
    precision = precision_score(y_val, pred, zero_division=0)
    recall = recall_score(y_val, pred, zero_division=0)
    f1 = f1_score(y_val, pred, zero_division=0)

    threshold_rows.append({
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "flagged": int(pred.sum()),
    })

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = float(threshold)

print(f"\nBest validation threshold: {best_threshold:.3f}")
print(f"Best validation F1: {best_f1:.4f}")

val_pred = (val_probability >= best_threshold).astype(np.int8)
test_pred = (test_probability >= best_threshold).astype(np.int8)

val_precision = precision_score(y_val, val_pred, zero_division=0)
val_recall = recall_score(y_val, val_pred, zero_division=0)
val_f1 = f1_score(y_val, val_pred, zero_division=0)
val_pr_auc = average_precision_score(y_val, val_probability)
val_roc_auc = roc_auc_score(y_val, val_probability)
val_cm = confusion_matrix(y_val, val_pred)

print("\n" + "=" * 70)
print("LAYER 2 VALIDATION")
print("=" * 70)
print(f"Threshold : {best_threshold:.3f}")
print(f"Precision : {val_precision:.4f}")
print(f"Recall    : {val_recall:.4f}")
print(f"F1        : {val_f1:.4f}")
print(f"PR-AUC    : {val_pr_auc:.4f}")
print(f"ROC-AUC   : {val_roc_auc:.4f}")
print("\nConfusion Matrix:")
print(val_cm)

test_precision = precision_score(y_test, test_pred, zero_division=0)
test_recall = recall_score(y_test, test_pred, zero_division=0)
test_f1 = f1_score(y_test, test_pred, zero_division=0)
test_pr_auc = average_precision_score(y_test, test_probability)
test_roc_auc = roc_auc_score(y_test, test_probability)
test_cm = confusion_matrix(y_test, test_pred)

print("\n" + "=" * 70)
print("LAYER 2 TEST")
print("=" * 70)
print(f"Threshold : {best_threshold:.3f}")
print(f"Precision : {test_precision:.4f}")
print(f"Recall    : {test_recall:.4f}")
print(f"F1        : {test_f1:.4f}")
print(f"PR-AUC    : {test_pr_auc:.4f}")
print(f"ROC-AUC   : {test_roc_auc:.4f}")
print("\nConfusion Matrix:")
print(test_cm)

print("\nSaving Layer 2 model...")
model.save_model(MODEL_FILE)

val_results = val[
    ["transaction_id", "user_id", "timestamp",
     "is_anomaly", "anomaly_type", "anomaly_severity"]
].copy()
val_results["layer1_anomaly_score"] = val["layer1_anomaly_score"].to_numpy()
val_results["risk_probability"] = val_probability
val_results["risk_score"] = val_probability * 100.0
val_results["layer2_prediction"] = val_pred

test_results = test[
    ["transaction_id", "user_id", "timestamp",
     "is_anomaly", "anomaly_type", "anomaly_severity"]
].copy()
test_results["layer1_anomaly_score"] = test["layer1_anomaly_score"].to_numpy()
test_results["risk_probability"] = test_probability
test_results["risk_score"] = test_probability * 100.0
test_results["layer2_prediction"] = test_pred

val_results.to_parquet(VAL_RESULT_FILE, index=False)
test_results.to_parquet(TEST_RESULT_FILE, index=False)
pd.DataFrame(threshold_rows).to_parquet(
    OUTPUT_DIR / "layer2_threshold_analysis.parquet", index=False
)

config = {
    "model": "XGBClassifier",
    "device": "cuda",
    "features": FEATURES,
    "feature_count": len(FEATURES),
    "threshold": best_threshold,
    "scale_pos_weight": float(scale_pos_weight),
    "training_time_seconds": training_time,
    "best_iteration": int(best_iteration) if best_iteration is not None else None,
    "validation": {
        "precision": float(val_precision),
        "recall": float(val_recall),
        "f1": float(val_f1),
        "pr_auc": float(val_pr_auc),
        "roc_auc": float(val_roc_auc),
    },
    "test": {
        "precision": float(test_precision),
        "recall": float(test_recall),
        "f1": float(test_f1),
        "pr_auc": float(test_pr_auc),
        "roc_auc": float(test_roc_auc),
    },
}

with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=4)

print("\n" + "=" * 70)
print("LAYER 2 COMPLETE")
print("=" * 70)
print(f"Model: {MODEL_FILE}")
print(f"Config: {CONFIG_FILE}")
print(f"Validation results: {VAL_RESULT_FILE}")
print(f"Test results: {TEST_RESULT_FILE}")
print(f"Threshold analysis: {OUTPUT_DIR / 'layer2_threshold_analysis.parquet'}")