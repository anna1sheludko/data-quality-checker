"""Testy dla check_consistency."""
import pandas as pd
from src.checks.consistency import check_consistency


class TestConsistency:

    def test_clean_data_passes(self, df_clean):
        result = check_consistency(df_clean)
        assert result.passed is True

    def test_detects_case_variants(self, df_with_consistency_issues):
        result = check_consistency(df_with_consistency_issues)
        assert result.passed is False
        assert "city" in result.metrics["by_column"]
        assert "case_variants" in result.metrics["by_column"]["city"]

    def test_detects_whitespace(self):
        df = pd.DataFrame({
            "name": [" Anna", " Jan ", "  Maria", "Piotr"],
        })
        result = check_consistency(df)
        assert result.passed is False
        info = result.metrics["by_column"]["name"]
        assert "whitespace" in info
        assert info["whitespace"]["count"] == 3

    def test_empty_dataframe(self, df_empty):
        result = check_consistency(df_empty)
        assert result.passed is True

    def test_no_text_columns(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        result = check_consistency(df)
        assert result.passed is True