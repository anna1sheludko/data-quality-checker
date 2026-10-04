"""Ładowanie konfiguracji z pliku YAML."""
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def load_rules(config_path: Path = None) -> dict:
    """
    Ładuje reguły jakości z pliku YAML.

    Args:
        config_path: ścieżka do pliku YAML. Domyślnie config/default_rules.yaml

    Returns:
        Słownik z regułami.
    """
    if config_path is None:
        config_path = BASE_DIR / "config" / "default_rules.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    logger.info(f"Loading rules from {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.debug(f"Loaded config keys: {list(config.keys())}")
    return config


def validate_rules(config: dict) -> None:
    """Sprawdza, czy konfiguracja ma wymaganą strukturę."""
    required_sections = ["checks", "report"]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config: '{section}'")

    if "checks" in config:
        required_checks = ["duplicates", "missing", "types"]
        for check in required_checks:
            if check not in config["checks"]:
                logger.warning(f"Check '{check}' not found in config — will be skipped")