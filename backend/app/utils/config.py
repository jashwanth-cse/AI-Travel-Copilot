"""Environment configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from app.utils.constants import BACKEND_DIR
from app.utils.logger import get_logger

logger = get_logger(__name__)

_ENV_LOADED: bool = False


def load_environment() -> None:
    """Load backend/.env once for scripts and services.

    The project spec requires API keys to be read from .env. Loading happens
    lazily here so standalone scripts, tests, and future FastAPI startup code
    all share the same behavior.
    """

    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path: Path = BACKEND_DIR / ".env"
    loaded: bool = load_dotenv(dotenv_path=env_path)
    logger.debug("Loaded environment file path=%s loaded=%s", env_path, loaded)
    _ENV_LOADED = True


def get_env_value(name: str) -> str | None:
    """Return a stripped environment value after loading backend/.env."""

    load_environment()
    value: str | None = os.getenv(name)
    if value is None or not value.strip():
        logger.warning("Missing environment variable name=%s", name)
        return None
    return value.strip()
