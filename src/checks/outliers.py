"""Check: wartości odstające (outliers) w kolumnach numerycznych."""
import pandas as pd
import numpy as np
import logging
from src.checks.base import CheckResult, Issue, Severity

logger = logging.getLogger(__name__)


def check_outliers(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """
    Wykrywa outliers w kolumnach numerycznych.

    Config:
        method: 'zscore' | 'iqr'  (domyślnie 'zscore')
        zscore_threshold: próg (domyślnie 3)
        iqr_multiplier: mnożnik IQR (domyślnie 1.5)
        max_examples: ile przykładów pokazać (domyślnie 5)
        min_rows: minimalna liczba wierszy, by w ogóle sprawdzać (domyślnie 10)
    """
    config = config or {}
    method = config.get("method", "zscore")
    zscore_threshold = config.get("zscore_threshold", 3)
    iqr_multiplier = config.get("iqr_multiplier", 1.5)
    max_examples = config.get("max_examples", 5)
    min_rows = config.get("min_rows", 10)

    result = CheckResult(
        name="outliers",
        passed=True,
        severity=Severity.OK,
        message="No outliers found",
    )

    total_rows = len(df)
    if total_rows < min_rows:
        result.metrics = {
            "total_rows": total_rows,
            "skipped": True,
            "reason": f"Not enough rows (< {min_rows})",
        }
        return result

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        result.metrics = {"total_rows": total_rows, "numeric_columns": 0}
        return result

    by_column = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 3:
            continue

        if method == "zscore":
            outliers_mask, lower, upper = _zscore_outliers(series, zscore_threshold)
        else:
            outliers_mask, lower, upper = _iqr_outliers(series, iqr_multiplier)

        count = int(outliers_mask.sum())
        pct = (count / len(series) * 100) if len(series) else 0

        if count == 0:
            continue

        examples = series[outliers_mask].head(max_examples).tolist()

        by_column[col] = {
            "count": count,
            "percent": round(pct, 2),
            "method": method,
            "lower_bound": round(float(lower), 4),
            "upper_bound": round(float(upper), 4),
            "min_value": round(float(series.min()), 4),
            "max_value": round(float(series.max()), 4),
            "examples": [round(float(v), 4) for v in examples],
        }

    result.metrics = {
        "total_rows": total_rows,
        "numeric_columns": len(numeric_cols),
        "columns_with_outliers": len(by_column),
        "by_column": by_column,
    }

    if not by_column:
        return result

    for col, info in by_column.items():
        pct = info["percent"]
        if pct >= 5:
            severity = Severity.CRITICAL
        elif pct >= 1:
            severity = Severity.WARNING
        else:
            severity = Severity.INFO

        issue = Issue(
            check="outliers",
            severity=severity,
            column=col,
            message=(
                f"Column '{col}': {info['count']} outliers ({pct:.1f}%) "
                f"using {method} — range [{info['lower_bound']}, {info['upper_bound']}]"
            ),
            details=info,
        )
        result.add_issue(issue)

    result.passed = False
    result.message = (
        f"{len(by_column)} columns contain outliers (method: {method})"
    )
    logger.info(f"Outliers check: {result.message}")
    return result


def _zscore_outliers(series: pd.Series, threshold: float):
    """Zwraca maskę outlierów + granice na podstawie Z-score."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        # brak wariancji — brak outlierów
        return pd.Series([False] * len(series), index=series.index), mean, mean
    zscores = (series - mean) / std
    mask = zscores.abs() > threshold
    lower = mean - threshold * std
    upper = mean + threshold * std
    return mask, lower, upper


def _iqr_outliers(series: pd.Series, multiplier: float):
    """Zwraca maskę outlierów + granice na podstawie IQR."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    mask = (series < lower) | (series > upper)
    return mask, lower, upper