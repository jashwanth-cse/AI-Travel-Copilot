"""Standalone weather service check.

Run from the backend directory with:
    python scripts/test_weather.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.weather_service import WeatherService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Fetch and print a 5-day forecast for the sample destination."""

    city = "Ooty"
    service = WeatherService()
    forecasts = service.fetch_forecast(city)
    if not forecasts:
        logger.warning("Weather script completed without forecasts city=%s", city)
        print("No forecasts returned. Check OPENWEATHER_API_KEY in backend/.env.")
        return

    print([forecast.model_dump() for forecast in forecasts])


if __name__ == "__main__":
    main()
