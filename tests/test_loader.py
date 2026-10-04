"""Testy dla loadera."""
import pytest
import pandas as pd
from pathlib import Path
from src.loader import load_file, detect_column_types, LoaderError


class TestLoader:

    def test_load_csv(self, tmp_path):
        csv = tmp_path / "test.csv"
        csv.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

        loaded = load_file(csv)
        assert loaded.original_rows == 2
        assert loaded.original_columns == 2
        assert loaded.file_format == "csv"
        assert list(loaded.df.columns) == ["a", "b"]

    def test_file_not_found(self, tmp_path):
        with pytest.raises(LoaderError, match="not found"):
            load_file(tmp_path / "missing.csv")

    def test_unsupported_format(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        with pytest.raises(LoaderError, match="Unsupported format"):
            load_file(f)

    def test_empty_csv_warns(self, tmp_path):
        csv = tmp_path / "empty.csv"
        csv.write_text("a,b\n", encoding="utf-8")
        loaded = load_file(csv)
        # Sprawdź, czy któryś warning zawiera frazę
        assert any("File is empty" in w for w in loaded.warnings)


class TestDetectColumnTypes:

    def test_integer_column(self):
        df = pd.DataFrame({"id": [1, 2, 3]})
        types = detect_column_types(df)
        assert types["id"] == "integer"

    def test_float_column(self):
        df = pd.DataFrame({"amount": [1.5, 2.5, 3.5]})
        types = detect_column_types(df)
        assert types["amount"] == "float"

    def test_text_column(self):
        df = pd.DataFrame({"name": ["a", "b", "c"]})
        types = detect_column_types(df)
        assert types["name"] == "text"

    def test_datetime_as_text(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-01-02", "2024-01-03"]})
        types = detect_column_types(df)
        assert types["date"] == "datetime-as-text"

    def test_numeric_as_text(self):
        df = pd.DataFrame({"value": ["100", "200", "300"]})
        types = detect_column_types(df)
        assert types["value"] == "numeric-as-text"

    def test_empty_column(self):
        df = pd.DataFrame({"x": [None, None, None]})
        types = detect_column_types(df)
        assert types["x"] == "empty"