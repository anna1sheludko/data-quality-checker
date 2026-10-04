"""Konfiguracja logowania — do pliku i konsoli."""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path, log_level: str = "INFO") -> None:
    """Konfiguruje logowanie do pliku i konsoli."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "data_quality.log"

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Usuń istniejące handlery (żeby nie duplikować przy wielokrotnym imporcie)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Wycisz zbyt gadatliwe biblioteki
    logging.getLogger("urllib3").setLevel(logging.WARNING)