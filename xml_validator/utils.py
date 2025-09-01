# src/xml_validator/utils.py
import csv
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import yaml


def write_csv_log(rows, csv_log_filename: Path):
    fieldnames = ["file", "schema", "validation_type", "status", "details"]
    file_exists = csv_log_filename.exists() and csv_log_filename.stat().st_size > 0

    with csv_log_filename.open("a", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
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

    log_dir = Path("./logs")  # altijd ./logs in root project
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "validation.log"

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


def load_config(path: str):
    """Load YAML config file if present, else return {}"""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
