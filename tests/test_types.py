"""Testy dla check_types."""
import pandas as pd
from src.checks.types import check_types
from src.checks.base import Severity


class TestTypes:

    def test_clean_data_passes(self, df_clean):
        result = check_types(df_clean)
        assert result.passed is True

    def test_detects_null_like_strings(self):
        # Używamy stringów, które pandas nie konwertuje na NaN,
        # ale nasz kod je rozpoznaje (patrz null_strings w types.py).
        df = pd.DataFrame({
            "name": ["Anna", "unknown", "Jan", "missing", "Maria", "nan"],
        })
        result = check_types(df)
        assert result.passed is False
        assert "name" in result.metrics["problematic_columns"]

    def test_detects_mixed_types(self):
        df = pd.DataFrame({
            "value": ["100", "200", "abc", "2026-01-01", "text", "300"],
        })
        result = check_types(df)
        assert result.passed is False
        assert "value" in result.metrics["inconsistent_columns"]

    def test_uniform_text_passes(self):
        df = pd.DataFrame({
            "name": ["Anna", "Jan", "Maria", "Piotr", "Kasia"],
        })
        result = check_types(df)
        assert result.passed is True

    def test_uniform_numbers_as_text_passes(self):
        df = pd.DataFrame({
            "value": ["100", "200", "300", "400", "500"],
        })
        result = check_types(df)
        assert "value" not in result.metrics["inconsistent_columns"]

    def test_empty_dataframe(self, df_empty):
        result = check_types(df_empty)
        assert result.passed is True

    def test_metrics_contains_detected_types(self, df_clean):
        result = check_types(df_clean)
        assert "detected_types" in result.metrics
        assert result.metrics["detected_types"]["id"] == "integer"
        assert result.metrics["detected_types"]["amount"] == "float"