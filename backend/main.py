"""FastAPI application entrypoint for the AI Travel Copilot backend."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.ai_routes import router as ai_router
from app.api.health_routes import router as health_router
from app.api.trip_routes import router as trip_router
from app.db.init_db import init_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize application resources at startup.

    Table creation is idempotent, so startup can safely ensure SQLite is ready
    before the first request reaches the route layer.
    """

    logger.info("Starting AI Travel Copilot API app_name=%s", app.title)
    init_db()
    yield
    logger.info("Stopping AI Travel Copilot API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="AI Travel Copilot API",
        description="Backend API for travel ETL, recommendations, and AI itinerary generation.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS is enabled for local frontend development now and can be tightened
    # with specific origins when deployment targets are known.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(trip_router)
    app.include_router(ai_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Log and return intentional HTTP errors."""

        logger.warning(
            "HTTP error path=%s status_code=%s detail=%s",
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Return compact request validation errors with a 422 status code."""

        logger.warning("Validation error path=%s errors=%s", request.url.path, exc.errors())
        errors = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])),
                "message": str(error.get("msg", "Invalid value")),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Request validation failed", "errors": errors},
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Return a stable error response for database failures."""

        logger.error("Database error path=%s error=%s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Database operation failed"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch unexpected errors so clients receive a JSON response."""

        logger.error("Unhandled error path=%s error=%s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app: FastAPI = create_app()
