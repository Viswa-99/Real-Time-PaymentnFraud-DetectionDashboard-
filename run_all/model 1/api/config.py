import os
from pathlib import Path

# Base directories
BASE_DIR = Path(r"C:\Hackathon\model 1")
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Model and config file paths
LAYER1_MODEL_PATH = MODELS_DIR / "layer1_isolation_forest.pkl"
LAYER1_CONFIG_PATH = MODELS_DIR / "layer1_config.json"
LAYER2_MODEL_PATH = MODELS_DIR / "layer2_xgboost.json"
LAYER2_CONFIG_PATH = MODELS_DIR / "layer2_config.json"

# Demo dataset paths
TEST_RESULTS_PATH = OUTPUTS_DIR / "layer2_test_results.parquet"
TEST_FEATURES_PATH = OUTPUTS_DIR / "test_features.parquet"

# Environment variables
ML_API_KEY = os.getenv("ML_API_KEY", None)

def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    origins = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:3000"]
    if raw_origins:
        for o in raw_origins.split(","):
            o = o.strip()
            if o and o not in origins:
                origins.append(o)
    return origins
