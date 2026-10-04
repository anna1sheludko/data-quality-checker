"""Check: brakujące wartości."""
import pandas as pd
import logging
from src.checks.base import CheckResult, Issue, Severity

logger = logging.getLogger(__name__)


def check_missing(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """
    Wykrywa brakujące wartości w każdej kolumnie.

    Config (opcjonalny):
        threshold_warning: % pustych → warning (domyślnie 10)
        threshold_critical: % pustych → critical (domyślnie 50)
    """
    config = config or {}
    threshold_warning = config.get("threshold_warning", 10)
    threshold_critical = config.get("threshold_critical", 50)

    result = CheckResult(
        name="missing",
        passed=True,
        severity=Severity.OK,
        message="No missing values",
    )

    total_rows = len(df)
    if total_rows == 0:
        result.metrics = {"total_rows": 0, "columns_with_missing": 0}
        return result

    # Policz braki w każdej kolumnie
    missing_counts = df.isna().sum()
    missing_pct = (missing_counts / total_rows * 100).round(2)

    columns_with_missing = missing_counts[missing_counts > 0]

    result.metrics = {
        "total_rows": total_rows,
        "columns_with_missing": int(len(columns_with_missing)),
        "total_missing_cells": int(missing_counts.sum()),
        "by_column": {
            col: {
                "count": int(missing_counts[col]),
                "percent": float(missing_pct[col]),
            }
            for col in columns_with_missing.index
        },
    }

    if len(columns_with_missing) == 0:
        return result

    # Issues dla każdej kolumny z brakami
    for col in columns_with_missing.index:
        pct = float(missing_pct[col])
        cnt = int(missing_counts[col])

        if pct >= threshold_critical:
            severity = Severity.CRITICAL
        elif pct >= threshold_warning:
            severity = Severity.WARNING
        else:
            severity = Severity.INFO

        issue = Issue(
            check="missing",
            severity=severity,
            column=col,
            message=f"Column '{col}': {cnt} missing values ({pct:.1f}%)",
            details={"count": cnt, "percent": pct},
        )
        result.add_issue(issue)

    result.passed = False
    critical_count = sum(
        1 for iss in result.issues if iss.severity == Severity.CRITICAL
    )
    result.message = (
        f"{len(columns_with_missing)} columns have missing values "
        f"({critical_count} critical)"
    )

    logger.info(f"Missing check: {result.message}")
    return result