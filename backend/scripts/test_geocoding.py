"""Standalone geocoding service check.

Run from the backend directory with:
    python scripts/test_geocoding.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.geocoding_service import GeocodingService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Fetch and print coordinates for the sample destination."""

    city = "Ooty"
    service = GeocodingService()
    coordinates = service.geocode_city(city)
    if coordinates is None:
        logger.warning("Geocoding script completed without coordinates city=%s", city)
        print("No coordinates returned. Check GEOAPIFY_API_KEY in backend/.env.")
        return

    print(coordinates.model_dump())


if __name__ == "__main__":
    main()
