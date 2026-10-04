"""Wspólne fixtures dla testów."""
import pandas as pd
import pytest


@pytest.fixture
def df_empty():
    """Pusty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def df_clean():
    """Czysty DataFrame — bez problemów."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "email": [
            "anna@example.com",
            "jan@example.com",
            "maria@example.com",
            "piotr@example.com",
            "kate@example.com",
        ],
        "amount": [100.0, 200.0, 150.0, 300.0, 250.0],
        "category": ["A", "B", "A", "B", "A"],
    })


@pytest.fixture
def df_with_duplicates():
    """DataFrame z duplikatami."""
    return pd.DataFrame({
        "id": [1, 2, 2, 3, 3, 3],
        "name": ["a", "b", "b", "c", "c", "c"],
    })


@pytest.fixture
def df_with_missing():
    """DataFrame z brakującymi wartościami."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "email": ["a@x.com", None, "c@x.com", None],
        "amount": [100.0, None, None, None],
    })


@pytest.fixture
def df_with_outliers():
    """DataFrame z outlierami — 99.9 jest outlierem."""
    return pd.DataFrame({
        "value": [10, 11, 10, 12, 11, 10, 99999, 11, 10, 12],
    })


@pytest.fixture
def df_with_consistency_issues():
    """DataFrame z niespójnym case i białymi znakami."""
    return pd.DataFrame({
        "city": ["Warsaw", "WARSAW", "warsaw", " Warsaw ", "Krakow"],
    })


@pytest.fixture
def df_with_suspicious():
    """DataFrame z podejrzanymi wartościami (ujemna cena, zły email)."""
    return pd.DataFrame({
        "price": [100.0, -50.0, 200.0, -10.0],
        "email": [
            "a@x.com",
            "invalid-email",
            "b@x.com",
            "also-bad",
        ],
    })