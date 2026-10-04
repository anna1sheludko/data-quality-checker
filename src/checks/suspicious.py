"""Check: podejrzane wartości według reguł biznesowych z konfiguracji."""
import pandas as pd
import re
import logging
from datetime import date
from src.checks.base import CheckResult, Issue, Severity

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def check_suspicious(df: pd.DataFrame, config: dict = None) -> CheckResult:
    """
    Wykrywa podejrzane wartości na podstawie reguł z YAML:
    - regex na nazwy kolumn → warunek na wartości
    """
    config = config or {}
    rules = config.get("rules", [])
    max_examples = config.get("max_examples", 5)

    result = CheckResult(
        name="suspicious",
        passed=True,
        severity=Severity.OK,
        message="No suspicious values",
    )

    if len(df) == 0 or not rules:
        result.metrics = {
            "total_rows": len(df),
            "rules": len(rules),
            "triggered": 0,
        }
        return result

    triggered = []

    for rule in rules:
        col_pattern = rule.get("column_pattern", "")
        check_expr = rule.get("check", "")
        message = rule.get("message", "")

        matching_cols = [
            c for c in df.columns if re.match(col_pattern, c, re.IGNORECASE)
        ]

        for col in matching_cols:
            offending_mask, examples = _apply_rule(df[col], check_expr)
            count = int(offending_mask.sum())

            if count == 0:
                continue

            pct = round(count / len(df) * 100, 2)

            triggered.append({
                "column": col,
                "check": check_expr,
                "count": count,
                "percent": pct,
                "message": message,
                "examples": examples[:max_examples],
            })

    result.metrics = {
        "total_rows": len(df),
        "rules": len(rules),
        "triggered": len(triggered),
        "details": triggered,
    }

    if not triggered:
        return result

    for t in triggered:
        if t["percent"] >= 5:
            severity = Severity.CRITICAL
        elif t["percent"] >= 1:
            severity = Severity.WARNING
        else:
            severity = Severity.INFO

        issue = Issue(
            check="suspicious",
            severity=severity,
            column=t["column"],
            message=(
                f"Column '{t['column']}': {t['count']} values fail "
                f"rule '{t['check']}' — {t['message']}"
            ),
            details=t,
        )
        result.add_issue(issue)

    result.passed = False
    result.message = f"{len(triggered)} rule violations"
    logger.info(f"Suspicious check: {result.message}")
    return result


def _apply_rule(series: pd.Series, check_expr: str):
    """
    Aplikuje regułę na serię. Zwraca maskę wartości, które NIE przechodzą reguły,
    oraz listę przykładów.
    """
    check_expr = check_expr.strip()

    # Obsługa konkretnych słów kluczowych
    if check_expr == "valid_email":
        mask_offend = ~series.astype(str).str.match(EMAIL_RE, na=False)
        # Pomijamy puste wartości — one i tak są łapane przez check 'missing'
        mask_offend = mask_offend & series.notna()
        examples = series[mask_offend].head(5).tolist()
        return mask_offend, examples

    if check_expr == "<= today":
        try:
            dates = pd.to_datetime(series, errors="coerce")
            mask_offend = dates > pd.Timestamp(date.today())
            mask_offend = mask_offend & dates.notna()
            examples = series[mask_offend].head(5).tolist()
            return mask_offend, examples
        except Exception:
            return pd.Series([False] * len(series), index=series.index), []

    # Obsługa operatorów: >= X, <= X, > X, < X, == X
    match = re.match(r"^(<=|>=|<|>|==)\s*(-?\d+(?:\.\d+)?)$", check_expr)
    if match:
        op, num = match.group(1), float(match.group(2))
        numeric = pd.to_numeric(series, errors="coerce")

        if op == ">=":
            mask_offend = numeric < num
        elif op == "<=":
            mask_offend = numeric > num
        elif op == ">":
            mask_offend = numeric <= num
        elif op == "<":
            mask_offend = numeric >= num
        elif op == "==":
            mask_offend = numeric != num

        mask_offend = mask_offend & numeric.notna()
        examples = series[mask_offend].head(5).tolist()
        return mask_offend, examples

    # Nieznana reguła — nic nie robimy
    logger.warning(f"Unknown rule expression: {check_expr}")
    return pd.Series([False] * len(series), index=series.index), []
