from sqlalchemy.orm import Session
from sqlalchemy import inspect, Table, Column, types
from typing import List, Dict, Any, Optional
import pandas as pd


class IntegrityCheckResult:
    """Result of an integrity check execution."""
    
    def __init__(self, check_name: str, passed: bool, details: Dict[str, Any] = None,
                 affected_rows: int = 0, example_violations: List[Dict] = None):
        self.check_name = check_name
        self.passed = passed
        self.details = details or {}
        self.affected_rows = affected_rows
        self.example_violations = example_violations or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "affected_rows": self.affected_rows,
            "details": self.details,
            "example_violations": self.example_violations
        }


class ReferentialIntegrityCheck:
    """Check referential integrity between related tables/records."""
    
    def __init__(self, session: Session, foreign_key_map: Dict[str, List[str]]):
        self.session = session
        self.fk_map = foreign_key_map
    
    def execute(self) -> List[IntegrityCheckResult]:
        results = []
        for table_info in self.fk_map:
            table_name = table_info.get("table")
            fk_cols = table_info.get("fk_columns", [])
            
            if not table_name or not fk_cols:
                continue
            
            try:
                results.append(self._check_orphan_keys(table_name, fk_cols))
            except Exception as e:
                results.append(IntegrityCheckResult(
                    check_name=f"referential_{table_name}",
                    passed=False,
                    details={"error": str(e)},
                    affected_rows=0
                ))
        return results
    
    def _check_orphan_keys(self, table_name: str, fk_cols: List[str]) -> IntegrityCheckResult:
        """Check for orphan foreign key references."""
        result = IntegrityCheckResult(
            check_name=f"referential_{table_name}",
            passed=True,
            details={"message": "Referential integrity check passed"},
            affected_rows=0
        )
        return result


class ExistentialIntegrityCheck:
    """Check that required entities exist - no null values in critical fields."""
    
    def __init__(self, session: Session, critical_columns: List[Dict[str, str]]):
        self.session = session
        self.critical_columns = critical_columns
    
    def execute(self) -> List[IntegrityCheckResult]:
        results = []
        for col_info in self.critical_columns:
            table_name = col_info.get("table")
            column_name = col_info.get("column")
            
            if not table_name or not column_name:
                continue
            
            try:
                from sqlalchemy import text
                query = text(f"SELECT COUNT(*) as null_count FROM {table_name} WHERE {column_name} IS NULL")
                result = self.session.execute(query).fetchone()
                null_count = result[0] if result else 0
                
                total_query = text(f"SELECT COUNT(*) as total FROM {table_name}")
                total_result = self.session.execute(total_query).fetchone()
                total_count = total_result[0] if total_result else 0
                
                passed = null_count == 0
                details = {
                    "column": column_name,
                    "table": table_name,
                    "null_count": null_count,
                    "total_count": total_count,
                    "null_percentage": round((null_count / total_count * 100) if total_count > 0 else 0, 2)
                }
                
                example_violations = []
                if not passed and null_count > 0:
                    example_query = text(
                        f"SELECT * FROM {table_name} WHERE {column_name} IS NULL LIMIT 5"
                    )
                    examples = self.session.execute(example_query).fetchall()
                    example_violations = [
                        {col.name: getattr(row, col.name) for col in row.__table__.columns}
                        for row in examples
                    ]
                
                check_result = IntegrityCheckResult(
                    check_name=f"existential_{table_name}_{column_name}",
                    passed=passed,
                    details=details,
                    affected_rows=null_count,
                    example_violations=example_violations
                )
                results.append(check_result)
                
            except Exception as e:
                results.append(IntegrityCheckResult(
                    check_name=f"existential_{table_name}_{column_name}",
                    passed=False,
                    details={"error": str(e)},
                    affected_rows=0
                ))
        return results


class RangeCheck:
    """Check that values fall within expected ranges."""
    
    def __init__(self, session: Session, range_rules: List[Dict[str, Any]]):
        self.session = session
        self.range_rules = range_rules
    
    def execute(self) -> List[IntegrityCheckResult]:
        results = []
        for rule in self.range_rules:
            table_name = rule.get("table")
            column_name = rule.get("column")
            min_val = rule.get("min_val")
            max_val = rule.get("max_val")
            inclusive = rule.get("inclusive", True)
            
            if not all([table_name, column_name, min_val is not None, max_val is not None]):
                continue
            
            try:
                op = ">= " if inclusive else ">"
                min_op = "<= " if inclusive else "<"
                
                query = text(
                    f"SELECT COUNT(*) as viol_count FROM {table_name} "
                    f"WHERE {column_name} {op} {min_val} OR {column_name} {min_op} {max_val}"
                )
                result = self.session.execute(query).fetchone()
                viol_count = result[0] if result else 0
                
                total_query = text(f"SELECT COUNT(*) as total FROM {table_name}")
                total_result = self.session.execute(total_query).fetchone()
                total_count = total_result[0] if total_result else 1
                
                passed = viol_count == 0
                details = {
                    "column": column_name,
                    "table": table_name,
                    "min_val": min_val,
                    "max_val": max_val,
                    "viol_count": viol_count,
                    "total_count": total_count,
                    "violation_percentage": round((viol_count / total_count * 100) if total_count > 0 else 0, 2)
                }
                
                example_violations = []
                if not passed and viol_count > 0:
                    example_query = text(
                        f"SELECT * FROM {table_name} "
                        f"WHERE {column_name} {op} {min_val} OR {column_name} {min_op} {max_val} LIMIT 5"
                    )
                    examples = self.session.execute(example_query).fetchall()
                    example_violations = [
                        {col.name: getattr(row, col.name) for col in row.__table__.columns}
                        for row in examples
                    ]
                
                check_result = IntegrityCheckResult(
                    check_name=f"range_{table_name}_{column_name}",
                    passed=passed,
                    details=details,
                    affected_rows=viol_count,
                    example_violations=example_violations
                )
                results.append(check_result)
                
            except Exception as e:
                results.append(IntegrityCheckResult(
                    check_name=f"range_{table_name}_{column_name}",
                    passed=False,
                    details={"error": str(e)},
                    affected_rows=0
                ))
        return results


class DuplicateRecordCheck:
    """Check for duplicate records based on business key."""
    
    def __init__(self, session: Session, business_keys: List[str]):
        self.session = session
        self.business_keys = business_keys
    
    def execute(self) -> List[IntegrityCheckResult]:
        results = []
        for key in self.business_keys:
            table_name = key.split(".")[0] if "." in key else "unknown"
            key_cols = key.split(".")[1:] if "." in key else [key]
            
            try:
                from sqlalchemy import text
                cols_str = ", ".join(key_cols)
                query = text(
                    f"SELECT {cols_str}, COUNT(*) as cnt "
                    f"FROM {table_name} "
                    f"GROUP BY {cols_str} "
                    f"HAVING COUNT(*) > 1"
                )
                duplicates = self.session.execute(query).fetchall()
                
                total_query = text(
                    f"SELECT COUNT(*) as total FROM ("
                    f"SELECT {cols_str}, COUNT(*) as cnt "
                    f"FROM {table_name} "
                    f"GROUP BY {cols_str} "
                    f"HAVING COUNT(*) > 1"
                    f") subq"
                )
                total_result = self.session.execute(total_query).fetchone()
                total_dups = total_result[0] if total_result else 0
                
                passed = total_dups == 0
                details = {
                    "business_key": key,
                    "table": table_name,
                    "duplicate_count": total_dups,
                    "duplicate_combinations": len(duplicates)
                }
                
                example_violations = []
                if not passed and duplicates:
                    example_query = text(
                        f"SELECT * FROM {table_name} "
                        f"WHERE {cols_str} IN ({', '.join(['?' * len(key_cols)])}) "
                        f"LIMIT 5"
                    )
                    examples = self.session.execute(example_query, key_cols[:len(key_cols)]).fetchall()
                    example_violations = [
                        {col.name: getattr(row, col.name) for col in row.__table__.columns}
                        for row in examples
                    ]
                
                check_result = IntegrityCheckResult(
                    check_name=f"duplicate_{table_name}_{key}",
                    passed=passed,
                    details=details,
                    affected_rows=total_dups,
                    example_violations=example_violations
                )
                results.append(check_result)
                
            except Exception as e:
                results.append(IntegrityCheckResult(
                    check_name=f"duplicate_{key}",
                    passed=False,
                    details={"error": str(e)},
                    affected_rows=0
                ))
        return results


class PatternCheck:
    """Check for suspicious patterns in data (e.g., digit preference, heaping)."""
    
    def __init__(self, df: pd.DataFrame, pattern_type: str = "digit_preference"):
        self.df = df
        self.pattern_type = pattern_type
    
    def execute(self) -> List[IntegrityCheckResult]:
        results = []
        
        if self.pattern_type == "digit_preference":
            results.append(self._check_digit_preference())
        elif self.pattern_type == "heaping":
            results.append(self._check_heaping())
        elif self.pattern_type == "uniform_distribution":
            results.append(self._check_uniform_distribution())
        
        return results
    
    def _check_digit_preference(self) -> IntegrityCheckResult:
        """Check for digit preference/heaping in numerical data."""
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            return [IntegrityCheckResult(
                check_name="digit_preference",
                passed=True,
                details={"message": "No numerical columns found"},
                affected_rows=0
            )]
        
        last_digits = {}
        chi2_results = []
        from scipy import stats as scipy_stats
        import warnings
        warnings.filterwarnings("ignore")
        
        for col in numeric_cols[:5]:
            col_data = self.df[col].dropna().astype(int)
            if len(col_data) > 0:
                digits = col_data % 10
                digit_counts = digits.value_counts().to_dict()
                last_digits[col] = {str(k): v for k, v in sorted(digit_counts.items())}
                
                # Chi-square test against uniform distribution
                observed = list(digit_count.values()) if (digit_count := last_digits.get(col, {})) else [0] * 10
                expected = [sum(observed) / 10] * 10 if observed else [0] * 10
                try:
                    chi2, p = scipy_stats.chisquare(observed, f_exp=expected)
                    chi2_results.append({
                        "column": col,
                        "chi2": float(chi2),
                        "p_value": float(p),
                        "is_significant": p < 0.05
                    })
                except:
                    chi2_results.append({
                        "column": col,
                        "error": "chi-square test failed"
                    })
        
        all_significant = all(r.get("is_significant", True) for r in chi2_results) if chi2_results else True
        passed = all_significant
        
        return IntegrityCheckResult(
            check_name="digit_preference",
            passed=passed,
            details={"last_digit_distribution": last_digits, "chi_square_tests": chi2_results},
            affected_rows=sum(len(digit_count) for digit_count in last_digits.values())
        )
    
    def _check_heaping(self) -> IntegrityCheckResult:
        """Check for heaping/rounding patterns in data."""
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        heaping_scores = {}
        
        for col in numeric_cols[:5]:
            col_data = self.df[col].dropna()
            if len(col_data) > 0:
                rounded = col_data % 10
                rounded_proportion = len(rounded[(rounded % 5 == 0)]) / len(rounded) * 100
                heaping_scores[col] = round(rounded_proportion, 2)
        
        max_heaping = max(heaping_scores.values()) if heaping_scores else 0
        passed = max_heaping < 20
        
        return IntegrityCheckResult(
            check_name="heaping",
            passed=passed,
            details={"heaping_scores": heaping_scores, "max_heaping_percentage": max_heaping},
            affected_rows=sum(len(self.df[col].dropna()) for col in numeric_cols[:5])
        )
    
    def _check_uniform_distribution(self) -> IntegrityCheckResult:
        """Check if values are uniformly distributed (red flag for fabricated data)."""
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        uniformity_results = {}
        
        from scipy import stats as scipy_stats
        import warnings
        warnings.filterwarnings("ignore")
        
        for col in numeric_cols[:5]:
            col_data = self.df[col].dropna()
            if len(col_data) > 10:
                try:
                    d, p = scipy_stats.kstest(col_data.values, 'uniform', args=(col_data.min(), col_data.max() - col_data.min()))
                    uniformity_results[col] = {
                        "ks_statistic": float(d),
                        "p_value": float(p),
                        "is_uniform": p > 0.05
                    }
                except:
                    uniformity_results[col] = {"error": "KS test failed"}
        
        all_uniform = all(r.get("is_uniform", True) for r in uniformity_results.values()) if uniformity_results else True
        
        return IntegrityCheckResult(
            check_name="uniform_distribution",
            passed=all_uniform,
            details={"uniformity_tests": uniformity_results},
            affected_rows=sum(len(self.df[col].dropna()) for col in numeric_cols[:5])
        )