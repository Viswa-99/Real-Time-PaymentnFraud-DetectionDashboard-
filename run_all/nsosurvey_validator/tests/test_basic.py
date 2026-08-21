"""Tests for the NSO Survey Data Validation Platform."""

import sys
import os
import json
import tempfile

import pandas as pd
import numpy as np

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.db import Base, engine, get_async_db, get_db
from app.models.anomaly_detector import (
    AnomalyDetectionEngine,
    IsolationForestDetector,
    MahalanobisDetector,
    ProbabilisticClusterDetector,
    StatisticalModel,
    BaseAnomalyDetector,
)
from app.checks.integrity_checks import (
    IntegrityCheckResult,
    ExistentialIntegrityCheck,
    ReferentialIntegrityCheck,
    RangeCheck,
    DuplicateRecordCheck,
    PatternCheck,
)


def test_config():
    """Test configuration loading."""
    assert settings.PROJECT_NAME == "NSO Survey Data Validation Platform"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    print("  test_config: PASSED")


def test_settings_attributes():
    """Test that settings has expected attributes."""
    required_attrs = [
        "POSTGRES_SERVER", "POSTGRES_PORT", "POSTGRES_USER", 
        "POSTGRES_PASSWORD", "POSTGRES_DB", "REDIS_HOST", "REDIS_PORT"
    ]
    for attr in required_attrs:
        assert hasattr(settings, attr), f"Missing setting: {attr}"
    print("  test_settings_attributes: PASSED")


def test_integrity_check_result():
    """Test IntegrityCheckResult model."""
    result = IntegrityCheckResult(
        check_name="test_check",
        passed=True,
        details={"key": "value"},
        affected_rows=5,
        example_violations=[{"col": "val"}],
    )
    assert result.check_name == "test_check"
    assert result.passed == True
    assert result.details == {"key": "value"}
    assert result.affected_rows == 5
    assert len(result.example_violations) == 1
    assert result.to_dict()["check_name"] == "test_check"
    print("  test_integrity_check_result: PASSED")


def test_existential_integrity_check_creation():
    """Test ExistentialIntegrityCheck can be created."""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    check = ExistentialIntegrityCheck(
        session,
        [{"table": "test_table", "column": "test_col"}]
    )
    results = check.execute()
    assert len(results) == 1
    assert isinstance(results[0], IntegrityCheckResult)
    print("  test_existential_integrity_check_creation: PASSED")


def test_referential_integrity_check_creation():
    """Test ReferentialIntegrityCheck can be created."""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    check = ReferentialIntegrityCheck(
        session,
        [{"table": "test_table", "fk_columns": ["ref_col"]}]
    )
    results = check.execute()
    assert len(results) == 1
    assert isinstance(results[0], IntegrityCheckResult)
    print("  test_referential_integrity_check_creation: PASSED")


def test_range_check_creation():
    """Test RangeCheck can be created."""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    check = RangeCheck(
        session,
        [{"table": "test_table", "column": "age", "min_val": 0, "max_val": 120}]
    )
    results = check.execute()
    assert len(results) == 1
    assert isinstance(results[0], IntegrityCheckResult)
    print("  test_range_check_creation: PASSED")


def test_duplicate_record_check_creation():
    """Test DuplicateRecordCheck can be created."""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    check = DuplicateRecordCheck(
        session,
        ["survey_responses.household_id.person_id"]
    )
    results = check.execute()
    assert len(results) == 1
    assert isinstance(results[0], IntegrityCheckResult)
    print("  test_duplicate_record_check_creation: PASSED")


def test_pattern_check_creation():
    """Test PatternCheck can be created."""
    df = pd.DataFrame({
        "col1": [1, 2, 3, 4, 5, 10, 20, 30, 40, 50],
        "col2": [11, 22, 33, 44, 55, 66, 77, 88, 99, 110],
    })
    check = PatternCheck(df, "digit_preference")
    results = check.execute()
    assert len(results) == 1
    assert isinstance(results[0], IntegrityCheckResult)
    print("  test_pattern_check_creation: PASSED")


def test_statistical_model_chi_square():
    """Test StatisticalModel.chi_square_test."""
    observed = pd.Series([10, 20, 30, 40, 50])
    expected = pd.Series([12, 22, 32, 40, 44])
    
    result = StatisticalModel.chi_square_test(observed, expected)
    assert "chi2_statistic" in result
    assert "p_value" in result
    assert "is_significant" in result
    print("  test_statistical_model_chi_square: PASSED")


def test_statistical_model_trend_analysis():
    """Test StatisticalModel.trend_analysis."""
    series = pd.Series([10, 15, 13, 18, 20, 25, 22, 28, 30, 35])
    result = StatisticalModel.trend_analysis(series)
    assert "trend_slope" in result
    assert "r_squared" in result
    assert "is_increasing" in result
    print("  test_statistical_model_trend_analysis: PASSED")


def test_anomaly_detector_creation():
    """Test anomaly detectors can be created."""
    detector = IsolationForestDetector(name="test", contamination=0.1, max_samples=100)
    assert detector.name == "test"
    assert detector.contamination == 0.1
    print("  test_anomaly_detector_creation: PASSED")


def test_anomaly_detection_engine_creation():
    """Test AnomalyDetectionEngine can be created."""
    engine = AnomalyDetectionEngine()
    assert "isolation_forest" in engine.detectors
    assert "mahalanobis" in engine.detectors
    assert "seasonal_esd" in engine.detectors
    assert "gmm" in engine.detectors
    print("  test_anomaly_detection_engine_creation: PASSED")


def test_sample_data_loading():
    """Test that sample data can be loaded and has expected structure."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_dir, "sample_plfs_data.csv")
    
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        assert len(df) > 0
        assert len(df.columns) > 0
        # Check expected columns exist
        expected_cols = ["household_id", "person_id", "age", "monthly_income", "region"]
        for col in expected_cols:
            assert col in df.columns, f"Missing expected column: {col}"
        print(f"  test_sample_data_loading: PASSED ({len(df)} rows, {len(df.columns)} cols)")
    else:
        print("  test_sample_data_loading: SKIPPED (no sample data)")


def test_data_ingestion_api_routes():
    """Test that the FastAPI app has expected routes."""
    from main import app
    
    routes = [route.path for route in app.routes if hasattr(route, "path")]
    expected_prefixes = ["/api/v1", "/ingestion", "/dashboard"]
    
    for prefix in expected_prefixes:
        matching = [r for r in routes if r.startswith(prefix)]
        assert len(matching) > 0, f"No routes found with prefix: {prefix}"
    print("  test_data_ingestion_api_routes: PASSED")


def test_main_import():
    """Test that main module can be imported."""
    from main import app as fastapi_app
    assert fastapi_app is not None
    assert fastapi_app.title == "NSO Survey Data Validation Platform"
    print("  test_main_import: PASSED")


if __name__ == "__main__":
    print("Running NSO Survey Data Validation Platform Tests...")
    print()
    
    test_config()
    test_settings_attributes()
    test_integrity_check_result()
    test_existential_integrity_check_creation()
    test_referential_integrity_check_creation()
    test_range_check_creation()
    test_duplicate_record_check_creation()
    test_pattern_check_creation()
    test_statistical_model_chi_square()
    test_statistical_model_trend_analysis()
    test_anomaly_detector_creation()
    test_anomaly_detection_engine_creation()
    test_sample_data_loading()
    test_data_ingestion_api_routes()
    test_main_import()
    
    print()
    print("All tests passed!")