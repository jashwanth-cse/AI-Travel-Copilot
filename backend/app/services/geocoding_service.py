"""Geoapify geocoding service."""

from __future__ import annotations

from typing import Any

import httpx

from app.schemas.service_models import Coordinates
from app.utils.config import get_env_value
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeocodingService:
    """Fetch destination coordinates from Geoapify Geocoding."""

    BASE_URL: str = "https://api.geoapify.com/v1/geocode/search"

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        """Create the service with a configurable network timeout."""

        self.timeout_seconds = timeout_seconds
        self.api_key = get_env_value("GEOAPIFY_API_KEY")

    def geocode_city(self, city: str) -> Coordinates | None:
        """Return coordinates for a city, or None when lookup fails.

        API failures are logged and converted into None so scripts and later
        pipelines can fail gracefully without crashing the entire application.
        """

        normalized_city: str = city.strip()
        if not normalized_city:
            logger.warning("Cannot geocode empty city")
            return None

        if not self.api_key:
            logger.error("Geoapify API key is not configured")
            return None

        params: dict[str, str] = {
            "text": normalized_city,
            "format": "json",
            "apiKey": self.api_key,
        }
        logger.info("Fetching geocode for city=%s", normalized_city)

        try:
            response = httpx.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            logger.debug("Raw geocoding response=%s", payload)
        except httpx.HTTPStatusError as error:
            logger.error(
                "Geoapify geocoding HTTP error city=%s status_code=%s error=%s",
                normalized_city,
                error.response.status_code,
                error,
            )
            return None
        except httpx.HTTPError as error:
            logger.error("Geoapify geocoding request failed city=%s error=%s", normalized_city, error)
            return None
        except ValueError as error:
            logger.error("Geoapify geocoding returned invalid JSON city=%s error=%s", normalized_city, error)
            return None

        results: list[dict[str, Any]] = payload.get("results", [])
        if not results:
            logger.warning("No geocoding results found for city=%s", normalized_city)
            return None

        first_result: dict[str, Any] = results[0]
        latitude = first_result.get("lat")
        longitude = first_result.get("lon")
        if latitude is None or longitude is None:
            logger.warning("Geocoding result missing coordinates city=%s result=%s", normalized_city, first_result)
            return None

        coordinates = Coordinates(
            city=normalized_city,
            latitude=float(latitude),
            longitude=float(longitude),
            country=first_result.get("country"),
            formatted_address=first_result.get("formatted"),
        )
        logger.info(
            "Geocoding successful city=%s latitude=%s longitude=%s",
            coordinates.city,
            coordinates.latitude,
            coordinates.longitude,
        )
        return coordinates
