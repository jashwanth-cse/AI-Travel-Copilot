"""Analytics service for cached city travel data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.attraction import Attraction
from app.models.restaurant import Restaurant
from app.models.weather import Weather
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Read lightweight aggregate analytics from SQLite."""

    def get_city_analytics(
        self,
        city: str,
        *,
        db_session: Session | None = None,
    ) -> dict[str, Any]:
        """Return aggregate counts, rating, and update timestamp for a city."""

        normalized_city = city.strip()
        logger.info("Fetching analytics for city=%s", normalized_city)

        if db_session is not None:
            return self._query_city_analytics(session=db_session, city=normalized_city)

        with SessionLocal() as session:
            return self._query_city_analytics(session=session, city=normalized_city)

    def _query_city_analytics(self, *, session: Session, city: str) -> dict[str, Any]:
        """Execute analytics queries using an existing SQLAlchemy session."""

        city_pattern = f"%{city}%"
        total_attractions = session.scalar(
            select(func.count()).select_from(Attraction).where(Attraction.city.ilike(city_pattern))
        ) or 0
        total_restaurants = session.scalar(select(func.count()).select_from(Restaurant)) or 0

        attraction_average = session.scalar(
            select(func.avg(Attraction.rating)).where(Attraction.city.ilike(city_pattern))
        )
        restaurant_average = session.scalar(select(func.avg(Restaurant.rating)))
        rating_values = [
            float(value)
            for value in (attraction_average, restaurant_average)
            if value is not None
        ]
        average_rating = round(sum(rating_values) / len(rating_values), 2) if rating_values else 0.0

        last_updated = self._latest_timestamp(
            session.scalar(select(func.max(Attraction.updated_at)).where(Attraction.city.ilike(city_pattern))),
            session.scalar(select(func.max(Restaurant.updated_at))),
            session.scalar(select(func.max(Weather.updated_at)).where(Weather.city.ilike(city_pattern))),
        )

        analytics = {
            "city": city,
            "total_attractions": total_attractions,
            "total_restaurants": total_restaurants,
            "average_rating": average_rating,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }
        logger.debug("City analytics=%s", analytics)
        return analytics

    def _latest_timestamp(self, *values: datetime | None) -> datetime | None:
        """Return the newest non-null timestamp from aggregate queries."""

        timestamps = [value for value in values if value is not None]
        if not timestamps:
            return None
        return max(timestamps)
