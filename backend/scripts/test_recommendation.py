"""Standalone recommendation service check.

Run from the backend directory with:
    python scripts/test_recommendation.py
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.models.attraction import Attraction  # noqa: E402
from app.models.restaurant import Restaurant  # noqa: E402
from app.models.weather import Weather  # noqa: E402
from app.schemas.service_models import TripRequestData  # noqa: E402
from app.services.recommendation_service import RecommendationService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def seed_demo_data() -> None:
    """Insert deterministic sample rows for recommendation testing.

    The ETL pipeline can populate real data later. This script remains useful
    before API keys are available because it creates enough local records to
    validate senior-citizen, vegetarian, and budget scoring rules.
    """

    init_db()
    today = date.today()
    attractions = [
        {
            "place_id": "demo_ooty_botanical_garden",
            "name": "Government Botanical Garden",
            "rating": 4.6,
            "latitude": 11.4189,
            "longitude": 76.7114,
            "category": "garden",
            "city": "Ooty",
            "description": "Calm botanical garden and park suitable for relaxed walks.",
        },
        {
            "place_id": "demo_ooty_lake",
            "name": "Ooty Lake",
            "rating": 4.3,
            "latitude": 11.4064,
            "longitude": 76.6932,
            "category": "lake",
            "city": "Ooty",
            "description": "Popular lake with gentle sightseeing options.",
        },
        {
            "place_id": "demo_ooty_steep_trek",
            "name": "Steep Hill Trek Point",
            "rating": 4.9,
            "latitude": 11.41,
            "longitude": 76.72,
            "category": "trekking",
            "city": "Ooty",
            "description": "Steep hill trekking trail with climbing sections.",
        },
    ]
    restaurants = [
        {
            "place_id": "demo_ooty_veg_meals",
            "name": "Nilgiri Vegetarian Meals",
            "rating": 4.4,
            "vegetarian": True,
            "price_level": 2,
            "latitude": 11.41,
            "longitude": 76.70,
        },
        {
            "place_id": "demo_ooty_premium_grill",
            "name": "Premium Hill Grill",
            "rating": 4.7,
            "vegetarian": False,
            "price_level": 4,
            "latitude": 11.42,
            "longitude": 76.71,
        },
    ]

    with SessionLocal() as session:
        for attraction in attractions:
            statement = sqlite_insert(Attraction).values(**attraction)
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["place_id"],
                    set_={key: value for key, value in attraction.items() if key != "place_id"},
                )
            )

        for restaurant in restaurants:
            statement = sqlite_insert(Restaurant).values(**restaurant)
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["place_id"],
                    set_={key: value for key, value in restaurant.items() if key != "place_id"},
                )
            )

        for offset in range(3):
            forecast_date = today + timedelta(days=offset)
            session.query(Weather).filter(
                Weather.city == "Ooty",
                Weather.date == forecast_date,
            ).delete()
            session.add(
                Weather(
                    city="Ooty",
                    date=forecast_date,
                    temperature=18.5 + offset,
                    condition="light rain" if offset == 1 else "cloudy",
                )
            )
        session.commit()

    logger.info("Seeded demo recommendation data")


def main() -> None:
    """Run and print a recommendation result for the sample trip."""

    seed_demo_data()
    trip = TripRequestData(
        destination="Ooty",
        days=3,
        budget=15000,
        travelers=2,
        food_preference="vegetarian",
        senior_citizen=True,
    )
    result = RecommendationService().recommend(trip)
    print(result.model_dump())


if __name__ == "__main__":
    main()
