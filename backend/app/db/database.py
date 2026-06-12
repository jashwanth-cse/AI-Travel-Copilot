"""SQLite and SQLAlchemy configuration for the backend."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.utils.constants import DEFAULT_DATABASE_PATH
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def _build_database_url() -> str:
    """Build the database URL from environment or local SQLite defaults."""

    configured_url: str | None = os.getenv("DATABASE_URL")
    if configured_url:
        logger.info("Using database URL from environment")
        return configured_url

    database_url: str = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
    logger.info("Using default SQLite database path=%s", DEFAULT_DATABASE_PATH)
    return database_url


DATABASE_URL: str = _build_database_url()

# SQLite needs check_same_thread=False when sessions may be used by FastAPI
# request handlers later. It is harmless for the current script-only phase.
engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    future=True,
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and always close it afterwards.

    This generator is ready for future FastAPI dependency injection while also
    being simple enough to reuse in standalone scripts.
    """

    db_session: Session = SessionLocal()
    logger.debug("Opened database session")
    try:
        yield db_session
    finally:
        db_session.close()
        logger.debug("Closed database session")

