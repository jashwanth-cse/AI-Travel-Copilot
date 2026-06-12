"""Trip generation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.schemas.request_schema import TripGenerateRequest
from app.schemas.response_schema import TripGenerateResponse
from app.services.ai_service import AiService
from app.services.etl_service import EtlService
from app.services.recommendation_service import RecommendationService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post(
    "/generate",
    response_model=TripGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a recommended AI itinerary",
)
def generate_trip(
    request: TripGenerateRequest,
    db_session: Session = Depends(get_db_session),
) -> TripGenerateResponse:
    """Generate recommendations and an AI itinerary for a trip request."""

    trip = request.to_service_model()
    logger.info("Trip generation requested destination=%s days=%s", trip.destination, trip.days)

    # ETL is best-effort at API time: if external travel APIs fail, we still try
    # to use whatever cleaned data is already in SQLite. The service logs the
    # exact provider failure and keeps route code free of ETL rules.
    etl_result = EtlService().run_for_city(trip.destination)
    if not etl_result.success:
        logger.warning("ETL did not refresh data destination=%s message=%s", trip.destination, etl_result.message)

    recommendation_result = RecommendationService().recommend(trip, db_session=db_session)
    if not recommendation_result.success:
        logger.error("Recommendation failed destination=%s message=%s", trip.destination, recommendation_result.message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=recommendation_result.message,
        )

    ai_result = AiService().generate_itinerary(trip, db_session=db_session)
    if not ai_result.success:
        logger.error("AI itinerary generation failed destination=%s message=%s", trip.destination, ai_result.message)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ai_result.message,
        )

    return TripGenerateResponse(
        trip_id=ai_result.trip_id,
        itinerary_id=ai_result.itinerary_id,
        destination=trip.destination,
        attractions=recommendation_result.attractions,
        restaurants=recommendation_result.restaurants,
        weather=recommendation_result.weather,
        itinerary=ai_result.generated_plan,
        message=ai_result.message,
    )
