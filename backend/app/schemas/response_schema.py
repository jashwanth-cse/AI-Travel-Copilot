"""Pydantic response schemas for FastAPI routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.service_models import ScoredAttraction, ScoredRestaurant, WeatherForecast


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    groq: str = "unknown"
    cache: str = "enabled"
    version: str = "1.0.0"
    success: bool = True
    message: str = "Health check passed"
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard API error payload."""

    success: bool = False
    message: str
    error: str


class StandardApiResponse(BaseModel):
    """Standard successful API response envelope."""

    success: bool = True
    message: str
    data: dict[str, Any] | list[Any] | None = None
    error: str | None = None


class TripGenerateResponse(BaseModel):
    """Response returned after trip recommendation and itinerary generation."""

    trip_id: int | None = None
    itinerary_id: int | None = None
    destination: str
    attractions: list[ScoredAttraction] = Field(default_factory=list)
    restaurants: list[ScoredRestaurant] = Field(default_factory=list)
    weather: list[WeatherForecast] = Field(default_factory=list)
    itinerary: str | None = None
    message: str


class ChatResponse(BaseModel):
    """AI travel assistant response."""

    answer: str


class ValidationErrorItem(BaseModel):
    """Compact validation error item for overridden validation responses."""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    detail: str
    errors: list[ValidationErrorItem]


class DbRecordCountResponse(BaseModel):
    """Small diagnostic schema for route internals and future checks."""

    table: str
    count: int
    checked_at: date | None = None
