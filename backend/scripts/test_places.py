"""Standalone places service check.

Run from the backend directory with:
    python scripts/test_places.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.geocoding_service import GeocodingService  # noqa: E402
from app.services.places_service import PlacesService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Geocode Ooty, then fetch nearby attractions and restaurants."""

    city = "Ooty"
    geocoding_service = GeocodingService()
    places_service = PlacesService()
    coordinates = geocoding_service.geocode_city(city)
    if coordinates is None:
        logger.warning("Places script stopped because geocoding failed city=%s", city)
        print("No coordinates returned. Check GEOAPIFY_API_KEY in backend/.env.")
        return

    attractions = places_service.fetch_attractions(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
        city=city,
        limit=10,
    )
    restaurants = places_service.fetch_restaurants(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
        limit=10,
    )

    print(
        {
            "city": city,
            "attractions_count": len(attractions),
            "restaurants_count": len(restaurants),
            "sample_attractions": [item.model_dump() for item in attractions[:3]],
            "sample_restaurants": [item.model_dump() for item in restaurants[:3]],
        }
    )


if __name__ == "__main__":
    main()
