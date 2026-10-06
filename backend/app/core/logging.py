"""Structured logging configuration for Dhruva.AI backend."""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured stdout logging."""
    logger = logging.getLogger("dhruva")
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
