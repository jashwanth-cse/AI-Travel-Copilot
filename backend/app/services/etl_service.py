"""ETL service that fetches, cleans, and loads travel data into SQLite."""

from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.models.attraction import Attraction
from app.models.restaurant import Restaurant
from app.models.weather import Weather
from app.schemas.service_models import AttractionData, EtlResult, RestaurantData, WeatherForecast
from app.services.geocoding_service import GeocodingService
from app.services.places_service import PlacesService
from app.services.weather_service import WeatherService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EtlService:
    """Coordinate extraction, transformation, and loading for one city."""

    def __init__(
        self,
        geocoding_service: GeocodingService | None = None,
        places_service: PlacesService | None = None,
        weather_service: WeatherService | None = None,
    ) -> None:
        """Create ETL with injectable services for script testing."""

        self.geocoding_service = geocoding_service or GeocodingService()
        self.places_service = places_service or PlacesService()
        self.weather_service = weather_service or WeatherService()

    def run_for_city(self, city: str) -> EtlResult:
        """Fetch live travel data, clean it, and populate SQLite automatically."""

        normalized_city: str = city.strip()
        if not normalized_city:
            logger.warning("Cannot run ETL for empty city")
            return EtlResult(city=city, success=False, message="City is required")

        logger.info("Starting ETL city=%s", normalized_city)
        init_db()

        coordinates = self.geocoding_service.geocode_city(normalized_city)
        if coordinates is None:
            logger.error("ETL stopped because geocoding failed city=%s", normalized_city)
            return EtlResult(city=normalized_city, success=False, message="Geocoding failed")

        raw_attractions = self.places_service.fetch_attractions(
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
            city=normalized_city,
        )
        raw_restaurants = self.places_service.fetch_restaurants(
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
        )
        raw_weather = self.weather_service.fetch_forecast(normalized_city)

        attractions = self._clean_attractions(raw_attractions)
        restaurants = self._clean_restaurants(raw_restaurants)
        weather = self._clean_weather(raw_weather)

        with SessionLocal() as session:
            attractions_loaded = self._load_attractions(session, attractions)
            restaurants_loaded = self._load_restaurants(session, restaurants)
            weather_loaded = self._load_weather(session, weather)
            session.commit()

        result = EtlResult(
            city=normalized_city,
            attractions_loaded=attractions_loaded,
            restaurants_loaded=restaurants_loaded,
            weather_loaded=weather_loaded,
        )
        logger.info("ETL completed result=%s", result.model_dump())
        return result

    def _clean_attractions(self, attractions: list[AttractionData]) -> list[AttractionData]:
        """Apply MVP cleaning rules to attraction records."""

        cleaned: list[AttractionData] = []
        seen_place_ids: set[str] = set()
        for attraction in attractions:
            if not attraction.name.strip():
                logger.warning("Skipping attraction with null/blank name place_id=%s", attraction.place_id)
                continue
            if attraction.place_id in seen_place_ids:
                logger.debug("Skipping duplicate attraction place_id=%s", attraction.place_id)
                continue
            if not self._valid_coordinates(attraction.latitude, attraction.longitude):
                logger.warning("Skipping attraction with invalid coordinates place_id=%s", attraction.place_id)
                continue

            seen_place_ids.add(attraction.place_id)
            cleaned.append(
                attraction.model_copy(
                    update={
                        "name": attraction.name.strip(),
                        "category": self._normalize_category(attraction.category),
                    }
                )
            )
        logger.info("Cleaned attractions input=%s output=%s", len(attractions), len(cleaned))
        return cleaned

    def _clean_restaurants(self, restaurants: list[RestaurantData]) -> list[RestaurantData]:
        """Apply MVP cleaning rules to restaurant records."""

        cleaned: list[RestaurantData] = []
        seen_place_ids: set[str] = set()
        for restaurant in restaurants:
            if not restaurant.name.strip():
                logger.warning("Skipping restaurant with null/blank name place_id=%s", restaurant.place_id)
                continue
            if restaurant.place_id in seen_place_ids:
                logger.debug("Skipping duplicate restaurant place_id=%s", restaurant.place_id)
                continue
            if not self._valid_coordinates(restaurant.latitude, restaurant.longitude):
                logger.warning("Skipping restaurant with invalid coordinates place_id=%s", restaurant.place_id)
                continue

            seen_place_ids.add(restaurant.place_id)
            cleaned.append(restaurant.model_copy(update={"name": restaurant.name.strip()}))
        logger.info("Cleaned restaurants input=%s output=%s", len(restaurants), len(cleaned))
        return cleaned

    def _clean_weather(self, forecasts: list[WeatherForecast]) -> list[WeatherForecast]:
        """Deduplicate weather forecasts by city and date."""

        cleaned: list[WeatherForecast] = []
        seen_keys: set[tuple[str, str]] = set()
        for forecast in forecasts:
            key = (forecast.city.lower(), forecast.date.isoformat())
            if key in seen_keys:
                logger.debug("Skipping duplicate weather forecast key=%s", key)
                continue
            seen_keys.add(key)
            cleaned.append(forecast)
        logger.info("Cleaned weather input=%s output=%s", len(forecasts), len(cleaned))
        return cleaned

    def _load_attractions(self, session: Session, attractions: list[AttractionData]) -> int:
        """Insert or replace attractions using SQLite upsert semantics."""

        for attraction in attractions:
            values = attraction.model_dump()
            statement = sqlite_insert(Attraction).values(**values)
            update_values = {
                key: value
                for key, value in values.items()
                if key != "place_id"
            }
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["place_id"],
                    set_=update_values,
                )
            )
        logger.info("Loaded attractions count=%s", len(attractions))
        return len(attractions)

    def _load_restaurants(self, session: Session, restaurants: list[RestaurantData]) -> int:
        """Insert or replace restaurants using SQLite upsert semantics."""

        for restaurant in restaurants:
            values = restaurant.model_dump()
            statement = sqlite_insert(Restaurant).values(**values)
            update_values = {
                key: value
                for key, value in values.items()
                if key != "place_id"
            }
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["place_id"],
                    set_=update_values,
                )
            )
        logger.info("Loaded restaurants count=%s", len(restaurants))
        return len(restaurants)

    def _load_weather(self, session: Session, forecasts: list[WeatherForecast]) -> int:
        """Replace existing forecasts for the same city/date pairs."""

        for forecast in forecasts:
            session.query(Weather).filter(
                Weather.city == forecast.city,
                Weather.date == forecast.date,
            ).delete()
            session.add(Weather(**forecast.model_dump()))
        logger.info("Loaded weather forecasts count=%s", len(forecasts))
        return len(forecasts)

    def _normalize_category(self, category: str | None) -> str | None:
        """Normalize category strings for future recommendation filtering."""

        if category is None:
            return None
        return category.strip().lower().replace(".", "_").replace(" ", "_")

    def _valid_coordinates(self, latitude: float | None, longitude: float | None) -> bool:
        """Validate latitude and longitude ranges."""

        if latitude is None or longitude is None:
            return False
        return -90 <= latitude <= 90 and -180 <= longitude <= 180
