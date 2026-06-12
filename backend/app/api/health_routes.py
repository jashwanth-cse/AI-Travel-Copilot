"""Health check API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.schemas.response_schema import HealthResponse
from app.utils.config import get_env_value
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
    groq_status = "configured" if get_env_value("GROQ_API_KEY") else "missing"
    health_data = {
        "status": "healthy",
        "database": "connected",
        "groq": groq_status,
        "cache": "enabled",
        "version": "1.0.0",
    }
    return HealthResponse(
        **health_data,
        success=True,
        message="Health check passed",
        data=health_data,
    )
