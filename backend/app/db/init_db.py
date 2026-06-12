"""Database initialization utilities."""

from __future__ import annotations

from sqlalchemy import inspect

from app.db.database import Base, engine
from app.utils.logger import get_logger

# Importing app.models registers every model class with SQLAlchemy metadata.
import app.models  # noqa: F401

logger = get_logger(__name__)


def init_db() -> list[str]:
    """Create all configured database tables and return their names."""

    logger.info("Starting database table creation")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names: list[str] = sorted(inspector.get_table_names())
    logger.info("Database table creation complete tables=%s", table_names)
    return table_names


if __name__ == "__main__":
    created_tables: list[str] = init_db()
    logger.info("Initialized database with table_count=%s", len(created_tables))

