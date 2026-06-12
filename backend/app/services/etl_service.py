"""ETL service that uses Pandas for transformation before SQLite loading."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sqlalchemy import func, select
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

CACHE_TTL_HOURS: int = 24


@dataclass(slots=True)
class EtlPipelineReport:
    """Execution counters captured during the latest ETL run.

    The service return type remains the existing EtlResult for backward
    compatibility. Scripts that need richer diagnostics can read this report
    from EtlService.last_report after calling run_for_city().
    """

    city: str = ""
    raw_attractions: int = 0
    cleaned_attractions: int = 0
    inserted_attractions: int = 0
    raw_restaurants: int = 0
    cleaned_restaurants: int = 0
    inserted_restaurants: int = 0
    raw_weather: int = 0
    cleaned_weather: int = 0
    inserted_weather: int = 0


def clean_places_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean attraction records with Pandas transformations.

    Expected columns match AttractionData fields. Missing optional columns are
    created so downstream load logic can rely on a stable shape.
    """

    logger.debug("Attractions DataFrame columns=%s", df.columns.tolist())
    if df.empty:
        logger.info("Rows after cleaning=%d", 0)
        return _ensure_columns(
            df.copy(),
            ["place_id", "name", "rating", "latitude", "longitude", "category", "city", "description"],
        )

    cleaned = _ensure_columns(
        df.copy(),
        ["place_id", "name", "rating", "latitude", "longitude", "category", "city", "description"],
    )
    starting_rows = len(cleaned)

    # ---------------------------------------------------------
    # Strip leading/trailing spaces from all text-like fields
    # ---------------------------------------------------------
    cleaned = _strip_string_columns(cleaned, ["place_id", "name", "category", "city", "description"])

    # ---------------------------------------------------------
    # Remove duplicate places based on unique place_id
    # ---------------------------------------------------------
    cleaned = cleaned.drop_duplicates(subset=["place_id"], keep="first")

    # ---------------------------------------------------------
    # Remove rows with missing names or identifiers
    # ---------------------------------------------------------
    cleaned = cleaned.dropna(subset=["place_id", "name"])
    cleaned = cleaned[(cleaned["place_id"] != "") & (cleaned["name"] != "")]

    # ---------------------------------------------------------
    # Convert numeric fields; invalid values become NaN
    # ---------------------------------------------------------
    cleaned["rating"] = pd.to_numeric(cleaned["rating"], errors="coerce").fillna(0).astype(float)
    cleaned["latitude"] = pd.to_numeric(cleaned["latitude"], errors="coerce")
    cleaned["longitude"] = pd.to_numeric(cleaned["longitude"], errors="coerce")

    # ---------------------------------------------------------
    # Validate coordinate ranges and remove invalid records
    # ---------------------------------------------------------
    cleaned = cleaned[
        cleaned["latitude"].between(-90, 90, inclusive="both")
        & cleaned["longitude"].between(-180, 180, inclusive="both")
    ]

    # ---------------------------------------------------------
    # Normalize category names to lowercase snake-like values
    # ---------------------------------------------------------
    cleaned["category"] = (
        cleaned["category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(".", "_", regex=False)
        .str.replace(" ", "_", regex=False)
    )
    cleaned["category"] = cleaned["category"].replace("", None)

    cleaned = _replace_pandas_missing_values(cleaned)
    dropped_rows = starting_rows - len(cleaned)
    if dropped_rows > 0:
        logger.warning("Dropped %d invalid rows", dropped_rows)
    logger.info("Rows after cleaning=%d", len(cleaned))
    return cleaned.reset_index(drop=True)


def clean_restaurants_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean restaurant records with Pandas transformations."""

    logger.debug("Restaurants DataFrame columns=%s", df.columns.tolist())
    if df.empty:
        logger.info("Rows after cleaning=%d", 0)
        return _ensure_columns(
            df.copy(),
            ["place_id", "name", "rating", "vegetarian", "price_level", "latitude", "longitude"],
        )

    cleaned = _ensure_columns(
        df.copy(),
        ["place_id", "name", "rating", "vegetarian", "price_level", "latitude", "longitude"],
    )
    starting_rows = len(cleaned)

    # ---------------------------------------------------------
    # Strip leading/trailing spaces from all text-like fields
    # ---------------------------------------------------------
    cleaned = _strip_string_columns(cleaned, ["place_id", "name"])

    # ---------------------------------------------------------
    # Remove duplicate restaurants based on unique place_id
    # ---------------------------------------------------------
    cleaned = cleaned.drop_duplicates(subset=["place_id"], keep="first")

    # ---------------------------------------------------------
    # Remove rows with missing names or identifiers
    # ---------------------------------------------------------
    cleaned = cleaned.dropna(subset=["place_id", "name"])
    cleaned = cleaned[(cleaned["place_id"] != "") & (cleaned["name"] != "")]

    # ---------------------------------------------------------
    # Convert numeric fields; invalid ratings become zero
    # ---------------------------------------------------------
    cleaned["rating"] = pd.to_numeric(cleaned["rating"], errors="coerce").fillna(0).astype(float)
    cleaned["price_level"] = pd.to_numeric(cleaned["price_level"], errors="coerce")
    cleaned["latitude"] = pd.to_numeric(cleaned["latitude"], errors="coerce")
    cleaned["longitude"] = pd.to_numeric(cleaned["longitude"], errors="coerce")

    # ---------------------------------------------------------
    # Validate coordinate ranges and remove invalid records
    # ---------------------------------------------------------
    cleaned = cleaned[
        cleaned["latitude"].between(-90, 90, inclusive="both")
        & cleaned["longitude"].between(-180, 180, inclusive="both")
    ]

    # ---------------------------------------------------------
    # Normalize boolean vegetarian flags and nullable price levels
    # ---------------------------------------------------------
    cleaned["vegetarian"] = cleaned["vegetarian"].apply(_normalize_boolean)
    cleaned["price_level"] = cleaned["price_level"].apply(
        lambda value: int(value) if pd.notna(value) else None
    )

    cleaned = _replace_pandas_missing_values(cleaned)
    dropped_rows = starting_rows - len(cleaned)
    if dropped_rows > 0:
        logger.warning("Dropped %d invalid rows", dropped_rows)
    logger.info("Rows after cleaning=%d", len(cleaned))
    return cleaned.reset_index(drop=True)


def clean_weather_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean weather forecast records with Pandas transformations."""

    logger.debug("Weather DataFrame columns=%s", df.columns.tolist())
    if df.empty:
        logger.info("Rows after cleaning=%d", 0)
        return _ensure_columns(df.copy(), ["city", "date", "temperature", "condition"])

    cleaned = _ensure_columns(df.copy(), ["city", "date", "temperature", "condition"])
    starting_rows = len(cleaned)

    # ---------------------------------------------------------
    # Strip leading/trailing spaces from text-like fields
    # ---------------------------------------------------------
    cleaned = _strip_string_columns(cleaned, ["city", "condition"])

    # ---------------------------------------------------------
    # Remove records without city or forecast date
    # ---------------------------------------------------------
    cleaned = cleaned.dropna(subset=["city", "date"])
    cleaned = cleaned[cleaned["city"] != ""]

    # ---------------------------------------------------------
    # Normalize dates and numeric temperature values
    # ---------------------------------------------------------
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce").dt.date
    cleaned["temperature"] = pd.to_numeric(cleaned["temperature"], errors="coerce")

    # ---------------------------------------------------------
    # Remove invalid dates and duplicate city/date forecasts
    # ---------------------------------------------------------
    cleaned = cleaned.dropna(subset=["date"])
    cleaned = cleaned.drop_duplicates(subset=["city", "date"], keep="first")

    cleaned = _replace_pandas_missing_values(cleaned)
    dropped_rows = starting_rows - len(cleaned)
    if dropped_rows > 0:
        logger.warning("Dropped %d invalid rows", dropped_rows)
    logger.info("Rows after cleaning=%d", len(cleaned))
    return cleaned.reset_index(drop=True)


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Ensure a DataFrame contains every expected column."""

    for column in columns:
        if column not in df.columns:
            df[column] = None
    return df[columns]


def _strip_string_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Strip whitespace from selected string columns while preserving nulls."""

    for column in columns:
        df[column] = df[column].apply(lambda value: value.strip() if isinstance(value, str) else value)
    return df


def _replace_pandas_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Pandas NaN/NA values to plain None for SQLAlchemy models."""

    return df.astype(object).where(pd.notna(df), None)


def _normalize_boolean(value: object) -> bool:
    """Normalize mixed provider boolean values to a real bool."""

    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "vegetarian", "vegan"}
    return bool(value)


def is_city_data_fresh(city: str) -> bool:
    """Return True when locally cached city data is present and fresh.

    Freshness is based on the newest cache timestamps stored in SQLite. The
    attractions and weather tables are city-aware, while restaurants remain
    city-agnostic because the existing schema intentionally has no city column.
    """

    normalized_city = city.strip()
    if not normalized_city:
        logger.warning("Cannot check cache freshness for empty city")
        return False

    init_db()
    threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=CACHE_TTL_HOURS)
    city_pattern = f"%{normalized_city}%"

    with SessionLocal() as session:
        attractions_count = session.scalar(
            select(func.count()).select_from(Attraction).where(Attraction.city.ilike(city_pattern))
        ) or 0
        weather_count = session.scalar(
            select(func.count()).select_from(Weather).where(Weather.city.ilike(city_pattern))
        ) or 0
        restaurants_count = session.scalar(select(func.count()).select_from(Restaurant)) or 0

        last_attraction_update = session.scalar(
            select(func.max(Attraction.updated_at)).where(Attraction.city.ilike(city_pattern))
        )
        last_weather_update = session.scalar(
            select(func.max(Weather.updated_at)).where(Weather.city.ilike(city_pattern))
        )
        last_restaurant_update = session.scalar(select(func.max(Restaurant.updated_at)))

    if attractions_count == 0 or weather_count == 0 or restaurants_count == 0:
        logger.info("Cache expired for city=%s", normalized_city)
        return False

    cache_timestamps = [
        timestamp
        for timestamp in (last_attraction_update, last_weather_update, last_restaurant_update)
        if timestamp is not None
    ]
    if len(cache_timestamps) < 3:
        logger.info("Cache expired for city=%s", normalized_city)
        return False

    is_fresh = min(cache_timestamps) >= threshold
    if is_fresh:
        logger.info("Using cached data for city=%s", normalized_city)
        return True

    logger.info("Cache expired for city=%s", normalized_city)
    return False


def refresh_city_data(city: str) -> EtlResult:
    """Use cached city data when fresh, otherwise run the ETL pipeline."""

    normalized_city = city.strip()
    if is_city_data_fresh(normalized_city):
        return EtlResult(city=normalized_city, success=True, message="Using cached data")

    logger.info("Running ETL pipeline")
    return EtlService().run_for_city(normalized_city)


class EtlService:
    """Coordinate extraction, Pandas transformation, and SQLite loading."""

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
        self.last_report = EtlPipelineReport()

    def run_for_city(self, city: str) -> EtlResult:
        """Fetch live travel data, clean it with Pandas, and populate SQLite."""

        started_at = time.perf_counter()
        normalized_city: str = city.strip()
        self.last_report = EtlPipelineReport(city=normalized_city)
        if not normalized_city:
            logger.warning("Cannot run ETL for empty city")
            elapsed = time.perf_counter() - started_at
            logger.info("ETL pipeline completed in %.2f seconds", elapsed)
            return EtlResult(city=city, success=False, message="City is required")

        logger.info("Starting ETL pipeline for city=%s", normalized_city)
        init_db()

        coordinates = self.geocoding_service.geocode_city(normalized_city)
        if coordinates is None:
            logger.error("ETL stopped because geocoding failed city=%s", normalized_city)
            elapsed = time.perf_counter() - started_at
            logger.info("ETL pipeline completed in %.2f seconds", elapsed)
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

        self.last_report.raw_attractions = len(raw_attractions)
        self.last_report.raw_restaurants = len(raw_restaurants)
        self.last_report.raw_weather = len(raw_weather)
        logger.info("Raw attractions count=%d", len(raw_attractions))
        logger.info("Raw restaurants count=%d", len(raw_restaurants))
        logger.info("Raw weather count=%d", len(raw_weather))

        attractions_df = clean_places_dataframe(self._models_to_dataframe(raw_attractions))
        restaurants_df = clean_restaurants_dataframe(self._models_to_dataframe(raw_restaurants))
        weather_df = clean_weather_dataframe(self._models_to_dataframe(raw_weather))

        self.last_report.cleaned_attractions = len(attractions_df)
        self.last_report.cleaned_restaurants = len(restaurants_df)
        self.last_report.cleaned_weather = len(weather_df)

        attractions = self._dataframe_to_attractions(attractions_df)
        restaurants = self._dataframe_to_restaurants(restaurants_df)
        weather = self._dataframe_to_weather(weather_df)

        with SessionLocal() as session:
            attractions_loaded = self._load_attractions(session, attractions)
            restaurants_loaded = self._load_restaurants(session, restaurants)
            weather_loaded = self._load_weather(session, weather)
            session.commit()

        self.last_report.inserted_attractions = attractions_loaded
        self.last_report.inserted_restaurants = restaurants_loaded
        self.last_report.inserted_weather = weather_loaded

        result = EtlResult(
            city=normalized_city,
            attractions_loaded=attractions_loaded,
            restaurants_loaded=restaurants_loaded,
            weather_loaded=weather_loaded,
        )
        logger.info("ETL completed successfully")
        logger.info("ETL completed result=%s", result.model_dump())
        elapsed = time.perf_counter() - started_at
        logger.info("ETL pipeline completed in %.2f seconds", elapsed)
        return result

    def _models_to_dataframe(
        self,
        records: list[AttractionData] | list[RestaurantData] | list[WeatherForecast],
    ) -> pd.DataFrame:
        """Convert Pydantic service models into a Pandas DataFrame."""

        rows: list[dict[str, Any]] = [record.model_dump() for record in records]
        dataframe = pd.DataFrame(rows)
        logger.debug("DataFrame columns=%s", dataframe.columns.tolist())
        return dataframe

    def _dataframe_to_attractions(self, df: pd.DataFrame) -> list[AttractionData]:
        """Convert a cleaned attractions DataFrame back to typed models."""

        rows = df.to_dict(orient="records")
        return [AttractionData(**row) for row in rows]

    def _dataframe_to_restaurants(self, df: pd.DataFrame) -> list[RestaurantData]:
        """Convert a cleaned restaurants DataFrame back to typed models."""

        rows = df.to_dict(orient="records")
        return [RestaurantData(**row) for row in rows]

    def _dataframe_to_weather(self, df: pd.DataFrame) -> list[WeatherForecast]:
        """Convert a cleaned weather DataFrame back to typed models."""

        rows = df.to_dict(orient="records")
        return [
            WeatherForecast(
                city=str(row["city"]),
                date=row["date"] if isinstance(row["date"], date) else pd.to_datetime(row["date"]).date(),
                temperature=row.get("temperature"),
                condition=row.get("condition"),
            )
            for row in rows
        ]

    def _load_attractions(self, session: Session, attractions: list[AttractionData]) -> int:
        """Insert or replace attractions using SQLite upsert semantics."""

        for attraction in attractions:
            current_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
            values = {
                **attraction.model_dump(),
                "created_at": current_timestamp,
                "updated_at": current_timestamp,
            }
            statement = sqlite_insert(Attraction).values(**values)
            update_values = {
                key: value
                for key, value in values.items()
                if key not in {"place_id", "created_at"}
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
            current_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
            values = {
                **restaurant.model_dump(),
                "created_at": current_timestamp,
                "updated_at": current_timestamp,
            }
            statement = sqlite_insert(Restaurant).values(**values)
            update_values = {
                key: value
                for key, value in values.items()
                if key not in {"place_id", "created_at"}
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
            current_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
            session.query(Weather).filter(
                Weather.city == forecast.city,
                Weather.date == forecast.date,
            ).delete()
            session.add(
                Weather(
                    **forecast.model_dump(),
                    created_at=current_timestamp,
                    updated_at=current_timestamp,
                )
            )
        logger.info("Loaded weather forecasts count=%s", len(forecasts))
        return len(forecasts)
