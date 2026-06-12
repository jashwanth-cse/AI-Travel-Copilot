"""Trip request ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.itinerary import Itinerary


class Trip(Base):
    """Stores a user's travel planning request."""

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    destination: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[int] = mapped_column(Integer, nullable=False)
    travelers: Mapped[int] = mapped_column(Integer, nullable=False)
    food_preference: Mapped[str] = mapped_column(String(50), nullable=False)
    senior_citizen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Server-generated timestamp provides a consistent creation audit trail.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    itineraries: Mapped[list[Itinerary]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )

