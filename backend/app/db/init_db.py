"""Database initialization utilities."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.database import Base, engine
from app.utils.logger import get_logger

# Importing app.models registers every model class with SQLAlchemy metadata.
import app.models  # noqa: F401

logger = get_logger(__name__)


def init_db() -> list[str]:
    """Create all configured database tables and return their names."""

    logger.info("Starting database table creation")
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_timestamp_migrations()

    inspector = inspect(engine)
    table_names: list[str] = sorted(inspector.get_table_names())
    logger.info("Database table creation complete tables=%s", table_names)
    return table_names


def _apply_sqlite_timestamp_migrations() -> None:
    """Add cache timestamp columns to older SQLite tables if they are missing.

    SQLite supports simple ALTER TABLE ADD COLUMN operations. We keep the
    migration nullable and then backfill existing rows so current databases are
    upgraded without losing data or requiring a migration framework.
    """

    timestamp_tables: tuple[str, ...] = ("attractions", "restaurants", "weather")
    inspector = inspect(engine)

    with engine.begin() as connection:
        for table_name in timestamp_tables:
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            if "created_at" not in existing_columns:
                logger.info("Adding created_at column table=%s", table_name)
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN created_at DATETIME"))

            if "updated_at" not in existing_columns:
                logger.info("Adding updated_at column table=%s", table_name)
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN updated_at DATETIME"))

            # ---------------------------------------------------------
            # Backfill older rows so cache freshness has a usable value
            # ---------------------------------------------------------
            connection.execute(
                text(
                    f"""
                    UPDATE {table_name}
                    SET
                        created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                        updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                    WHERE created_at IS NULL OR updated_at IS NULL
                    """
                )
            )


if __name__ == "__main__":
    created_tables: list[str] = init_db()
    logger.info("Initialized database with table_count=%s", len(created_tables))
