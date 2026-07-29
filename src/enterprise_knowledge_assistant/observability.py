"""Simple file and console tracing for the complete graph execution."""

from datetime import datetime
import logging
from pathlib import Path


def configure_logging(log_dir: Path) -> logging.Logger:
    """Create a timestamped execution log and return the application logger."""

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"execution_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("enterprise_knowledge_assistant")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info("Execution log: %s", log_file)
    return logger

