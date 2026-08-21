# NSO Survey Data Validation Platform
## Intelligent Survey Data Validation using Probabilistic and Machine Learning Techniques

### Overview
The National Statistical Office (NSO), under the Ministry of Statistics and Programme Implementation (MoSPI), Government of India, requires an intelligent survey data validation platform to detect complex anomalies that traditional rule-based CAPI checks cannot identify. This platform uses probabilistic and machine learning models on historical datasets to aid HSD officials in identifying enumerator bias, temporal drifts, unusual response patterns, and inconsistencies relative to historical trends or related surveys.

---

## Table of Contents
1. [Architecture](#architecture)
2. [Core Components](#core-components)
3. [Data Ingestion](#data-ingestion)
4. [Anomaly Detection](#anomaly-detection)
5. [Integrity Checks](#integrity-checks)
6. [User Interface](#user-interface)
7. [Dashboards](#dashboards)
8. [Export & Reporting](#export--reporting)
9. [Integration Roadmap](#integration-roadmap)
10. [Technology Stack](#technology-stack)
11. [Security & Compliance](#security--compliance)

---

## Architecture
The platform is designed as a modular, standalone system that can be deployed on cloud infrastructure (AWS, GCP, Azure) or on-premises. The architecture follows a microservice pattern with a central FastAPI application coordinating between various modules.

```
+----------------------+       +----------------------+       +----------------------+
|  Front-end Interface  | <->   |   FastAPI Backend    | <->   |   Database/Storage   |
|  (Dash + Custom UI)  |       |   (main.py)          |       |   (PostgreSQL + Redis)|
+----------------------+       +----------------------+       +----------------------+
         |                           |                            |
         |                           |                            |
         v                           v                            v
+----------------------+       +----------------------+       +----------------------+
|   Ingestion Module   |       |   Anomaly Detection  |       |   Integrity Checks   |
|   (API + Batch)     |       |   Engine             |       |   (SQL-based)        |
+----------------------+       +----------------------+       +----------------------+
```

---

## Core Components

### 1. Data Ingestion
- **Real-time API ingestion**: POST `/ingestion/upload_csv/`, `/ingestion/upload_json/`, `/ingestion/sync_from_api/`
- **Batch processing**: `/scripts/batch_processing.py` for handling large datasets
- **Supported formats**: CSV, Excel, JSON, Parquet
- **Kafka integration**: For streaming data from CAPI tools
- **Queue-based processing**: Redis for managing ingestion jobs

### 2. Anomaly Detection Engine
Multiple detection methods operating at different levels:

#### Record-Level Detection
- **Isolation Forest**: Identifies point anomalies in individual records
- **Mahalanobis Distance**: Multivariate outlier detection
- **Z-Score based**: Univariate anomaly detection

#### Cluster-Level Detection
- **Gaussian Mixture Models**: Cluster-based anomaly scoring
- **Isolation Forest on cluster centroids**: Identifies unusual clusters

#### Aggregate-Level Detection
- **Trend Analysis**: Mann-Kendall trend test for time series
- **Chi-Square Goodness of Fit**: Distribution comparison
- **Seasonal ESD**: Seasonal outlier detection

#### Statistical Models
- **Breusch-Pagan test**: Heteroscedasticity detection
- **Durbin-Watson test**: Autocorrelation detection
- **Kolmogorov-Smirnov test**: Distribution fitting

### 3. Integrity Checks
Rule-based validation operating at database level:

- **Referential Integrity**: Foreign key consistency checks
- **Existential Integrity**: No null values in critical fields
- **Range Checks**: Value range validation (e.g., age 0-120, income > 0)
- **Duplicate Detection**: Business key duplicate identification
- **Pattern Analysis**: Digit preference, heaping, uniformity tests

### 4. User Interface
- **Web-based dashboard** (Dash framework)
- **Interactive validation**: Upload data, select analysis type, view results
- **Batch mode**: Process files without manual intervention
- **Real-time feedback**: Immediate anomaly detection results

### 5. Dashboards
Performance and anomaly metrics dashboards:

- **Anomaly distribution**: Count and percentage of anomalies by type
- **Trend charts**: Time series visualization with trend lines
- **Geospatial views**: Regional anomaly mapping
- **Checker performance**: Integrity check success/failure rates

### 6. Export & Reporting
- **CSV/Excel export**: Download validation results
- **PDF reports**: Formatted validation reports
- **JSON exports**: Machine-readable results for further analysis
- **Summary statistics**: Descriptive statistics of the dataset

---

## Data Ingestion

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ingestion/upload_csv/` | POST | Upload CSV data for batch processing |
| `/ingestion/upload_json/` | POST | Upload JSON data for batch processing |
| `/ingestion/sync_from_api/` | POST | Synchronize from external API endpoint |
| `/health` | GET | Health check endpoint |

### Batch Processing
- Read data from CSV, Excel, JSON, Parquet files
- Automatic type detection and normalization
- Background processing for anomaly detection
- Store in PostgreSQL for further analysis

### Kafka Integration
- Real-time data stream from CAPI tools
- Topic: `survey_data_raw`
- Consumer group for parallel processing
- Enable eventual consistency for validation

---

## Anomaly Detection

### Record-Level Anomaly Scoring
```python
from app.models.anomaly_detector import AnomalyDetectionEngine, IsolationForestDetector

# Initialize engine
engine = AnomalyDetectionEngine()

# Or use individual detectors
detector = IsolationForestDetector(contamination=0.1, max_samples=1000)
detector.fit(X)  # X is a pandas DataFrame
predictions = detector.predict(X)  # 1=normal, -1=anomaly
scores = detector.decision_function(X)  # Lower score = more anomalous
```

### Aggregate-Level Analysis
```python
# Detect anomalies at aggregate level (e.g., by region)
results = engine.detect_aggregate_level(df, "region", "monthly_income")

# Includes:
# - Trend analysis (Mann-Kendall test)
# - Chi-square goodness of fit
# - Isolation forest on aggregated data
```

### Statistical Test Examples
```python
from app.models.anomaly_detector import StatisticalModel

# Chi-square test
result = StatisticalModel.chi_square_test(observed, expected)
# {"chi2_statistic": 12.5, "p_value": 0.001, "is_significant": True}

# Trend analysis
result = StatisticalModel.trend_analysis(series)
# {"trend_slope": 0.5, "r_squared": 0.85, "is_increasing": True}

# KS test for normality
result = StatisticalModel.kolmogorov_smirnov_test(sample)
# {"ks_statistic": 0.15, "p_value": 0.05, "is_normal": True}
```

---

## Integrity Checks

### Example: Running All Checks
```python
from app.checks.integrity_checks import (
    ExistentialIntegrityCheck,
    ReferentialIntegrityCheck,
    RangeCheck,
    DuplicateRecordCheck,
)
from sqlalchemy.orm import Session

session = SessionLocal()

# 1. Existential check (no nulls in critical fields)
check = ExistentialIntegrityCheck(session, [
    {"table": "survey_responses", "column": "household_id"},
    {"table": "survey_responses", "column": "person_id"},
])
results = check.execute()

# 2. Range check
check = RangeCheck(session, [
    {"table": "survey_responses", "column": "age", "min_val": 0, "max_val": 120},
    {"table": "survey_responses", "column": "monthly_income", "min_val": 0, "max_val": 1000000},
])
results.extend(check.execute())

# 3. Duplicate check
check = DuplicateRecordCheck(session, ["survey_responses.household_id.person_id"])
results.extend(check.execute())

# 4. Referential check
check = ReferentialIntegrityCheck(session, [
    {"table": "survey_responses", "fk_columns": ["district_id"]}
])
results.extend(check.execute())
```

### Pattern-Based Checks
```python
from app.checks.integrity_checks import PatternCheck
import pandas as pd

df = pd.read_csv("data.csv")
check = PatternCheck(df, "digit_preference")
results = check.execute()

check = PatternCheck(df, "heaping")
results.extend(check.execute())

check = PatternCheck(df, "uniform_distribution")
results.extend(check.execute())
```

---

## User Interface

### Dash Application
The web interface is built with Dash and can be accessed at `http://localhost:8000/dashboard/`.

#### Features
- **File upload**: Drag-and-drop CSV/Excel file upload
- **Validation type selection**: Record-level, aggregate-level, or cluster-level
- **Parameter configuration**: Select grouping columns and value columns
- **Real-time results**: Interactive charts and tables
- **Anomaly visualization**: Box plots, scatter plots, heatmaps

#### Running the Dashboard
```bash
python dash_dashboard.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000
# Then visit http://localhost:8000/dashboard/
```

---

## Integration Roadmap

### Phase 1: MVP (Current)
- ✅ Standalone platform with core anomaly detection
- ✅ Basic integrity checks (referential, existential, range)
- ✅ Web-based UI for data upload and validation
- ✅ CSV/Excel data ingestion
- ✅ Record and aggregate anomaly detection
- ✅ Basic dashboards and reporting

### Phase 2: Enhanced Capabilities
- [ ] PLFS-specific models calibrated on 2024 data
- [ ] Multi-survey comparison (PLFS, NSS, KLEMS)
- [ ] Time series forecasting for trend detection
- [ ] Geospatial anomaly mapping
- [ ] Enumerator bias detection models
- [ ] Advanced pattern detection (Benford's Law, etc.)

### Phase 3: eSigma Integration
- [ ] API endpoint for eSigma data ingestion
- [ ] Shared authentication with MoSPI ecosystem
- [ ] Real-time validation triggered from eSigma
- [ ] Data model alignment with eSigma schema
- [ ] Cloud deployment on MOSPI infrastructure
- [ ] Multi-tenancy for different survey types

### Phase 4: Enterprise Features
- [ ] User management and RBAC
- [ ] Audit logging for all validation actions
- [ ] Model versioning and A/B testing
- [ ] Scheduled batch validation jobs
- [ ] API-first design for third-party integration
- [ ] Disaster recovery and backup systems

---

## Technology Stack

### Language & Framework
- **Python 3.9+**: Core language
- **FastAPI**: Web API framework
- **Dash**: Interactive web dashboards

### Data & ML
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning models
- **scipy**: Statistical tests
- **statsmodels**: Statistical modeling

### Database & Storage
- **PostgreSQL**: Primary data storage
- **Redis**: Caching and job queue
- **SQLAlchemy 2.0**: ORM and database abstraction

### Deployment
- **Docker**: Containerization
- **Uvicorn**: ASGI server for FastAPI
- **Gunicorn**: WSGI server (if needed)
- **Cloud-ready**: AWS, GCP, Azure compatible

### Development Tools
- **pytest**: Testing framework
- **black/code format**: Code formatting
- **Type hints**: Static type checking

---

## Security & Compliance

### Government of India Data Security
- **Data encryption at rest**: AES-256 for stored data
- **Data encryption in transit**: TLS 1.3 for all network communications
- **Access control**: Role-based access control (RBAC)
- **Audit logging**: All data access and modifications logged
- **Data residency**: Data stored within Indian cloud infrastructure

### Confidentiality Guidelines
- **Statistical confidentiality**: adherence to NSO data protection standards
- **PII minimization**: Only necessary fields collected and stored
- **Access logging**: All queries and operations logged with user attribution
- **Data classification**: Survey data marked according to sensitivity level
- **Third-party compliance**: Open-source components vetted for government use

### Security Measures
```yaml
security:
  encryption_at_rest: "AES-256"
  encryption_in_transit: "TLS-1.3"
  auth_method: "OAuth2 + OpenID Connect"
  rate_limiting: "100 requests/minute per IP"
  audit_logging: "Enabled for all operations"
  data_retention: "Configured per MoSPI policy"
```

---

## Quick Start Guide

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/nsosurvey-validator.git
cd nsosurvey-validator

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database, Redis, and Kafka credentials

# Initialize database
python -c "from app.core.db import Base, engine; Base.metadata.create_all(bind=engine)"

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000

# Access the dashboard at http://localhost:8000/dashboard/
```

### First Validation Run
1. Upload a CSV file with survey data through the web UI
2. Select validation type: "Record-Level Anomalies"
3. View anomaly scores and flagged records
4. Run integrity checks to identify data quality issues
5. Export results or generate reports

### Sample Data
Sample PLFS-like data is available at `data/sample_plfs_data.csv` with 5000 records and
columns including household_id, person_id, age, education, industry, occupation,
monthly_income, region, district, survey_month, and employment_status.