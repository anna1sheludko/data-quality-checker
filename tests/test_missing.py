"""Testy dla check_missing."""
from src.checks.missing import check_missing
from src.checks.base import Severity


class TestMissing:

    def test_no_missing_passes(self, df_clean):
        result = check_missing(df_clean)
        assert result.passed is True
        assert result.metrics["total_missing_cells"] == 0

    def test_detects_missing(self, df_with_missing):
        result = check_missing(df_with_missing)
        assert result.passed is False
        assert result.metrics["columns_with_missing"] >= 2

    def test_empty_dataframe(self, df_empty):
        result = check_missing(df_empty)
        assert result.passed is True

    def test_critical_threshold(self):
        import pandas as pd
        # 60% pustych w kolumnie 'a'
        df = pd.DataFrame({"a": [None, None, None, 1, 2], "b": [1, 2, 3, 4, 5]})
        result = check_missing(df, {"threshold_critical": 50, "threshold_warning": 10})
        criticals = [i for i in result.issues if i.severity == Severity.CRITICAL]
        assert len(criticals) >= 1

    def test_warning_threshold(self):
        import pandas as pd
        # 20% pustych — powinno być warning
        df = pd.DataFrame({"a": [None, 1, 2, 3, 4], "b": [1, 2, 3, 4, 5]})
        result = check_missing(df, {"threshold_critical": 50, "threshold_warning": 10})
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        assert len(warnings) >= 1

    def test_metrics_by_column(self, df_with_missing):
        result = check_missing(df_with_missing)
        assert "by_column" in result.metrics
        assert "email" in result.metrics["by_column"]
        assert result.metrics["by_column"]["email"]["count"] == 2