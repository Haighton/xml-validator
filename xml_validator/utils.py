# xml_validator/utils.py
import csv
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import yaml


def write_csv_log(rows, csv_log_filename: Path):
    fieldnames = ["batch", "file", "validation_type", "status", "details"]
    file_exists = csv_log_filename.exists()

    with csv_log_filename.open("a", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def setup_logging(
    output: Path,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """Configure logging to console + rotating logfile."""

    log_file = output / "validation.log"
    logger = logging.getLogger("xml_validator")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def load_config(config_path: str | Path = "config.yaml") -> dict:
    """Load YAML config file if present."""
    config_file = Path(config_path)
    if config_file.exists():
        with config_file.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
