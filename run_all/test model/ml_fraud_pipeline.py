"""
ML Pipeline Preparation for Credit Card Fraud Detection
Dataset: AIML Dataset (6.3M rows, highly imbalanced fraud detection)
Target: isFraud (1 = fraud, 0 = legitimate)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
import warnings
import joblib
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek
warnings.filterwarnings("ignore")
sns.set(style="whitegrid", context="notebook")


def load_and_preprocess(data_path="AIML Dataset.csv", sample_size=100000):
    """
    Load dataset and perform preprocessing for ML training.
    
    Parameters:
    - data_path: path to CSV file
    - sample_size: number of rows to sample (None = full dataset, int = sample)
    
    Returns:
    - X_train, X_test, y_train, y_test: scaled train/test splits
    - preprocessors: dict with scaler and encoders
    """
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    # Remove transactions where the fraud label is missing
    missing_fraud = df['isFraud'].isna().sum()
    print(f"Missing isFraud values: {missing_fraud}")

    df = df.dropna(subset=['isFraud']).copy()

    print(f"Dataset shape after removing missing labels: {df.shape}")
    if sample_size and sample_size < len(df):
        print(f"Sampling {sample_size} rows from {len(df)} total...")
        df = df.sample(n=sample_size, random_state=42)
        print(f"Sampled shape: {df.shape}")
    
    print(f"Initial shape: {df.shape}")
    
    # Drop identifier columns - they're not predictive features
    df = df.drop(['nameOrig', 'nameDest'], axis=1)
    
    # Feature engineering: balance differences
    df['balanceDiffOrig'] = df['oldbalanceOrg'] - df['newbalanceOrig']
    df['balanceDiffDest'] = df['newbalanceDest'] - df['oldbalanceDest']
    
    # Encode categorical 'type' column
    le = LabelEncoder()
    df['type_encoded'] = le.fit_transform(df['type'])
    df = df.drop(['type'], axis=1)  # Drop original categorical
    
    # Define features and target
    X = df.drop(['isFraud', 'isFlaggedFraud'], axis=1)
    y = df['isFraud']
    
    print(f"\nFeatures: {X.shape[1]}, Samples: {X.shape[0]}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    print(f"Fraud rate: {y.mean()*100:.4f}%")
    
    # Scale numeric features
    scaler = StandardScaler()
    numeric_features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                        'oldbalanceDest', 'newbalanceDest', 'balanceDiffOrig', 'balanceDiffDest']
    
    # Only scale columns that exist (in case of sampling)
    available_numeric = [c for c in numeric_features if c in X.columns]
    X[available_numeric] = scaler.fit_transform(X[available_numeric])
    
    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {X_train.shape} | Fraud rate: {y_train.mean()*100:.4f}%")
    print(f"Test set: {X_test.shape} | Fraud rate: {y_test.mean()*100:.4f}%")
    
    preprocessors = {
        'scaler': scaler,
        'label_encoder': le,
        'feature_names': X.columns.tolist(),
        'numeric_features': available_numeric
    }
    
    return X_train, X_test, y_train, y_test, preprocessors


def train_models(X_train, y_train, X_test, y_test, use_smote=False):
    """
    Train multiple ML models for fraud detection.
    
    Parameters:
    - use_smote: whether to apply SMOTE for class imbalance
    
    Returns:
    - dict of trained models with metrics
    """
    print("\n--- Training Models ---")
    
    # Handle class imbalance with SMOTE if requested
    if use_smote:
        print("Applying SMOTE for class balancing...")
        smote = SMOTE(random_state=42, k_neighbors=5)
        X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
        print(f"After SMOTE: {len(y_train_res)} samples, fraud rate: {y_train_res.mean()*100:.2f}%")
    else:
        X_train_res, y_train_res = X_train, y_train
    
    models = {}
    
    # 1. Logistic Regression (baseline)
    print("Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42, solver='lbfgs')
    lr.fit(X_train_res, y_train_res)
    lr_pred = lr.predict(X_test)
    lr_auc = roc_auc_score(y_test, lr_pred)
    models['Logistic Regression'] = {
        'model': lr,
        'auc': lr_auc,
        'preds': lr_pred,
        'report': classification_report(y_test, lr_pred, output_dict=True, digits=3)
    }
    print(f"Logistic Regression AUC: {lr_auc:.4f}")
    
    # 2. Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', 
                                random_state=42, n_jobs=-1, max_depth=10)
    rf.fit(X_train_res, y_train_res)
    rf_pred = rf.predict(X_test)
    rf_auc = roc_auc_score(y_test, rf_pred)
    models['Random Forest'] = {
        'model': rf,
        'auc': rf_auc,
        'preds': rf_pred,
        'report': classification_report(y_test, rf_pred, output_dict=True, digits=3)
    }
    print(f"Random Forest AUC: {rf_auc:.4f}")
    
    # 3. Gradient Boosting
    print("Training Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=30, random_state=42, max_depth=3)
    gb.fit(X_train_res, y_train_res)
    gb_pred = gb.predict(X_test)
    gb_auc = roc_auc_score(y_test, gb_pred)
    models['Gradient Boosting'] = {
        'model': gb,
        'auc': gb_auc,
        'preds': gb_pred,
        'report': classification_report(y_test, gb_pred, output_dict=True, digits=3)
    }
    print(f"Gradient Boosting AUC: {gb_auc:.4f}")
    
    # Sort by AUC (descending)
    models = dict(sorted(models.items(), key=lambda x: x[1]['auc'], reverse=True))
    
    return models, X_test, y_test


def evaluate_models(models, X_test, y_test):
    """Evaluate and compare all trained models."""
    print("\n=== Model Comparison ===")
    for name, info in models.items():
        print(f"\n{name}:")
        print(f"  AUC: {info['auc']:.4f}")
        print(f"  Classification Report:")
        report = info['report']
        for cls in [0, 1]:
            if cls in report:
                print(f"    Class {cls}: Precision={report[cls]['precision']:.3f}, "
                      f"Recall={report[cls]['recall']:.3f}, F1={report[cls]['f1-score']:.3f}")
        print(f"    Accuracy: {report['accuracy']:.4f}")
    
    # Return best model
    best_name = list(models.keys())[0]
    best_auc = models[best_name]['auc']
    for name, info in models.items():
        if info['auc'] > best_auc:
            best_auc = info['auc']
            best_name = name
    
    print(f"\nBest model: {best_name} with AUC={best_auc:.4f}")
    return best_name, models


def main():
    """Main pipeline execution."""
    print("=" * 60)
    print("FRAUD DETECTION ML PIPELINE")
    print("=" * 60)
    
    # Step 1: Load and preprocess
    # Use full dataset or set sample_size for quicker testing
    # sample_size = 100000  # Uncomment for quick testing
    sample_size = None  # Full dataset
    
    X_train, X_test, y_train, y_test, preprocessors = load_and_preprocess(
        sample_size=sample_size
    )
    
    # Save preprocessors for later use
    joblib.dump(preprocessors, "ml_preprocessors.pkl")
    print("\nPreprocessors saved to 'ml_preprocessors.pkl'")
    
    # Step 2: Train models (without SMOTE first, then with)
    models_baseline, X_test, y_test = train_models(
        X_train, y_train, X_test, y_test, use_smote=False
    )
    
    models_balanced, _, _ = train_models(
        X_train, y_train, X_test, y_test, use_smote=True
    )
    
    # Step 3: Evaluate and compare
    print("\n=== BASELINE MODELS (No SMOTE) ===")
    best_baseline, models_baseline = evaluate_models(models_baseline, X_test, y_test)
    
    print("\n=== BALANCED MODELS (With SMOTE) ===")
    best_balanced, models_balanced = evaluate_models(models_balanced, X_test, y_test)
    
    # Step 4: Save best model
    # Determine which is better
    best_baseline_auc = models_baseline[best_baseline]['auc'] if best_baseline in models_baseline else 0
    best_balanced_auc = models_balanced[best_balanced]['auc'] if best_balanced in models_balanced else 0
    
    if best_balanced_auc > best_baseline_auc:
        best_model_name = best_balanced
        best_model = models_balanced[best_balanced]['model']
        print(f"\n>>> Best model is balanced (SMOTE) with AUC {best_balanced_auc:.4f}")
    else:
        best_model_name = best_baseline
        best_model = models_baseline[best_baseline]['model']
        print(f"\n>>> Best model is baseline with AUC {best_baseline_auc:.4f}")
    
    joblib.dump({
        'model': best_model,
        'model_name': best_model_name,
        'preprocessors': preprocessors
    }, "best_fraud_model.pkl")
    
    print(f"\nBest model saved to 'best_fraud_model.pkl'")
    print("=" * 60)
    print("Pipeline complete!")


if __name__ == "__main__":
    main()