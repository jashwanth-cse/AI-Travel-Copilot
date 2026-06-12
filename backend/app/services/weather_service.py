"""OpenWeather forecast service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.schemas.service_models import WeatherForecast
from app.utils.config import get_env_value
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherService:
    """Fetch 5-day weather forecasts from OpenWeather."""

    BASE_URL: str = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        """Create the service with a configurable network timeout."""

        self.timeout_seconds = timeout_seconds
        self.api_key = get_env_value("OPENWEATHER_API_KEY")

    def fetch_forecast(self, city: str, max_days: int = 5) -> list[WeatherForecast]:
        """Fetch one daily forecast value per day for the requested city."""

        normalized_city: str = city.strip()
        if not normalized_city:
            logger.warning("Cannot fetch weather for empty city")
            return []

        if not self.api_key:
            logger.error("OpenWeather API key is not configured")
            return []

        params: dict[str, str] = {
            "q": normalized_city,
            "appid": self.api_key,
            "units": "metric",
        }
        logger.info("Fetching weather forecast city=%s max_days=%s", normalized_city, max_days)

        try:
            response = httpx.get(self.BASE_URL, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            logger.debug("Raw weather response=%s", payload)
        except httpx.HTTPStatusError as error:
            logger.error(
                "OpenWeather HTTP error city=%s status_code=%s error=%s",
                normalized_city,
                error.response.status_code,
                error,
            )
            return []
        except httpx.HTTPError as error:
            logger.error("OpenWeather request failed city=%s error=%s", normalized_city, error)
            return []
        except ValueError as error:
            logger.error("OpenWeather returned invalid JSON city=%s error=%s", normalized_city, error)
            return []

        forecasts = self._daily_forecasts(payload=payload, city=normalized_city, max_days=max_days)
        logger.info("Fetched weather forecast city=%s count=%s", normalized_city, len(forecasts))
        return forecasts

    def _daily_forecasts(
        self,
        *,
        payload: dict[str, Any],
        city: str,
        max_days: int,
    ) -> list[WeatherForecast]:
        """Collapse OpenWeather 3-hour records into one forecast per day."""

        by_date: dict[str, WeatherForecast] = {}
        for item in payload.get("list", []):
            date_text = item.get("dt_txt")
            if not date_text:
                logger.warning("Skipping weather item without dt_txt item=%s", item)
                continue

            try:
                forecast_datetime = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                logger.warning("Skipping weather item with invalid dt_txt value=%s", date_text)
                continue
            forecast_date = forecast_datetime.date()
            date_key = forecast_date.isoformat()

            # Prefer a midday-ish forecast when possible. Otherwise keep the
            # first value encountered for the day.
            if date_key in by_date and forecast_datetime.hour != 12:
                continue

            weather_items: list[dict[str, Any]] = item.get("weather", [])
            condition = weather_items[0].get("description") if weather_items else None
            by_date[date_key] = WeatherForecast(
                city=city,
                date=forecast_date,
                temperature=self._extract_temperature(item),
                condition=condition,
            )

            if len(by_date) >= max_days and forecast_datetime.hour == 12:
                break

        return list(by_date.values())[:max_days]

    def _extract_temperature(self, item: dict[str, Any]) -> float | None:
        """Extract temperature as Celsius from an OpenWeather list item."""

        raw_temperature = item.get("main", {}).get("temp")
        try:
            return float(raw_temperature) if raw_temperature is not None else None
        except (TypeError, ValueError):
            logger.warning("Invalid weather temperature value=%s", raw_temperature)
            return None
