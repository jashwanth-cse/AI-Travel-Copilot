"""Standalone AI itinerary service check.

Run from the backend directory with:
    python scripts/test_ai.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.service_models import TripRequestData  # noqa: E402
from app.services.ai_service import AiService  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402
from scripts.test_recommendation import seed_demo_data  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Generate and store an AI itinerary when GROQ_API_KEY is configured."""

    seed_demo_data()
    trip = TripRequestData(
        destination="Ooty",
        days=3,
        budget=15000,
        travelers=2,
        food_preference="vegetarian",
        senior_citizen=True,
    )
    service = AiService()

    # Prompt preview makes the script useful even without a Groq key: developers
    # can inspect the modular prompt composition before enabling live calls.
    prompt_preview = service.build_prompt_preview(trip)
    if prompt_preview is not None:
        print(
            {
                "prompt_preview": {
                    "system_prompt": prompt_preview.system_prompt,
                    "user_prompt_start": prompt_preview.user_prompt[:800],
                }
            }
        )

    result = service.generate_itinerary(trip)
    print(result.model_dump())
    if not result.success:
        logger.warning("AI script completed without generated itinerary message=%s", result.message)
        print("No itinerary stored. Check GROQ_API_KEY in backend/.env.")


if __name__ == "__main__":
    main()
