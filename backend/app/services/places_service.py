"""Geoapify places service for attractions and restaurants."""

from __future__ import annotations

from typing import Any

import httpx

from app.schemas.service_models import AttractionData, RestaurantData
from app.utils.config import get_env_value
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlacesService:
    """Fetch nearby attractions and restaurants from Geoapify Places."""

    BASE_URL: str = "https://api.geoapify.com/v2/places"
    DEFAULT_RADIUS_METERS: int = 10_000
    DEFAULT_LIMIT: int = 25

    # Categories are intentionally broad for MVP discovery. ETL will normalize
    # and filter data before persistence.
    ATTRACTION_CATEGORIES: str = "tourism.sights,entertainment,leisure,beach,natural"
    RESTAURANT_CATEGORIES: str = "catering.restaurant,catering.fast_food,catering.cafe"

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        """Create the service with a configurable network timeout."""

        self.timeout_seconds = timeout_seconds
        self.api_key = get_env_value("GEOAPIFY_API_KEY")

    def fetch_attractions(
        self,
        *,
        latitude: float,
        longitude: float,
        city: str,
        radius_meters: int = DEFAULT_RADIUS_METERS,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AttractionData]:
        """Fetch attraction candidates near a coordinate pair."""

        features = self._fetch_places(
            categories=self.ATTRACTION_CATEGORIES,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
            place_kind="attractions",
        )
        attractions: list[AttractionData] = []
        for feature in features:
            attraction = self._feature_to_attraction(feature=feature, city=city)
            if attraction is not None:
                attractions.append(attraction)
        logger.info("Fetched attractions city=%s count=%s", city, len(attractions))
        return attractions

    def fetch_restaurants(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_meters: int = DEFAULT_RADIUS_METERS,
        limit: int = DEFAULT_LIMIT,
    ) -> list[RestaurantData]:
        """Fetch restaurant candidates near a coordinate pair."""

        features = self._fetch_places(
            categories=self.RESTAURANT_CATEGORIES,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
            place_kind="restaurants",
        )
        restaurants: list[RestaurantData] = []
        for feature in features:
            restaurant = self._feature_to_restaurant(feature)
            if restaurant is not None:
                restaurants.append(restaurant)
        logger.info("Fetched restaurants count=%s", len(restaurants))
        return restaurants

    def _fetch_places(
        self,
        *,
        categories: str,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int,
        place_kind: str,
    ) -> list[dict[str, Any]]:
        """Call Geoapify Places and return raw feature dictionaries."""

        if not self.api_key:
            logger.error("Geoapify API key is not configured")
            return []

        params: dict[str, str | int] = {
            "categories": categories,
            "filter": f"circle:{longitude},{latitude},{radius_meters}",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": limit,
            "apiKey": self.api_key,
        }
        logger.info(
            "Fetching places kind=%s latitude=%s longitude=%s radius=%s limit=%s",
            place_kind,
            latitude,
            longitude,
            radius_meters,
            limit,
        )

        try:
            response = httpx.get(self.BASE_URL, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            logger.debug("Raw places response kind=%s response=%s", place_kind, payload)
        except httpx.HTTPStatusError as error:
            logger.error(
                "Geoapify Places HTTP error kind=%s status_code=%s error=%s",
                place_kind,
                error.response.status_code,
                error,
            )
            return []
        except httpx.HTTPError as error:
            logger.error("Geoapify Places request failed kind=%s error=%s", place_kind, error)
            return []
        except ValueError as error:
            logger.error("Geoapify Places returned invalid JSON kind=%s error=%s", place_kind, error)
            return []

        features = payload.get("features", [])
        if not isinstance(features, list):
            logger.warning("Geoapify Places response missing features kind=%s", place_kind)
            return []
        return features

    def _feature_to_attraction(self, *, feature: dict[str, Any], city: str) -> AttractionData | None:
        """Convert a Geoapify feature into a typed attraction model."""

        properties: dict[str, Any] = feature.get("properties", {})
        coordinates = self._extract_coordinates(feature)
        name = properties.get("name")
        place_id = properties.get("place_id")
        if not name or not place_id:
            logger.warning("Skipping attraction with missing name/place_id feature=%s", feature)
            return None

        categories: list[str] = properties.get("categories", []) or []
        description = properties.get("formatted") or properties.get("address_line2")
        return AttractionData(
            place_id=str(place_id),
            name=str(name),
            rating=self._extract_rating(properties),
            latitude=coordinates[0],
            longitude=coordinates[1],
            category=categories[0] if categories else None,
            city=city,
            description=description,
        )

    def _feature_to_restaurant(self, feature: dict[str, Any]) -> RestaurantData | None:
        """Convert a Geoapify feature into a typed restaurant model."""

        properties: dict[str, Any] = feature.get("properties", {})
        coordinates = self._extract_coordinates(feature)
        name = properties.get("name")
        place_id = properties.get("place_id")
        if not name or not place_id:
            logger.warning("Skipping restaurant with missing name/place_id feature=%s", feature)
            return None

        categories: list[str] = properties.get("categories", []) or []
        category_text = " ".join(categories).lower()
        return RestaurantData(
            place_id=str(place_id),
            name=str(name),
            rating=self._extract_rating(properties),
            vegetarian="vegetarian" in category_text or "vegan" in category_text,
            price_level=self._extract_price_level(properties),
            latitude=coordinates[0],
            longitude=coordinates[1],
        )

    def _extract_coordinates(self, feature: dict[str, Any]) -> tuple[float | None, float | None]:
        """Return latitude and longitude from GeoJSON coordinates."""

        geometry: dict[str, Any] = feature.get("geometry", {})
        coordinates: list[Any] = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            logger.warning("Places feature missing coordinates feature=%s", feature)
            return None, None
        try:
            return float(coordinates[1]), float(coordinates[0])
        except (TypeError, ValueError):
            logger.warning("Places feature has invalid coordinates coordinates=%s", coordinates)
            return None, None

    def _extract_rating(self, properties: dict[str, Any]) -> float | None:
        """Extract a rating from the fields Geoapify may provide."""

        raw_rating = properties.get("rating")
        if raw_rating is None:
            raw_rating = properties.get("rank", {}).get("popularity")
        try:
            return float(raw_rating) if raw_rating is not None else None
        except (TypeError, ValueError):
            logger.warning("Invalid rating value value=%s", raw_rating)
            return None

    def _extract_price_level(self, properties: dict[str, Any]) -> int | None:
        """Convert provider price hints into a simple integer price level."""

        raw_price = properties.get("price_level") or properties.get("price_range")
        if raw_price is None:
            return None
        if isinstance(raw_price, str):
            return max(1, min(len(raw_price), 4))
        try:
            return int(raw_price)
        except (TypeError, ValueError):
            logger.warning("Invalid price level value=%s", raw_price)
            return None
