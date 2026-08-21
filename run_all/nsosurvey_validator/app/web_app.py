from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import asyncio

from app.core.db import get_async_db, engine, Base, SessionLocal
from app.core.config import settings
from app.ingestion.api_ingestion import router as ingestion_router
from app.checks.integrity_checks import (
    ExistentialIntegrityCheck,
    ReferentialIntegrityCheck,
    RangeCheck,
    DuplicateRecordCheck,
    PatternCheck,
)
from app.models.anomaly_detector import AnomalyDetectionEngine, StatisticalModel

app = FastAPI(
    title="NSO Survey Data Validation Platform",
    description="Intelligent survey data validation using probabilistic and machine learning techniques",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include ingestion router
app.include_router(ingestion_router)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "NSO Survey Data Validation Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "survey-validation-platform"}


# --- Integrity Checks ---

@app.post("/checks/existential/", response_model=List[dict])
async def run_existential_checks(
    db: Session = Depends(get_db),
    critical_columns: Optional[List[dict]] = None
):
    """Run existential integrity checks (no nulls in critical fields)."""
    if critical_columns is None:
        # Default critical columns - would be configured per survey
        critical_columns = [
            {"table": "survey_responses", "column": "household_id"},
            {"table": "survey_responses", "column": "person_id"},
        ]
    
    check = ExistentialIntegrityCheck(db, critical_columns)
    results = check.execute()
    return [r.to_dict() for r in results]


@app.post("/checks/referential/", response_model=List[dict])
async def run_referential_checks(
    db: Session = Depends(get_db),
    fk_map: Optional[List[dict]] = None
):
    """Run referential integrity checks."""
    if fk_map is None:
        fk_map = [
            {"table": "survey_responses", "fk_columns": ["district_id"], "ref_table": "districts", "ref_column": "district_id"},
        ]
    
    check = ReferentialIntegrityCheck(db, fk_map)
    results = check.execute()
    return [r.to_dict() for r in results]


@app.post("/checks/range/", response_model=List[dict])
async def run_range_checks(
    db: Session = Depends(get_db),
    range_rules: Optional[List[dict]] = None
):
    """Run range-based integrity checks."""
    if range_rules is None:
        range_rules = [
            {"table": "survey_responses", "column": "age", "min_val": 0, "max_val": 120},
            {"table": "survey_responses", "column": "household_income", "min_val": 0, "max_val": 1000000},
        ]
    
    check = RangeCheck(db, range_rules)
    results = check.execute()
    return [r.to_dict() for r in results]


@app.post("/checks/duplicates/", response_model=List[dict])
async def run_duplicate_checks(
    db: Session = Depends(get_db),
    business_keys: Optional[List[str]] = None
):
    """Run duplicate record checks based on business keys."""
    if business_keys is None:
        business_keys = ["survey_responses.household_id.person_id"]
    
    check = DuplicateRecordCheck(db, business_keys)
    results = check.execute()
    return [r.to_dict() for r in results]


@app.post("/checks/patterns/", response_model=List[dict])
async def run_pattern_checks(
    data: dict,
    pattern_type: str = "digit_preference"
):
    """Run pattern-based checks (digit preference, heaping, uniformity)."""
    df = pd.DataFrame(data.get("rows", []))
    
    check = PatternCheck(df, pattern_type)
    results = check.execute()
    return [r.to_dict() for r in results]


# --- Anomaly Detection ---

@app.post("/anomaly/detect/record/", response_model=dict)
async def detect_record_anomalies(
    data: dict,
    feature_cols: Optional[List[str]] = None
):
    """Detect point anomalies at individual record level."""
    df = pd.DataFrame(data.get("rows", []))
    
    if not feature_cols:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:10]
    
    engine = AnomalyDetectionEngine()
    results = engine.detect_record_level(df, feature_cols)
    return results


@app.post("/anomaly/detect/aggregate/", response_model=dict)
async def detect_aggregate_anomalies(
    data: dict,
    groupby_col: str,
    value_col: str
):
    """Detect anomalies at aggregate level."""
    df = pd.DataFrame(data.get("rows", []))
    
    engine = AnomalyDetectionEngine()
    results = engine.detect_aggregate_level(df, groupby_col, value_col)
    return results


@app.post("/anomaly/detect/cluster/", response_model=dict)
async def detect_cluster_anomalies(
    data: dict,
    cluster_col: str,
    feature_cols: Optional[List[str]] = None
):
    """Detect anomalies at cluster/group level."""
    df = pd.DataFrame(data.get("rows", []))
    
    if not feature_cols:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:5]
    
    engine = AnomalyDetectionEngine()
    results = engine.detect_cluster_level(df, cluster_col, feature_cols)
    return results


@app.post("/anomaly/trend/", response_model=dict)
async def analyze_trend(
    data: dict,
    series_col: str,
    timestamp_col: Optional[str] = None
):
    """Analyze trends in time series data."""
    df = pd.DataFrame(data.get("rows", []))
    
    series = df[series_col]
    timestamps = df[timestamp_col] if timestamp_col and timestamp_col in df.columns else None
    
    te = TrendAnalysisEngine(series, timestamps)
    
    results = {
        "mann_kendall": te.mann_kendall_trend(),
    }
    
    if timestamp_col:
        try:
            seasonal = te.seasonal_decomposition()
            results["seasonal_decomposition"] = seasonal
        except:
            pass
    
    return results


# --- Reporting & Export ---

@app.post("/export/csv/")
async def export_csv(
    data: dict,
    filename: str = "validation_report.csv"
):
    """Export validation results as CSV."""
    try:
        df = pd.DataFrame(data.get("rows", []))
        df.to_csv(filename, index=False)
        return {"status": "exported", "filename": filename, "rows": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/report/")
async def generate_report(
    data: dict,
    report_type: str = "summary"
):
    """Generate validation report."""
    df = pd.DataFrame(data.get("rows", []))
    
    if report_type == "summary":
        report = {
            "total_records": len(df),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": {c: str(d) for c, d in df.dtypes.items()},
            "summary_statistics": df.describe().to_dict(),
        }
    elif report_type == "anomaly":
        # Would integrate with anomaly detection results
        report = {
            "report_type": "anomaly_detection",
            "message": "Anomaly detection report - integrate with detection results"
        }
    else:
        report = {"report_type": report_type, "message": "Custom report generation"}
    
    return {"status": "generated", "report": report}


# --- Data Dashboard (basic endpoint) ---

@app.get("/dashboard/summary/")
async def dashboard_summary(
    db: Session = Depends(get_db)
):
    """Get summary metrics for dashboard."""
    from sqlalchemy import text
    
    # Basic table info
    query = text("SELECT COUNT(*) as total_records FROM survey_responses")
    total = db.execute(query).scalar()
    
    # Missing data percentage
    query = text("""
        SELECT COUNT(*) as total_rows FROM survey_responses
    """)
    total_rows = db.execute(query).scalar()
    
    # Recent validation runs (would be stored in a results table)
    recent_runs = []
    
    return {
        "total_records": total,
        "active_checks": 0,
        "flags_raised": 0,
        "data_freshness": "real-time",
        "recent_validation_runs": recent_runs
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)