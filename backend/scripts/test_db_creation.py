"""Verify SQLite database creation for project setup steps 1-4.

Run from the backend directory with:
    python scripts/test_db_creation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# Allow the script to be executed directly without installing the backend as a
# package. This keeps script-by-script testing simple during the MVP phase.
BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import engine  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.models.trip import Trip  # noqa: E402
from app.utils.constants import DEFAULT_DATABASE_PATH  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

EXPECTED_TABLES: set[str] = {
    "attractions",
    "itineraries",
    "restaurants",
    "trips",
    "weather",
}


def verify_database_creation() -> None:
    """Create tables and validate basic SQLAlchemy read/write behavior."""

    logger.info("Running database creation verification")
    created_tables: set[str] = set(init_db())
    missing_tables: set[str] = EXPECTED_TABLES - created_tables

    if missing_tables:
        logger.error("Missing expected database tables tables=%s", sorted(missing_tables))
        raise RuntimeError(f"Missing expected tables: {sorted(missing_tables)}")

    inspector = inspect(engine)
    logger.debug("Verified table names tables=%s", sorted(inspector.get_table_names()))

    # A tiny transaction verifies that models, sessions, and SQLite are wired
    # together. The row is rolled back so the verification stays repeatable.
    with Session(engine) as session:
        trip = Trip(
            destination="Ooty",
            days=3,
            budget=15000,
            travelers=2,
            food_preference="vegetarian",
            senior_citizen=True,
        )
        session.add(trip)
        session.flush()
        logger.debug("Inserted verification trip id=%s", trip.id)
        session.rollback()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.debug("Verified direct SQLite connection")

    logger.info("Database verification passed database_path=%s", DEFAULT_DATABASE_PATH)


if __name__ == "__main__":
    verify_database_creation()

