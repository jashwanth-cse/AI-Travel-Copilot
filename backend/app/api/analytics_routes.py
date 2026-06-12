"""Analytics API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.schemas.response_schema import StandardApiResponse
from app.services.analytics_service import AnalyticsService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get(
    "/{city}",
    response_model=StandardApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached travel-data analytics for a city",
)
def get_city_analytics(
    city: str,
    db_session: Session = Depends(get_db_session),
) -> StandardApiResponse:
    """Return aggregate analytics for the requested city."""

    logger.info("Analytics requested city=%s", city)
    analytics = AnalyticsService().get_city_analytics(city, db_session=db_session)
    return StandardApiResponse(
        success=True,
        message="Analytics fetched successfully",
        data=analytics,
    )
