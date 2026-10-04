"""Check: typy danych — niespójności, tekst w kolumnach numerycznych, itd."""
import pandas as pd
import logging
import re
from src.checks.base import CheckResult, Issue, Severity
from src.loader import detect_column_types

logger = logging.getLogger(__name__)


def check_types(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """
    Wykrywa problemy z typami:
    - liczby zapisane jako tekst
    - daty zapisane jako tekst
    - niespójne formaty w tej samej kolumnie
    - podejrzane wartości tekstowe (np. 'N/A' jako string zamiast NaN)
    """
    config = config or {}
    email_pattern = config.get("email_pattern", r"^[\w\.-]+@[\w\.-]+\.\w+$")
    phone_pattern = config.get("phone_pattern", r"^\+?[\d\s\-\(\)]{7,20}$")

    result = CheckResult(
        name="types",
        passed=True,
        severity=Severity.OK,
        message="Types are consistent",
    )

    if len(df) == 0:
        result.metrics = {"total_columns": 0, "problematic_columns": 0}
        return result

    detected_types = detect_column_types(df)

    problematic = {}
    inconsistent = {}

    # Rozszerzona lista "pustych" stringów
    null_strings = {
        "n/a", "na", "null", "none", "-", "--", "?", "",
        "nan", "unknown", "missing", "brak", "неизвестно",
    }

    for col in df.columns:
        series = df[col]

        # Sprawdź stringowe odpowiedniki null
        if _is_text_dtype(series):
            str_series = series.astype(str).str.strip().str.lower()
            null_like_mask = str_series.isin(null_strings)
            null_like = int(null_like_mask.sum())

            if null_like > 0:
                examples = series[null_like_mask].head(3).astype(str).tolist()
                problematic[col] = {
                    "issue": "null-like strings",
                    "count": null_like,
                    "examples": examples,
                }

            # Sprawdź mieszane typy
            kind = _detect_mixed_types(series)
            if kind == "mixed":
                inconsistent[col] = {
                    "issue": "mixed types in one column",
                    "examples": series.dropna().head(5).astype(str).tolist(),
                }

    result.metrics = {
        "total_columns": len(df.columns),
        "detected_types": detected_types,
        "problematic_columns": list(problematic.keys()),
        "inconsistent_columns": list(inconsistent.keys()),
    }

    # Issues
    for col, info in problematic.items():
        issue = Issue(
            check="types",
            severity=Severity.WARNING,
            column=col,
            message=(
                f"Column '{col}' has {info['count']} 'null-like' strings "
                f"(e.g. 'N/A') — should be treated as missing"
            ),
            details=info,
        )
        result.add_issue(issue)

    for col, info in inconsistent.items():
        issue = Issue(
            check="types",
            severity=Severity.WARNING,
            column=col,
            message=f"Column '{col}' has mixed data types",
            details=info,
        )
        result.add_issue(issue)

    if problematic or inconsistent:
        result.passed = False
        result.message = (
            f"{len(problematic)} columns with null-like values, "
            f"{len(inconsistent)} with mixed types"
        )

    logger.info(f"Types check: {result.message}")
    return result


def _detect_mixed_types(series: pd.Series) -> str:
    """
    Sprawdza, czy w kolumnie są różne typy.
    Zwraca: 'uniform' | 'mixed'.

    Uwaga: data musi zawierać cyfry — inaczej pandas parsuje 'Jan'
    jako styczeń, 'Maria' jako marzec, itd. (imiona ≠ daty).
    """
    sample = series.dropna().head(200).astype(str)

    if len(sample) < 2:
        return "uniform"

    numeric = 0
    date_like = 0
    text = 0

    for val in sample:
        v = val.strip()
        if not v:
            continue

        # Liczba?
        try:
            float(v)
            numeric += 1
            continue
        except (ValueError, TypeError):
            pass

        # Data — tylko jeśli zawiera cyfry
        has_digit = any(c.isdigit() for c in v)
        if has_digit:
            try:
                parsed = pd.to_datetime(v, errors="coerce")
                if pd.notna(parsed):
                    date_like += 1
                    continue
            except (ValueError, TypeError):
                pass

        text += 1

    total = numeric + date_like + text
    if total == 0:
        return "uniform"

    max_share = max(numeric, date_like, text) / total
    if max_share >= 0.9:
        return "uniform"

    return "mixed"

def _is_text_dtype(series: pd.Series) -> bool:
    """Sprawdza, czy kolumna jest tekstowa — obsługuje pandas 2 i 3."""
    dtype_name = str(series.dtype).lower()
    return dtype_name in ("object", "string", "str") or "str" in dtype_name