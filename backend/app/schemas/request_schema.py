"""Pydantic request schemas for FastAPI routes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.service_models import TripRequestData


class TripGenerateRequest(BaseModel):
    """Request body for itinerary generation."""

    destination: str = Field(..., min_length=1, max_length=120)
    days: int = Field(..., gt=0, le=30)
    budget: int = Field(..., ge=0)
    travelers: int = Field(..., gt=0, le=50)
    food_preference: str = Field(..., min_length=1, max_length=50)
    senior_citizen: bool = False

    def to_service_model(self) -> TripRequestData:
        """Convert API request shape into the service-layer trip model."""

        return TripRequestData(
            destination=self.destination.strip(),
            days=self.days,
            budget=self.budget,
            travelers=self.travelers,
            food_preference=self.food_preference.strip(),
            senior_citizen=self.senior_citizen,
        )


class ChatRequest(BaseModel):
    """Request body for the AI travel assistant endpoint."""

    message: str = Field(..., min_length=1, max_length=2_000)
