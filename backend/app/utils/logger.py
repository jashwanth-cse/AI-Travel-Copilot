"""Structured logging helpers for backend modules."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

from app.utils.constants import DEFAULT_LOG_LEVEL

_LOG_FORMAT: Final[str] = (
    "%(asctime)s | level=%(levelname)s | logger=%(name)s | "
    "module=%(module)s | line=%(lineno)d | message=%(message)s"
)

_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Configure application-wide structured console logging.

    The function is idempotent enough for scripts and tests: if the root logger
    already has handlers, we update levels and formatters instead of adding
    duplicate handlers that would repeat every log line.
    """

    raw_level: str = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level: int = getattr(logging, raw_level, logging.DEBUG)
    formatter: logging.Formatter = logging.Formatter(
        fmt=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )

    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        console_handler: logging.StreamHandler[str] = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
        return

    for handler in root_logger.handlers:
        handler.setLevel(log_level)
        handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after ensuring structured logging is configured."""

    configure_logging()
    return logging.getLogger(name)

