"""Testy dla check_duplicates."""
from src.checks.duplicates import check_duplicates
from src.checks.base import Severity


class TestDuplicates:

    def test_no_duplicates_passes(self, df_clean):
        result = check_duplicates(df_clean)
        assert result.passed is True
        assert result.severity == Severity.OK
        assert result.metrics["subset_duplicates"] == 0

    def test_detects_duplicates(self, df_with_duplicates):
        result = check_duplicates(df_with_duplicates)
        assert result.passed is False
        assert result.metrics["subset_duplicates"] > 0

    def test_empty_dataframe(self, df_empty):
        result = check_duplicates(df_empty)
        assert result.passed is True
        assert result.metrics["total_rows"] == 0

    def test_duplicates_above_10_percent_is_critical(self):
        import pandas as pd
        df = pd.DataFrame({"a": [1, 1, 1, 1, 1, 2, 3, 4, 5, 6]})
        result = check_duplicates(df)
        assert result.severity == Severity.CRITICAL

    def test_subset_columns(self):
        import pandas as pd
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["a", "a", "b"],
            "other": ["x", "y", "z"],
        })
        result = check_duplicates(df, {"subset": ["name"]})
        # 'a' występuje dwa razy w kolumnie 'name'
        assert result.metrics["subset_duplicates"] == 1

    def test_metrics_contains_examples(self, df_with_duplicates):
        result = check_duplicates(df_with_duplicates)
        assert "examples" in result.issues[0].details