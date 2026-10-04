"""Loader — czyta CSV/Excel i zwraca DataFrame + metadane."""
import pandas as pd
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class LoaderError(Exception):
    """Błąd podczas wczytywania pliku."""
    pass


@dataclass
class LoadedData:
    """Wynik wczytania pliku — DataFrame + metadane."""
    df: pd.DataFrame
    filepath: Path
    file_format: str                    # 'csv' | 'excel'
    original_rows: int
    original_columns: int
    source_name: str
    warnings: list = field(default_factory=list)

    @property
    def summary(self) -> dict:
        return {
            "file": str(self.filepath.name),
            "format": self.file_format,
            "rows": self.original_rows,
            "columns": self.original_columns,
            "column_names": list(self.df.columns),
        }


def load_file(filepath: Path, **kwargs) -> LoadedData:
    """
    Wczytuje plik CSV lub Excel.

    Args:
        filepath: ścieżka do pliku.
        **kwargs: dodatkowe argumenty przekazywane do pd.read_csv/read_excel.

    Returns:
        LoadedData z DataFrame i metadanymi.

    Raises:
        LoaderError: gdy plik nie istnieje, ma nieobsługiwany format,
                     lub nie da się go wczytać.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise LoaderError(f"File not found: {filepath}")

    suffix = filepath.suffix.lower()
    warnings = []

    try:
        if suffix == ".csv":
            df = _load_csv(filepath, **kwargs)
            file_format = "csv"
        elif suffix in (".xlsx", ".xls"):
            df = _load_excel(filepath, **kwargs)
            file_format = "excel"
        else:
            raise LoaderError(
                f"Unsupported format: {suffix}. "
                f"Supported: .csv, .xlsx, .xls"
            )
    except Exception as e:
        raise LoaderError(f"Failed to load {filepath.name}: {e}") from e

    original_rows = len(df)
    original_columns = len(df.columns)

    logger.info(
        f"Loaded {filepath.name}: {original_rows} rows, {original_columns} columns"
    )

    # Ostrzeżenia o strukturze
    if original_rows == 0:
        warnings.append("File is empty (0 rows)")

    if original_columns == 0:
        warnings.append("File has no columns")

    # Sprawdź duplikaty nazw kolumn
    if len(df.columns) != len(set(df.columns)):
        warnings.append("Duplicate column names detected")
        logger.warning(f"Duplicate column names in {filepath.name}")

    return LoadedData(
        df=df,
        filepath=filepath,
        file_format=file_format,
        original_rows=original_rows,
        original_columns=original_columns,
        source_name=filepath.stem,
        warnings=warnings,
    )


def _load_csv(filepath: Path, **kwargs) -> pd.DataFrame:
    """Wczytuje CSV z sensownymi domyślnymi wartościami."""
    defaults = {
        "encoding": "utf-8",
        "on_bad_lines": "warn",
    }
    defaults.update(kwargs)

    try:
        return pd.read_csv(filepath, **defaults)
    except UnicodeDecodeError:
        # fallback — spróbuj innego kodowania
        logger.warning(f"UTF-8 failed for {filepath.name}, trying latin-1")
        defaults["encoding"] = "latin-1"
        return pd.read_csv(filepath, **defaults)


def _load_excel(filepath: Path, **kwargs) -> pd.DataFrame:
    """Wczytuje Excel."""
    return pd.read_excel(filepath, **kwargs)


def detect_column_types(df: pd.DataFrame) -> dict:
    """
    Wykrywa typ każdej kolumny — nie tylko 'object', ale semantycznie:
    'numeric', 'integer', 'float', 'datetime', 'boolean', 'text'.
    """
    types = {}

    for col in df.columns:
        series = df[col].dropna()

        if len(series) == 0:
            types[col] = "empty"
            continue

        # Pandas type
        dtype = series.dtype

        if pd.api.types.is_integer_dtype(dtype):
            types[col] = "integer"
        elif pd.api.types.is_float_dtype(dtype):
            types[col] = "float"
        elif pd.api.types.is_bool_dtype(dtype):
            types[col] = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            types[col] = "datetime"
        else:
            # object — spróbuj wykryć, co to naprawdę jest
            types[col] = _detect_object_type(series)

    return types


def _detect_object_type(series: pd.Series) -> str:
    """Próbuje rozpoznać, co siedzi w kolumnie typu 'object'."""
    sample = series.head(100).astype(str)

    # Spróbuj jako numeric
    try:
        pd.to_numeric(sample)
        return "numeric-as-text"
    except (ValueError, TypeError):
        pass

        # Spróbuj jako datetime
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pd.to_datetime(sample, errors="raise")
        return "datetime-as-text"
    except (ValueError, TypeError):
        pass

    # Boolean?
    unique_lower = set(sample.str.lower().unique())
    if unique_lower.issubset({"true", "false", "yes", "no", "1", "0"}):
        return "boolean-as-text"

    return "text"