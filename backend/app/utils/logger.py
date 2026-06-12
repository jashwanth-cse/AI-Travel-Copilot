"""Structured logging helpers for backend modules."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

from app.utils.constants import APP_LOG_PATH, DEFAULT_LOG_LEVEL, LOG_DIR

_LOG_FORMAT: Final[str] = (
    "[%(asctime)s]\n%(levelname)s\n%(name)s\n%(message)s"
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

    # Windows terminals often default to cp1252, which cannot encode every
    # Unicode value that may arrive from travel APIs. Reconfiguring stdout keeps
    # structured logging from failing while preserving readable output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    formatter: logging.Formatter = logging.Formatter(
        fmt=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        console_handler: logging.StreamHandler[str] = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
            handler.setFormatter(formatter)

    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == str(APP_LOG_PATH)
        for handler in root_logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(APP_LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    # Keep third-party transport logs quiet. At DEBUG, httpx/httpcore include
    # full request URLs, which can expose API keys passed as query parameters.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after ensuring structured logging is configured."""

    configure_logging()
    return logging.getLogger(name)
