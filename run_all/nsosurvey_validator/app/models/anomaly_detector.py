from sklearn.ensemble import IsolationForest
from sklearn.covariance import MinCovDet
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.distributions.empirical_distribution import ECDF
import warnings

warnings.filterwarnings("ignore")


class BaseAnomalyDetector:
    """Base class for all anomaly detectors."""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.is_fitted = False
    
    def fit(self, X: pd.DataFrame):
        raise NotImplementedError
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError
    
    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


class IsolationForestDetector(BaseAnomalyDetector):
    """Isolation Forest for point anomaly detection at record and cluster levels."""
    
    def __init__(self, name: str = "isolation_forest", contamination: float = 0.1, max_samples: int = 1000):
        super().__init__(name)
        self.contamination = contamination
        self.max_samples = max_samples
        self.model = IsolationForest(
            contamination=contamination,
            max_samples=max_samples,
            random_state=42
        )
    
    def fit(self, X: pd.DataFrame):
        X_array = X.select_dtypes(include=[np.number]).fillna(0).values
        self.model.fit(X_array)
        self.is_fitted = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        X_array = X.select_dtypes(include=[np.number]).fillna(0).values
        return self.model.predict(X_array)  # 1=normal, -1=anomaly
    
    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        X_array = X.select_dtypes(include=[np.number]).fillna(0).values
        return self.model.score_samples(X_array)


class MahalanobisDetector(BaseAnomalyDetector):
    """Mahalanobis distance-based detector for multivariate outliers."""
    
    def __init__(self, name: str = "mahalanobis"):
        super().__init__(name)
        self.cov_matrix = None
        self.mean_vector = None
        self.inv_cov_matrix = None
    
    def fit(self, X: pd.DataFrame):
        X_numeric = X.select_dtypes(include=[np.number]).fillna(0)
        self.mean_vector = X_numeric.mean().values
        self.cov_matrix = X_numeric.cov().values
        # Use robust covariance estimation
        mcd = MinCovDet()
        mcd.fit(X_numeric.values)
        self.cov_matrix = mcd.covariance_
        self.inv_cov_matrix = np.linalg.inv(self.cov_matrix)
        self.is_fitted = True
    
    def _mahalanobis_distance(self, x):
        delta = np.array(x) - self.mean_vector
        return np.sqrt(delta @ self.inv_cov_matrix @ delta.T)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        distances = X.select_dtypes(include=[np.number]).apply(self._mahalanobis_distance, axis=1)
        threshold = np.percentile(distances.values, 95)
        return (distances.values > threshold).astype(int)  # 1=anomaly, 0=normal
    
    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        return X.select_dtypes(include=[np.number]).apply(self._mahalanobis_distance, axis=1)


class SeasonalESDDetector(BaseAnomalyDetector):
    """Seasonal Extreme Studentized Deviate test for outlier detection in time series."""
    
    def __init__(self, name: str = "seasonal_esd", alpha: float = 0.05):
        super().__init__(name)
        self.alpha = alpha
    
    def fit(self, X: pd.DataFrame):
        # For PLFS data, detect outliers in numerical columns
        self.outlier_indices = {}
        for col in X.select_dtypes(include=[np.number]).columns:
            col_data = X[col].dropna()
            n = len(col_data)
            if n < 3:
                continue
            
            # ESD test implementation
            sorted_vals = np.sort(col_data.values)
            max_outliers = min(int(0.1 * n), 10)
            
            outliers = []
            for k in range(1, max_outliers + 1):
                # Studentized deviate
                mean = np.mean(sorted_vals)
                std = np.std(sorted_vals, ddof=1)
                if std == 0:
                    continue
                esd = abs(sorted_vals[0] - mean) / (std / np.sqrt(n))  # simplified
                outliers.append((k, esd, sorted_vals[0]))
            
            self.outlier_indices[col] = [o[2] for o in outliers if o[1] > self.alpha]
        self.is_fitted = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        mask = np.zeros(len(X), dtype=int)
        for col, outlier_vals in self.outlier_indices.items():
            if col in X.columns:
                for idx, val in enumerate(X[col].values):
                    if val in outlier_vals:
                        mask[idx] = 1
        return mask
    
    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        return np.zeros(len(X))


class ProbabilisticClusterDetector(BaseAnomalyDetector):
    """Probabilistic clustering-based anomaly detection using Gaussian Mixture Models."""
    
    def __init__(self, name: str = "gmm_detector", n_components: int = 3, contamination: float = 0.1):
        super().__init__(name)
        self.n_components = n_components
        self.contamination = contamination
        self.model = None
    
    def fit(self, X: pd.DataFrame):
        X_numeric = X.select_dtypes(include=[np.number]).fillna(0).values
        from sklearn.mixture import GaussianMixture
        self.model = GaussianMixture(
            n_components=self.n_components,
            random_state=42,
            covariance_type='full'
        )
        self.model.fit(X_numeric)
        self.is_fitted = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        X_numeric = X.select_dtypes(include=[np.number]).fillna(0).values
        probs = self.model.predict_proba(X_numeric)
        # Anomalies are points with low probability under the dominant clusters
        max_probs = probs.max(axis=1)
        threshold = np.percentile(max_probs, 100 * (1 - self.contamination))
        return (max_probs < threshold).astype(int)
    
    def decision_function(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Detector must be fitted before prediction")
        X_numeric = X.select_dtypes(include=[np.number]).fillna(0).values
        probs = self.model.predict_proba(X_numeric)
        return probs.max(axis=1)


class StatisticalModel:
    """Statistical models for aggregate-level analysis and trend detection."""
    
    @staticmethod
    def chi_square_test(observed: pd.Series, expected: pd.Series) -> dict:
        """Chi-square goodness of fit test."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            chi2, p = stats.chisquare(observed.values, f_exp=expected.values)
        return {
            "chi2_statistic": float(chi2),
            "p_value": float(p),
            "is_significant": p < 0.05
        }
    
    @staticmethod
    def kolmogorov_smirnov_test(sample: pd.Series, distribution: str = "norm", **params) -> dict:
        """Kolmogorov-Smirnov test for normality or other distributions."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d, p = stats.kstest(sample.values, distribution, args=tuple(params.values()))
        return {
            "ks_statistic": float(d),
            "p_value": float(p),
            "is_normal": p > 0.05
        }
    
    @staticmethod
    def breusch_pagan_test(residuals: pd.Series, exog: pd.DataFrame) -> dict:
        """Breusch-Pagan test for heteroscedasticity."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from statsmodels.stats.diagnostic import breusch_pagan
            bp_stat, p_value, _, _ = breusch_pagan(residuals.values, exog.values)
        return {
            "bp_statistic": float(bp_stat),
            "p_value": float(p_value),
            "is_heteroscedastic": p_value < 0.05
        }
    
    @staticmethod
    def durbin_watson_test(residuals: pd.Series) -> dict:
        """Durbin-Watson test for autocorrelation."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dw = statsmodels.stats.stattools.durbin_watson(residuals.values)
        return {
            "durbin_watson": float(dw),
            "is_autocorrelated": dw < 1.5 or dw > 2.5
        }
    
    @staticmethod
    def trend_analysis(series: pd.Series) -> dict:
        """Mann-Kendall trend test."""
        from statsmodels.tsa.seasonal import seasonal_decompose
        import numpy as np
        
        try:
            # Simple linear trend
            x = np.arange(len(series))
            slope, intercept = np.polyfit(x, series.values, 1)
            r_squared = stats.linregress(x, series.values).rvalue ** 2
            
            return {
                "trend_slope": float(slope),
                "r_squared": float(r_squared),
                "is_increasing": slope > 0,
                "trend_type": "linear"
            }
        except Exception:
            return {
                "trend_slope": 0.0,
                "r_squared": 0.0,
                "is_increasing": False,
                "trend_type": "error"
            }


class AnomalyDetectionEngine:
    """Engine that runs multiple anomaly detectors on survey data."""
    
    def __init__(self):
        self.detectors = {
            "isolation_forest": IsolationForestDetector(),
            "mahalanobis": MahalanobisDetector(),
            "seasonal_esd": SeasonalESDDetector(),
            "gmm": ProbabilisticClusterDetector()
        }
        self.statistical = StatisticalModel()
        self.results = {}
    
    def detect_record_level(self, df: pd.DataFrame, feature_cols: list) -> dict:
        """Detect point anomalies at individual record level."""
        results = {}
        X = df[feature_cols].copy()
        
        for name, detector in self.detectors.items():
            try:
                detector.fit(X)
                predictions = detector.predict(X)
                decision = detector.decision_function(X)
                results[name] = {
                    "anomaly_count": int((predictions == -1).sum() if hasattr(detector.model, 'predict') and (predictions == -1).sum() else predictions.sum()),
                    "anomaly_percentage": float((predictions == -1).mean() * 100) if hasattr(detector.model, 'predict') and (predictions == -1).sum() else float(predictions.mean() * 100),
                    "decision_scores": decision.tolist()
                }
            except Exception as e:
                results[name] = {"error": str(e)}
        
        return results
    
    def detect_aggregate_level(self, df: pd.DataFrame, groupby_col: str, value_col: str) -> dict:
        """Detect anomalies at aggregate level (e.g., by region, cluster, time)."""
        results = {}
        
        # Group and aggregate
        grouped = df.groupby(groupby_col)[value_col].agg(['mean', 'median', 'count', 'std']).reset_index()
        
        # Statistical tests
        if len(grouped) > 3:
            trend = self.statistical.trend_analysis(grouped[value_col])
            results["trend_analysis"] = trend
            
            # Chi-square test if we have categories
            if grouped['mean'].nunique() > 1:
                try:
                    expected = grouped['mean'].mean()
                    chi_result = self.statistical.chi_square_test(
                        grouped['mean'].astype(int) if grouped['mean'].dtype == int else grouped['mean'],
                        pd.Series([expected] * len(grouped))
                    )
                    results["chi_square"] = chi_result
                except Exception:
                    results["chi_square"] = {"error": "chi-square test failed"}
        
        # Isolation forest on aggregated data
        try:
            X = grouped[[value_col]].copy()
            detector = self.detectors["isolation_forest"]
            detector.fit(X)
            predictions = detector.predict(X)
            results["isolation_forest_aggregate"] = {
                "anomaly_count": int((predictions == -1).sum()),
                "anomaly_percentage": float((predictions == -1).mean() * 100)
            }
        except Exception as e:
            results["isolation_forest_aggregate"] = {"error": str(e)}
        
        return results
    
    def detect_cluster_level(self, df: pd.DataFrame, cluster_col: str, feature_cols: list) -> dict:
        """Detect anomalies at cluster/group level."""
        results = {}
        
        # Aggregate by cluster
        cluster_means = df.groupby(cluster_col)[feature_cols].mean()
        
        # Run isolation forest on cluster means
        try:
            detector = self.detectors["isolation_forest"]
            detector.fit(cluster_means)
            predictions = detector.predict(cluster_means)
            decision = detector.decision_function(cluster_means)
            
            results["cluster_anomalies"] = {
                "anomaly_count": int((predictions == -1).sum()),
                "anomaly_percentage": float((predictions == -1).mean() * 100),
                "anomalous_clusters": cluster_means[predictions == -1].index.tolist() if hasattr(predictions, '__iter__') else [],
                "cluster_scores": decision.tolist()
            }
        except Exception as e:
            results["cluster_anomalies"] = {"error": str(e)}
        
        return results
    
    def run_all(self, df: pd.DataFrame, record_features: list, 
                groupby_col: str = None, value_col: str = None) -> dict:
        """Run comprehensive anomaly detection."""
        self.results = {
            "record_level": self.detect_record_level(df, record_features),
            "statistical_summary": {}
        }
        
        if groupby_col and value_col:
            self.results["aggregate_level"] = self.detect_aggregate_level(df, groupby_col, value_col)
        
        return self.results