"""Check: duplikaty wierszy."""
import pandas as pd
import logging
from src.checks.base import CheckResult, Issue, Severity

logger = logging.getLogger(__name__)


def check_duplicates(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """Wykrywa duplikaty — pełne i w podzbiorze kolumn."""
    config = config or {}
    subset = config.get("subset")
    max_examples = config.get("max_examples", 5)

    result = CheckResult(
        name="duplicates",
        passed=True,
        severity=Severity.OK,
        message="No duplicates found",
    )

    total_rows = len(df)

    if total_rows == 0:
        result.metrics = {"total_rows": 0, "duplicates": 0, "percent": 0.0}
        return result

    # Pełne duplikaty (wszystkie kolumny)
    full_dups_mask = df.duplicated(keep=False)
    full_dups_count = int(df.duplicated(keep="first").sum())

    # Duplikaty w podzbiorze (jeśli podany)
    if subset:
        subset_dups_mask = df.duplicated(subset=subset, keep=False)
        subset_dups_count = int(df.duplicated(subset=subset, keep="first").sum())
    else:
        subset_dups_mask = full_dups_mask
        subset_dups_count = full_dups_count

    # ZAWSZE licz procent — poza if/else
    dup_percent = (subset_dups_count / total_rows * 100) if total_rows else 0.0

    result.metrics = {
        "total_rows": total_rows,
        "full_duplicates": full_dups_count,
        "subset_duplicates": subset_dups_count,
        "subset_columns": subset,
        "percent": round(float(dup_percent), 2),
    }

    if subset_dups_count == 0:
        return result

    if dup_percent >= 10:
        severity = Severity.CRITICAL
    elif dup_percent >= 1:
        severity = Severity.WARNING
    else:
        severity = Severity.INFO

    examples = []
    dup_rows = df[subset_dups_mask]
    if len(dup_rows) > 0:
        cols_to_show = subset if subset else list(df.columns[:5])
        sample = dup_rows.head(max_examples)[cols_to_show].to_dict(orient="records")
        examples = sample

    message = (
        f"Found {subset_dups_count} duplicate rows "
        f"({dup_percent:.1f}% of data)"
    )

    issue = Issue(
        check="duplicates",
        severity=severity,
        message=message,
        details={
            "count": subset_dups_count,
            "percent": round(float(dup_percent), 2),
            "examples": examples,
        },
    )
    result.add_issue(issue)
    result.passed = False
    result.message = message

    logger.info(f"Duplicates check: {message}")
    return result