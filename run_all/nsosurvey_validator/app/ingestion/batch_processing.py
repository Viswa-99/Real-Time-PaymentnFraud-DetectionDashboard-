import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

from app.core.db import engine, get_async_db
from app.core.config import settings
from app.models.anomaly_detector import AnomalyDetectionEngine, StatisticalModel
import warnings
warnings.filterwarnings("ignore")


class BatchIngestionProcessor:
    """Process batch survey data files and perform validation."""
    
    def __init__(self, file_path: str, groupby_col: str = None, value_col: str = None):
        self.file_path = file_path
        self.groupby_col = groupby_col
        self.value_col = value_col
        self.df = None
        self.anomaly_engine = AnomalyDetectionEngine()
        self.stats_model = StatisticalModel()
    
    def load_data(self) -> pd.DataFrame:
        """Load data from various file formats."""
        file_ext = self.file_path.split(".").[-1].lower()
        
        try:
            if file_ext == "csv":
                self.df = pd.read_csv(self.file_path)
            elif file_ext in ["xlsx", "xls"]:
                self.df = pd.read_excel(self.file_path)
            elif file_ext in ["json"]:
                self.df = pd.read_json(self.file_path)
            elif file_ext in ["parquet"]:
                self.df = pd.read_parquet(self.file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            print(f"Loaded {len(self.df)} rows from {self.file_path}")
            return self.df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def preprocess_data(self) -> pd.DataFrame:
        """Preprocess data: handle missing values, types, etc."""
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Make a copy
        df = self.df.copy()
        
        # Convert date columns
        date_cols = [c for c in df.columns if any(kw in c.lower() for kw in ['date', 'year', 'month'])]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Ensure numerical columns are proper type
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        # Fill missing values appropriately
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isnull().any():
                if df[col].nunique() / len(df) < 0.5:  # If not too many unique values
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 0, inplace=True)
        
        self.df = df
        return df
    
    def run_statistical_tests(self) -> dict:
        """Run statistical tests on the data."""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        results = {
            "descriptive_statistics": self.df.describe(include='all').to_dict(),
            "missing_data_pct": (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
        }
        
        # Kolmogorov-Smirnov test for normality on numerical columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ks_tests = {}
            for col in numeric_cols[:10]:  # Limit to first 10 numeric cols
                try:
                    d, p = self.stats_model.kolmogorov_smirnov_test(self.df[col])
                    ks_tests[col] = d
                except:
                    pass
            results["normality_tests"] = ks_tests
        
        # Durbin-Watson for autocorrelation on time-series like data
        date_like = [c for c in self.df.columns if 'date' in c.lower() or 'month' in c.lower()]
        if date_like:
            try:
                dw_result = self.stats_model.durbin_watson_test(self.df[date_like[0]])
                results["autocorrelation"] = dw_result
            except:
                pass
        
        return results
    
    def detect_anomalies(self) -> dict:
        """Run anomaly detection on the data."""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        # Determine feature columns (numeric, excluding the value column if specified)
        feature_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if self.value_col and self.value_col in feature_cols:
            feature_cols.remove(self.value_col)
        
        if not feature_cols:
            return {"error": "No feature columns available for anomaly detection"}
        
        # Run record-level anomaly detection
        record_anomalies = self.anomaly_engine.detect_record_level(
            self.df, feature_cols[:10]  # Limit to first 10 features
        )
        
        # Run aggregate-level detection if groupby specified
        aggregate_anomalies = None
        if self.groupby_col and self.value_col and self.groupby_col in self.df.columns:
            aggregate_anomalies = self.anomaly_engine.detect_aggregate_level(
                self.df, self.groupby_col, self.value_col
            )
        
        # Run cluster-level detection
        cluster_anomalies = self.anomaly_engine.detect_cluster_level(
            self.df, self.groupby_col or "region", feature_cols[:5]
        )
        
        return {
            "record_level": record_anomalies,
            "aggregate_level": aggregate_anomalies,
            "cluster_level": cluster_anomalies
        }
    
    def run_full_validation(self) -> dict:
        """Run complete validation pipeline."""
        self.load_data()
        self.preprocess_data()
        
        results = {
            "file_path": self.file_path,
            "loaded_at": datetime.utcnow().isoformat(),
            "data_shape": self.df.shape,
            "statistical_tests": self.run_statistical_tests(),
            "anomaly_detection": self.detect_anomalies(),
            "validation_status": "complete"
        }
        
        return results


class TrendAnalysisEngine:
    """Analyze trends over time in survey data."""
    
    def __init__(self, series: pd.Series, timestamps: pd.Series = None):
        self.series = series
        self.timestamps = timestamps
    
    def mann_kendall_trend(self) -> dict:
        """Mann-Kendall trend test."""
        import numpy as np
        
        x = np.arange(len(self.series))
        y = self.series.values
        
        # Calculate S statistic
        n = len(x)
        s = 0
        for i in range(n):
            for j in range(i + 1, n):
                if y[i] < y[j]:
                    s += 1
                elif y[i] > y[j]:
                    s -= 1
        
        # Calculate variance
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        # Z statistic
        if var_s > 0:
            z = (s - 1) / np.sqrt(var_s) if s > 0 else (s + 1) / np.sqrt(var_s) if s < 0 else 0
        else:
            z = 0
        
        # p-value (approximate)
        from scipy import stats as scipy_stats
        p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
        
        return {
            "statistic": float(s),
            "z_value": float(z),
            "p_value": float(p_value),
            "trend": "increasing" if z > 0 else "decreasing" if z < 0 else "no trend",
            "significant": p_value < 0.05
        }
    
    def seasonal_decomposition(self) -> dict:
        """Decompose time series into trend, seasonal, and residual components."""
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        try:
            # Ensure monthly frequency
            if self.timestamps is not None:
                data = pd.Series(
                    self.series.values,
                    index=pd.to_datetime(self.timestamps)
                )
            else:
                data = self.series
            
            # Use additive model if data is stationary, multiplicative otherwise
            decomposition = seasonal_decompose(
                data.fillna(method='ffill'),
                model='additive',
                period=12
            )
            
            return {
                "trend": decomposition.trend.tolist(),
                "seasonal": decomposition.seasonal.tolist(),
                "residual": decomposition.resid.tolist(),
                "observed": decomposition.observed.tolist()
            }
        except Exception as e:
            return {"error": str(e)}


def validate_batch_file(file_path: str, groupby_col: str = None, value_col: str = None) -> dict:
    """Convenience function to validate a batch file."""
    processor = BatchIngestionProcessor(file_path, groupby_col, value_col)
    return processor.run_full_validation()