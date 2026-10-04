"""Testy dla check_outliers."""
import pandas as pd
import pytest
from src.checks.outliers import check_outliers
from src.checks.base import Severity


class TestOutliers:

    def test_no_outliers_passes(self, df_clean):
        result = check_outliers(df_clean)
        assert result.passed is True

    def test_detects_outliers_zscore(self, df_with_outliers):
        # Domyślny z-score=3 może nie złapać przy małej próbce.
        # Zmniejszamy próg, żeby test sprawdzał samą logikę.
        result = check_outliers(
            df_with_outliers,
            {"method": "zscore", "zscore_threshold": 2},
        )
        assert result.passed is False
        assert "value" in result.metrics["by_column"]
        assert result.metrics["by_column"]["value"]["count"] >= 1

    def test_detects_outliers_iqr(self, df_with_outliers):
        result = check_outliers(df_with_outliers, {"method": "iqr"})
        assert result.passed is False
        assert "value" in result.metrics["by_column"]

    def test_too_few_rows_skipped(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        result = check_outliers(df, {"min_rows": 10})
        assert result.metrics.get("skipped") is True

    def test_no_numeric_columns(self):
        df = pd.DataFrame({"name": ["a", "b", "c"] * 5})
        result = check_outliers(df)
        assert result.passed is True
        assert result.metrics["numeric_columns"] == 0

    def test_metrics_contains_bounds(self, df_with_outliers):
        result = check_outliers(
            df_with_outliers,
            {"method": "iqr"},
        )
        info = result.metrics["by_column"]["value"]
        assert "lower_bound" in info
        assert "upper_bound" in info
        assert info["max_value"] >= 99999

    def test_empty_dataframe(self, df_empty):
        result = check_outliers(df_empty)
        assert result.passed is True