import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score, confusion_matrix
import lightgbm as lgb

# -------------------------------------------------------------
# 1. Feature Engineering
# -------------------------------------------------------------
# Balance discrepancies
df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']

# Ratio of transaction amount to account balance
df['amount_to_oldBalanceOrig'] = df['amount'] / (df['oldbalanceOrg'] + 1e-5)

# One-hot encode the transaction type
df = pd.get_dummies(df, columns=['type'], drop_first=True)

# Define feature columns and target
features_to_drop = ['isFraud', 'isFlaggedFraud', 'nameOrig', 'nameDest']
X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
y = df['isFraud']

# -------------------------------------------------------------
# 2. Time-Based Splitting
# -------------------------------------------------------------
# Sort chronologically by 'step' if available, otherwise preserve order
if 'step' in X.columns:
    X = X.sort_values(by='step')
    y = y.loc[X.index]

# Chronological 80/20 train/test split
split_idx = int(len(X) * 0.80)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# -------------------------------------------------------------
# 3. Model Configuration & Training
# -------------------------------------------------------------
# Calculate positive class weighting
scale_pos = (len(y_train) - sum(y_train)) / sum(y_train)

model = lgb.LGBMClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    num_leaves=31,
    scale_pos_weight=scale_pos,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    eval_metric='average_precision',
    callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=True)]
)

# -------------------------------------------------------------
# 4. Evaluation & Metrics
# -------------------------------------------------------------
y_pred_proba = model.predict_proba(X_test)[:, 1]

# Default 0.5 decision threshold
y_pred = (y_pred_proba >= 0.5).astype(int)

print("\n--- Model Evaluation ---")
print(f"ROC-AUC Score:  {roc_auc_score(y_test, y_pred_proba):.4f}")
print(f"PR-AUC Score:   {average_precision_score(y_test, y_pred_proba):.4f}")
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred, digits=4))