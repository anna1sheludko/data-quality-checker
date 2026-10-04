"""Testy dla check_suspicious."""
import pandas as pd
from src.checks.suspicious import check_suspicious
from src.checks.base import Severity


class TestSuspicious:

    def test_no_rules_no_issues(self, df_clean):
        result = check_suspicious(df_clean, {"rules": []})
        assert result.passed is True

    def test_detects_negative_prices(self, df_with_suspicious):
        rules = {
            "rules": [
                {
                    "column_pattern": ".*price.*",
                    "check": ">= 0",
                    "message": "Price must be non-negative",
                }
            ]
        }
        result = check_suspicious(df_with_suspicious, rules)
        assert result.passed is False
        # Dwie ujemne ceny: -50, -10
        assert result.metrics["triggered"] >= 1

    def test_detects_invalid_emails(self, df_with_suspicious):
        rules = {
            "rules": [
                {
                    "column_pattern": ".*email.*",
                    "check": "valid_email",
                    "message": "Email must be valid",
                }
            ]
        }
        result = check_suspicious(df_with_suspicious, rules)
        assert result.passed is False
        assert result.metrics["triggered"] >= 1

    def test_detects_future_dates(self):
        df = pd.DataFrame({
            "order_date": ["2026-01-01", "2099-12-31", "2025-06-15"],
        })
        rules = {
            "rules": [
                {
                    "column_pattern": ".*date.*",
                    "check": "<= today",
                    "message": "Date cannot be in the future",
                }
            ]
        }
        result = check_suspicious(df, rules)
        assert result.passed is False

    def test_clean_data_passes(self, df_clean):
        rules = {
            "rules": [
                {
                    "column_pattern": ".*amount.*",
                    "check": ">= 0",
                    "message": "Amount must be positive",
                }
            ]
        }
        result = check_suspicious(df_clean, rules)
        assert result.passed is True

    def test_unknown_rule_ignored(self, df_clean):
        rules = {
            "rules": [
                {
                    "column_pattern": ".*",
                    "check": "some_unknown_rule",
                    "message": "Test",
                }
            ]
        }
        result = check_suspicious(df_clean, rules)
        assert result.passed is True