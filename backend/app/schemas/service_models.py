"""Typed service response models.

These Pydantic models define the boundary between raw external API responses
and the rest of the backend. Keeping that boundary typed makes ETL and later
recommendation/API layers easier to reason about.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Latitude and longitude returned by the geocoding provider."""

    city: str
    latitude: float
    longitude: float
    country: str | None = None
    formatted_address: str | None = None


class AttractionData(BaseModel):
    """Normalized attraction payload used before database persistence."""

    place_id: str
    name: str
    rating: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = None
    city: str | None = None
    description: str | None = None


class RestaurantData(BaseModel):
    """Normalized restaurant payload used before database persistence."""

    place_id: str
    name: str
    rating: float | None = None
    vegetarian: bool = False
    price_level: int | None = None
    latitude: float | None = None
    longitude: float | None = None


class WeatherForecast(BaseModel):
    """Daily weather forecast value used before database persistence."""

    city: str
    date: date
    temperature: float | None = None
    condition: str | None = None


class EtlResult(BaseModel):
    """Summary returned after an ETL run completes."""

    city: str
    attractions_loaded: int = Field(default=0, ge=0)
    restaurants_loaded: int = Field(default=0, ge=0)
    weather_loaded: int = Field(default=0, ge=0)
    success: bool = True
    message: str = "ETL completed"


class TripRequestData(BaseModel):
    """User trip inputs used by recommendation and AI services."""

    destination: str
    days: int = Field(gt=0)
    budget: int = Field(ge=0)
    travelers: int = Field(gt=0)
    food_preference: str
    senior_citizen: bool = False


class ScoredAttraction(BaseModel):
    """Attraction recommendation with score details for explainability."""

    place_id: str
    name: str
    score: float
    rating: float | None = None
    category: str | None = None
    city: str | None = None
    description: str | None = None
    reasons: list[str] = Field(default_factory=list)


class ScoredRestaurant(BaseModel):
    """Restaurant recommendation with score details for explainability."""

    place_id: str
    name: str
    score: float
    rating: float | None = None
    vegetarian: bool = False
    price_level: int | None = None
    reasons: list[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    """Ranked recommendation result for a trip request."""

    trip: TripRequestData
    attractions: list[ScoredAttraction] = Field(default_factory=list)
    restaurants: list[ScoredRestaurant] = Field(default_factory=list)
    weather: list[WeatherForecast] = Field(default_factory=list)
    success: bool = True
    message: str = "Recommendations generated"


class PromptBundle(BaseModel):
    """Reusable prompt payload passed to an AI chat-completions provider."""

    system_prompt: str
    user_prompt: str


class AiItineraryResult(BaseModel):
    """Result returned by itinerary generation."""

    trip_id: int | None = None
    itinerary_id: int | None = None
    generated_plan: str | None = None
    success: bool = True
    message: str = "Itinerary generated"
