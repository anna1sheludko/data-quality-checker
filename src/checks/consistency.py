"""Check: spójność tekstu — wielkość liter, białe znaki, jednorodność."""
import pandas as pd
import logging
from src.checks.base import CheckResult, Issue, Severity

logger = logging.getLogger(__name__)


def check_consistency(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """
    Wykrywa niespójności w kolumnach tekstowych:
    - ten sam tekst w różnych wielkościach liter (np. "Warszawa" vs "WARSZAWA")
    - nadmiarowe białe znaki na początku/końcu
    - duplikaty po normalizacji (to samo słowo, inny zapis)
    """
    config = config or {}
    check_case = config.get("check_case", True)
    check_whitespace = config.get("check_whitespace", True)
    max_examples = config.get("max_examples", 5)

    result = CheckResult(
        name="consistency",
        passed=True,
        severity=Severity.OK,
        message="Text is consistent",
    )

    if len(df) == 0:
        result.metrics = {"total_columns": 0}
        return result

    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

    if not text_cols:
        result.metrics = {"total_rows": len(df), "text_columns": 0}
        return result

    by_column = {}

    for col in text_cols:
        series = df[col].dropna().astype(str)

        if len(series) == 0:
            continue

        col_issues = {}

        # 1. Białe znaki
        if check_whitespace:
            stripped = series.str.strip()
            with_whitespace = (series != stripped).sum()
            if with_whitespace > 0:
                col_issues["whitespace"] = {
                    "count": int(with_whitespace),
                    "percent": round(with_whitespace / len(series) * 100, 2),
                }

        # 2. Wielkość liter — sprawdź, czy istnieją różne warianty tych samych wartości
        if check_case:
            lower_map = series.str.lower().value_counts()
            mixed_case_values = []
            for value_lower, count in lower_map.items():
                if count < 2:
                    continue
                variants = series[series.str.lower() == value_lower].unique()
                if len(variants) > 1:
                    mixed_case_values.append({
                        "variants": list(variants),
                        "lower_form": value_lower,
                        "count": int(count),
                    })
            if mixed_case_values:
                col_issues["case_variants"] = {
                    "groups": len(mixed_case_values),
                    "examples": mixed_case_values[:max_examples],
                }

        if col_issues:
            by_column[col] = col_issues

    result.metrics = {
        "total_rows": len(df),
        "text_columns": len(text_cols),
        "columns_with_issues": len(by_column),
        "by_column": by_column,
    }

    if not by_column:
        return result

    for col, info in by_column.items():
        if "case_variants" in info:
            examples_str = ", ".join(
                f"{ex['variants']}" for ex in info["case_variants"]["examples"][:2]
            )
            issue = Issue(
                check="consistency",
                severity=Severity.WARNING,
                column=col,
                message=(
                    f"Column '{col}': {info['case_variants']['groups']} groups "
                    f"with inconsistent case (e.g. {examples_str})"
                ),
                details=info["case_variants"],
            )
            result.add_issue(issue)

        if "whitespace" in info:
            issue = Issue(
                check="consistency",
                severity=Severity.INFO,
                column=col,
                message=(
                    f"Column '{col}': {info['whitespace']['count']} values "
                    f"have leading/trailing whitespace"
                ),
                details=info["whitespace"],
            )
            result.add_issue(issue)

    result.passed = False
    result.message = f"{len(by_column)} columns have consistency issues"
    logger.info(f"Consistency check: {result.message}")
    return result