"""Standalone ETL service check.

Run from the backend directory with:
    python scripts/test_etl.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal  # noqa: E402
from app.models.attraction import Attraction  # noqa: E402
from app.models.restaurant import Restaurant  # noqa: E402
from app.models.weather import Weather  # noqa: E402
from app.services.etl_service import EtlService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Run ETL for Ooty and print resulting database counts."""

    city = "Ooty"
    service = EtlService()
    result = service.run_for_city(city)
    print(result.model_dump())

    if not result.success:
        logger.warning("ETL script completed unsuccessfully message=%s", result.message)
        return

    with SessionLocal() as session:
        attraction_count = session.scalar(select(func.count()).select_from(Attraction))
        restaurant_count = session.scalar(select(func.count()).select_from(Restaurant))
        weather_count = session.scalar(select(func.count()).select_from(Weather))

    print(
        {
            "database_counts": {
                "attractions": attraction_count,
                "restaurants": restaurant_count,
                "weather": weather_count,
            }
        }
    )


if __name__ == "__main__":
    main()
