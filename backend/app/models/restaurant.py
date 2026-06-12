"""Restaurant ORM model."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Restaurant(Base):
    """Stores normalized restaurant records for recommendation filtering."""

    __tablename__ = "restaurants"
    __table_args__ = (
        UniqueConstraint("place_id", name="uq_restaurants_place_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    place_id: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    vegetarian: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

