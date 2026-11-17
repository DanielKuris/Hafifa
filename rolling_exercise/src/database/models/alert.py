from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("air_quality.id"),
        nullable=False,
    )

    measurement: Mapped[AirQuality] = relationship(back_populates="alert")
