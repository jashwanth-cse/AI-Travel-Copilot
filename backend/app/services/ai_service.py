"""Groq-powered itinerary generation service."""

from __future__ import annotations

import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.models.itinerary import Itinerary
from app.models.trip import Trip
from app.schemas.service_models import (
    AiItineraryResult,
    PromptBundle,
    RecommendationResult,
    ScoredAttraction,
    ScoredRestaurant,
    TripRequestData,
    WeatherForecast,
)
from app.services.recommendation_service import RecommendationService
from app.utils.config import get_env_value
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ItineraryPromptBuilder:
    """Build reusable prompts for itinerary generation."""

    def build(self, recommendations: RecommendationResult) -> PromptBundle:
        """Create system and user prompts from recommendation data."""

        trip = recommendations.trip
        system_prompt = (
            "You are an expert India travel planner. Create practical, safe, "
            "day-wise itineraries using only the provided destination data. "
            "Respect budget, food preference, traveler count, senior-citizen "
            "constraints, and weather. Keep the tone concise and helpful."
        )

        user_prompt = "\n".join(
            [
                self._trip_section(trip),
                self._attraction_section(recommendations.attractions),
                self._restaurant_section(recommendations.restaurants),
                self._weather_section(recommendations.weather),
                "Output format:",
                "- Day-wise plan with morning, afternoon, evening.",
                "- Mention suitable restaurants where useful.",
                "- Mention weather-aware cautions.",
                "- Avoid attractions that conflict with senior-citizen mode.",
            ]
        )
        logger.debug("Built itinerary prompt trip=%s prompt_length=%s", trip.model_dump(), len(user_prompt))
        return PromptBundle(system_prompt=system_prompt, user_prompt=user_prompt)

    def _trip_section(self, trip: TripRequestData) -> str:
        """Render trip request details for the prompt."""

        return (
            "Trip request:\n"
            f"- Destination: {trip.destination}\n"
            f"- Days: {trip.days}\n"
            f"- Budget: {trip.budget}\n"
            f"- Travelers: {trip.travelers}\n"
            f"- Food preference: {trip.food_preference}\n"
            f"- Senior citizen mode: {trip.senior_citizen}"
        )

    def _attraction_section(self, attractions: list[ScoredAttraction]) -> str:
        """Render ranked attractions for the prompt."""

        if not attractions:
            return "Recommended attractions: none available"

        lines = ["Recommended attractions:"]
        for attraction in attractions:
            lines.append(
                "- "
                f"{attraction.name} | category={attraction.category} | "
                f"rating={attraction.rating} | score={attraction.score} | "
                f"notes={attraction.description}"
            )
        return "\n".join(lines)

    def _restaurant_section(self, restaurants: list[ScoredRestaurant]) -> str:
        """Render ranked restaurants for the prompt."""

        if not restaurants:
            return "Recommended restaurants: none available"

        lines = ["Recommended restaurants:"]
        for restaurant in restaurants:
            lines.append(
                "- "
                f"{restaurant.name} | vegetarian={restaurant.vegetarian} | "
                f"price_level={restaurant.price_level} | "
                f"rating={restaurant.rating} | score={restaurant.score}"
            )
        return "\n".join(lines)

    def _weather_section(self, forecasts: list[WeatherForecast]) -> str:
        """Render weather forecasts for the prompt."""

        if not forecasts:
            return "Weather forecast: none available"

        lines = ["Weather forecast:"]
        for forecast in forecasts:
            lines.append(
                "- "
                f"{forecast.date.isoformat()} | temp_c={forecast.temperature} | "
                f"condition={forecast.condition}"
            )
        return "\n".join(lines)


class AiService:
    """Generate and store AI itineraries through Groq chat completions."""

    GROQ_CHAT_COMPLETIONS_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"

    def __init__(
        self,
        recommendation_service: RecommendationService | None = None,
        prompt_builder: ItineraryPromptBuilder | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        """Create the AI service with injectable collaborators."""

        self.recommendation_service = recommendation_service or RecommendationService()
        self.prompt_builder = prompt_builder or ItineraryPromptBuilder()
        self.timeout_seconds = timeout_seconds
        self.api_key = get_env_value("GROQ_API_KEY")

    def generate_itinerary(
        self,
        trip: TripRequestData,
        *,
        db_session: Session | None = None,
    ) -> AiItineraryResult:
        """Generate a Groq itinerary, then store trip and itinerary in SQLite."""

        started_at = time.perf_counter()
        logger.info("Starting itinerary generation destination=%s days=%s", trip.destination, trip.days)
        recommendations = self.recommendation_service.recommend(trip, db_session=db_session)
        if not recommendations.success:
            logger.error("Itinerary generation stopped recommendation_message=%s", recommendations.message)
            elapsed = time.perf_counter() - started_at
            logger.info("AI generation completed in %.2f seconds", elapsed)
            return AiItineraryResult(success=False, message=recommendations.message)

        prompt = self.prompt_builder.build(recommendations)
        generated_plan = self._call_groq(prompt)
        if generated_plan is None:
            elapsed = time.perf_counter() - started_at
            logger.info("AI generation completed in %.2f seconds", elapsed)
            return AiItineraryResult(success=False, message="Groq itinerary generation failed")

        try:
            trip_id, itinerary_id = self._store_itinerary(
                trip=trip,
                generated_plan=generated_plan,
                db_session=db_session,
            )
        except Exception as error:
            logger.error("Failed to store generated itinerary error=%s", error)
            elapsed = time.perf_counter() - started_at
            logger.info("AI generation completed in %.2f seconds", elapsed)
            return AiItineraryResult(success=False, message="Failed to store itinerary")

        logger.info("Itinerary generated and stored trip_id=%s itinerary_id=%s", trip_id, itinerary_id)
        result = AiItineraryResult(
            trip_id=trip_id,
            itinerary_id=itinerary_id,
            generated_plan=generated_plan,
        )
        elapsed = time.perf_counter() - started_at
        logger.info("AI generation completed in %.2f seconds", elapsed)
        return result

    def build_prompt_preview(
        self,
        trip: TripRequestData,
        *,
        db_session: Session | None = None,
    ) -> PromptBundle | None:
        """Build a prompt without calling Groq, useful for script diagnostics."""

        recommendations = self.recommendation_service.recommend(trip, db_session=db_session)
        if not recommendations.success:
            logger.error("Prompt preview failed recommendation_message=%s", recommendations.message)
            return None
        return self.prompt_builder.build(recommendations)

    def chat(self, message: str) -> str | None:
        """Answer a general travel-assistant message through Groq.

        This method intentionally does not touch route or HTTP objects. The API
        layer only validates the request and maps None to an HTTP error.
        """

        prompt = PromptBundle(
            system_prompt=(
                "You are a concise AI travel assistant. Answer travel planning "
                "questions with practical, safety-aware guidance."
            ),
            user_prompt=message.strip(),
        )
        if not prompt.user_prompt:
            logger.warning("Cannot answer empty chat message")
            return None
        return self._call_groq(prompt)

    def _call_groq(self, prompt: PromptBundle) -> str | None:
        """Call Groq and return generated text, or None on failure."""

        if not self.api_key:
            logger.error("Groq API key is not configured")
            return None

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 1800,
        }
        logger.info("Calling Groq model=%s", self.DEFAULT_MODEL)
        logger.debug("Groq request payload=%s", {**payload, "messages": "[redacted prompt messages]"})

        try:
            response = httpx.post(
                self.GROQ_CHAT_COMPLETIONS_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            response_payload: dict[str, Any] = response.json()
            logger.debug("Groq response payload=%s", response_payload)
        except httpx.HTTPStatusError as error:
            logger.error(
                "Groq HTTP error status_code=%s error=%s",
                error.response.status_code,
                error,
            )
            return None
        except httpx.HTTPError as error:
            logger.error("Groq request failed error=%s", error)
            return None
        except ValueError as error:
            logger.error("Groq returned invalid JSON error=%s", error)
            return None

        choices = response_payload.get("choices", [])
        if not choices:
            logger.error("Groq response missing choices")
            return None

        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            logger.error("Groq response missing message content")
            return None

        logger.info("Groq itinerary generation succeeded content_length=%s", len(content))
        return content.strip()

    def _store_itinerary(
        self,
        *,
        trip: TripRequestData,
        generated_plan: str,
        db_session: Session | None = None,
    ) -> tuple[int, int]:
        """Persist the trip request and generated itinerary in one transaction."""

        init_db()
        if db_session is not None:
            db_trip = self._create_trip_row(session=db_session, trip=trip)
            db_itinerary = Itinerary(trip_id=db_trip.id, generated_plan=generated_plan)
            db_session.add(db_itinerary)
            db_session.commit()
            db_session.refresh(db_itinerary)
            logger.debug(
                "Stored itinerary with injected session trip_id=%s itinerary_id=%s",
                db_trip.id,
                db_itinerary.id,
            )
            return db_trip.id, db_itinerary.id

        with SessionLocal() as session:
            db_trip = self._create_trip_row(session=session, trip=trip)
            db_itinerary = Itinerary(trip_id=db_trip.id, generated_plan=generated_plan)
            session.add(db_itinerary)
            session.commit()
            session.refresh(db_itinerary)
            logger.debug(
                "Stored itinerary trip_id=%s itinerary_id=%s",
                db_trip.id,
                db_itinerary.id,
            )
            return db_trip.id, db_itinerary.id

    def _create_trip_row(self, *, session: Session, trip: TripRequestData) -> Trip:
        """Create and flush a Trip ORM row before itinerary insertion."""

        db_trip = Trip(
            destination=trip.destination,
            days=trip.days,
            budget=trip.budget,
            travelers=trip.travelers,
            food_preference=trip.food_preference,
            senior_citizen=trip.senior_citizen,
        )
        session.add(db_trip)
        session.flush()
        logger.debug("Stored trip row trip_id=%s", db_trip.id)
        return db_trip
