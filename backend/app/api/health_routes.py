"""Health check API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.schemas.response_schema import HealthResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API and database health",
)
def health_check(db_session: Session = Depends(get_db_session)) -> HealthResponse:
    """Return API status after verifying a lightweight SQLite query."""

    logger.info("Health check requested")
    try:
        db_session.execute(text("SELECT 1"))
    except Exception as error:
        logger.error("Health check database probe failed error=%s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    logger.debug("Health check database probe passed")
    return HealthResponse(status="ok", database="ok")
