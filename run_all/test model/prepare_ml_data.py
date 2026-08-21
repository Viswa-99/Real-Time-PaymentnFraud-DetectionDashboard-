import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import warnings
import joblib
warnings.filterwarnings("ignore")
sns.set(style="whitegrid")

# Load data
df = pd.read_csv("AIML Dataset.csv")
print(f"Dataset shape: {df.shape}")

# Basic preprocessing
# Drop name fields - they're identifiers, not features
df = df.drop(['nameOrig', 'nameDest'], axis=1)

# Feature engineering: balance differences
df['balanceDiffOrig'] = df['oldbalanceOrg'] - df['newbalanceOrig']
df['balanceDiffDest'] = df['newbalanceDest'] - df['oldbalanceDest']

# Encode categorical 'type' column
le = LabelEncoder()
df['type_encoded'] = le.fit_transform(df['type'])
print(f"Type classes: {le.classes_.tolist()}")

# Drop original categorical column since we have type_encoded
df = df.drop(['type'], axis=1)

# Define features (X) and target (y)
X = df.drop(['isFraud', 'isFlaggedFraud'], axis=1)
y = df['isFraud']

print(f"\nFeatures shape: {X.shape}")
print(f"Target distribution:\n{y.value_counts()}")

# Scale numeric features
scaler = StandardScaler()
numeric_features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                    'oldbalanceDest', 'newbalanceDest', 'balanceDiffOrig', 'balanceDiffDest']
X[numeric_features] = scaler.fit_transform(X[numeric_features])

# Train/test split - important with imbalanced data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain set: {X_train.shape}, Fraud rate: {y_train.mean()*100:.4f}%")
print(f"Test set: {X_test.shape}, Fraud rate: {y_test.mean()*100:.4f}%")

# Save processed data for training
X_train.to_csv("X_train.csv", index=False)
X_test.to_csv("X_test.csv", index=False)
y_train.to_csv("y_train.csv", index=False)
y_test.to_csv("y_test.csv", index=False)

# Save the preprocessor info for later use
joblib.dump({
    'scaler': scaler,
    'label_encoder': le,
    'feature_names': X.columns.tolist()
}, "preprocessors.pkl")

print("\nPreprocessing complete. Files saved:")
print("  - X_train.csv, X_test.csv, y_train.csv, y_test.csv")
print("  - preprocessors.pkl")

# Quick model training demo
print("\n--- Training Quick Models ---")

# Logistic Regression
lr = LogisticRegression(max_iter=1000, class_weight='balanced')
lr.fit(X_train, y_train)
lr_pred = lr.predict(X_test)
lr_auc = roc_auc_score(y_test, lr_pred)
print(f"Logistic Regression - AUC: {lr_auc:.4f}")
print(classification_report(y_test, lr_pred, digits=4))

# Random Forest
rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_auc = roc_auc_score(y_test, rf_pred)
print(f"Random Forest - AUC: {rf_auc:.4f}")
print(classification_report(y_test, rf_pred, digits=4))