"""Rule-based recommendation service with transparent scoring."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.attraction import Attraction
from app.models.restaurant import Restaurant
from app.models.weather import Weather
from app.schemas.service_models import (
    RecommendationResult,
    ScoredAttraction,
    ScoredRestaurant,
    TripRequestData,
    WeatherForecast,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RecommendationService:
    """Generate destination recommendations from cleaned SQLite data.

    The MVP keeps the engine intentionally transparent: each candidate starts
    from a rating-driven score and then receives additive rule adjustments for
    senior-friendly attractions, vegetarian preference, budget fit, and group
    travel. Scores are not meant to be universal truth; they are a readable
    first-pass ranking that later ML or vector search can replace.
    """

    SENIOR_AVOID_TERMS: tuple[str, ...] = (
        "trek",
        "trekking",
        "hike",
        "hiking",
        "steep",
        "hill",
        "mountain",
        "climb",
    )
    SENIOR_PREFER_TERMS: tuple[str, ...] = (
        "lake",
        "garden",
        "park",
        "botanical",
        "viewpoint",
        "museum",
    )

    def recommend(
        self,
        trip: TripRequestData,
        *,
        max_attractions: int = 8,
        max_restaurants: int = 6,
        db_session: Session | None = None,
    ) -> RecommendationResult:
        """Return ranked attractions, restaurants, and weather for a trip."""

        logger.info(
            "Generating recommendations destination=%s days=%s budget=%s travelers=%s",
            trip.destination,
            trip.days,
            trip.budget,
            trip.travelers,
        )

        try:
            if db_session is not None:
                # API routes pass a dependency-injected session so request
                # lifecycle and rollback/close behavior stay centralized.
                attractions = self._fetch_attractions(session=db_session, city=trip.destination)
                restaurants = self._fetch_restaurants(session=db_session)
                weather = self._fetch_weather(session=db_session, city=trip.destination, days=trip.days)
            else:
                # Standalone scripts still work without needing FastAPI's
                # dependency system.
                with SessionLocal() as session:
                    attractions = self._fetch_attractions(session=session, city=trip.destination)
                    restaurants = self._fetch_restaurants(session=session)
                    weather = self._fetch_weather(session=session, city=trip.destination, days=trip.days)
        except Exception as error:
            logger.error("Recommendation query failed destination=%s error=%s", trip.destination, error)
            return RecommendationResult(
                trip=trip,
                success=False,
                message="Recommendation lookup failed",
            )

        scored_attractions = [
            self._score_attraction(attraction=attraction, trip=trip)
            for attraction in attractions
        ]
        scored_restaurants = [
            self._score_restaurant(restaurant=restaurant, trip=trip)
            for restaurant in restaurants
        ]

        ranked_attractions = sorted(scored_attractions, key=lambda item: item.score, reverse=True)
        ranked_restaurants = sorted(scored_restaurants, key=lambda item: item.score, reverse=True)

        logger.debug(
            "Recommendation scoring complete attraction_scores=%s restaurant_scores=%s",
            [item.model_dump() for item in ranked_attractions[:max_attractions]],
            [item.model_dump() for item in ranked_restaurants[:max_restaurants]],
        )
        logger.info(
            "Recommendations generated destination=%s attractions=%s restaurants=%s weather=%s",
            trip.destination,
            len(ranked_attractions),
            len(ranked_restaurants),
            len(weather),
        )

        return RecommendationResult(
            trip=trip,
            attractions=ranked_attractions[:max_attractions],
            restaurants=ranked_restaurants[:max_restaurants],
            weather=weather,
        )

    def _fetch_attractions(self, *, session: Session, city: str) -> list[Attraction]:
        """Fetch city-matched attractions, falling back to all data if needed."""

        city_pattern = f"%{city.strip()}%"
        rows = list(
            session.scalars(
                select(Attraction).where(Attraction.city.ilike(city_pattern))
            )
        )
        if rows:
            logger.debug("Fetched city-specific attractions city=%s count=%s", city, len(rows))
            return rows

        fallback_rows = list(session.scalars(select(Attraction)))
        logger.warning(
            "No city-specific attractions found city=%s fallback_count=%s",
            city,
            len(fallback_rows),
        )
        return fallback_rows

    def _fetch_restaurants(self, *, session: Session) -> list[Restaurant]:
        """Fetch restaurants from the database."""

        rows = list(session.scalars(select(Restaurant)))
        logger.debug("Fetched restaurants count=%s", len(rows))
        return rows

    def _fetch_weather(self, *, session: Session, city: str, days: int) -> list[WeatherForecast]:
        """Fetch weather forecasts for the destination city."""

        city_pattern = f"%{city.strip()}%"
        rows = list(
            session.scalars(
                select(Weather)
                .where(Weather.city.ilike(city_pattern))
                .order_by(Weather.date)
                .limit(days)
            )
        )
        forecasts = [
            WeatherForecast(
                city=row.city,
                date=row.date,
                temperature=row.temperature,
                condition=row.condition,
            )
            for row in rows
        ]
        logger.debug("Fetched weather forecasts city=%s count=%s", city, len(forecasts))
        return forecasts

    def _score_attraction(self, *, attraction: Attraction, trip: TripRequestData) -> ScoredAttraction:
        """Score an attraction using rating plus preference rules."""

        reasons: list[str] = []
        score = self._rating_score(attraction.rating)
        reasons.append(f"rating_score={score:.2f}")

        searchable_text = " ".join(
            [
                attraction.name or "",
                attraction.category or "",
                attraction.description or "",
            ]
        ).lower()

        if trip.senior_citizen:
            if any(term in searchable_text for term in self.SENIOR_AVOID_TERMS):
                score -= 4.0
                reasons.append("senior_penalty=avoid_steep_or_trekking")
            if any(term in searchable_text for term in self.SENIOR_PREFER_TERMS):
                score += 3.0
                reasons.append("senior_bonus=calmer_accessible_place")

        # Longer trips can tolerate more varied attractions; short trips favor
        # highly rated and general-interest places by giving a small boost to
        # broad tourism categories.
        if trip.days <= 2 and "tourism" in searchable_text:
            score += 0.75
            reasons.append("short_trip_bonus=general_interest")

        if trip.travelers >= 4 and any(term in searchable_text for term in ("park", "garden", "lake")):
            score += 0.75
            reasons.append("group_bonus=open_space")

        final_score = round(max(score, 0.0), 2)
        logger.debug(
            "Scored attraction place_id=%s name=%s score=%s reasons=%s",
            attraction.place_id,
            attraction.name,
            final_score,
            reasons,
        )
        return ScoredAttraction(
            place_id=attraction.place_id,
            name=attraction.name,
            score=final_score,
            rating=attraction.rating,
            category=attraction.category,
            city=attraction.city,
            description=attraction.description,
            reasons=reasons,
        )

    def _score_restaurant(self, *, restaurant: Restaurant, trip: TripRequestData) -> ScoredRestaurant:
        """Score a restaurant using rating, food preference, and budget fit."""

        reasons: list[str] = []
        score = self._rating_score(restaurant.rating)
        reasons.append(f"rating_score={score:.2f}")

        preference = trip.food_preference.strip().lower()
        if preference in {"vegetarian", "veg", "vegan"}:
            if restaurant.vegetarian:
                score += 4.0
                reasons.append("food_bonus=vegetarian_match")
            else:
                score -= 2.0
                reasons.append("food_penalty=vegetarian_not_confirmed")

        budget_per_person_per_day = trip.budget / max(trip.travelers * trip.days, 1)
        price_level = restaurant.price_level or 2
        if budget_per_person_per_day < 1500 and price_level >= 4:
            score -= 3.0
            reasons.append("budget_penalty=expensive")
        elif budget_per_person_per_day < 2500 and price_level <= 2:
            score += 1.5
            reasons.append("budget_bonus=value_friendly")
        elif budget_per_person_per_day >= 4000 and price_level >= 3:
            score += 0.75
            reasons.append("budget_bonus=premium_allowed")

        final_score = round(max(score, 0.0), 2)
        logger.debug(
            "Scored restaurant place_id=%s name=%s score=%s reasons=%s",
            restaurant.place_id,
            restaurant.name,
            final_score,
            reasons,
        )
        return ScoredRestaurant(
            place_id=restaurant.place_id,
            name=restaurant.name,
            score=final_score,
            rating=restaurant.rating,
            vegetarian=restaurant.vegetarian,
            price_level=restaurant.price_level,
            reasons=reasons,
        )

    def _rating_score(self, rating: float | None) -> float:
        """Convert provider rating/popularity into a bounded base score."""

        if rating is None:
            return 2.5
        # Ratings may come from different providers. Keep a normal 0-5 rating
        # meaningful, while taming larger popularity-style scores.
        if rating <= 5:
            return rating * 2
        return min(rating, 10.0)
