from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

if TYPE_CHECKING:
    from database.models.alert import Alert


class AirQuality(Base):
    __tablename__ = "air_quality"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    pm25: Mapped[float] = mapped_column(Float, nullable=False)
    no2: Mapped[float] = mapped_column(Float, nullable=False)
    co2: Mapped[float] = mapped_column(Float, nullable=False)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)
    aqi_level: Mapped[str] = mapped_column(String, nullable=False)

    alert: Mapped[Alert | None] = relationship(
        back_populates="measurement",
        uselist=False,
    )
