"""Pydantic response schemas for FastAPI routes."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.service_models import ScoredAttraction, ScoredRestaurant, WeatherForecast


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str


class ErrorResponse(BaseModel):
    """Standard API error payload."""

    detail: str


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
