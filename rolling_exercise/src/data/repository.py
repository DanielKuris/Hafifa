from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.air_quality import AirQuality
from models.alert import Alert


class AirQualityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_measurements(
        self,
        measurements: Sequence[AirQuality],
    ) -> None:
        self.session.add_all(measurements)

    def add_alerts(
        self,
        alerts: Sequence[Alert],
    ) -> None:
        self.session.add_all(alerts)

    def get_measurements(
        self,
        city: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[AirQuality]:
        statement = select(AirQuality)

        if city is not None:
            statement = statement.where(AirQuality.city == city)

        if start_date is not None:
            statement = statement.where(AirQuality.date >= start_date)

        if end_date is not None:
            statement = statement.where(AirQuality.date <= end_date)

        statement = statement.order_by(AirQuality.date)

        return list(self.session.scalars(statement).all())

    def get_city_aqi_history(self, city: str) -> list[AirQuality]:
        statement = (
            select(AirQuality).where(AirQuality.city == city).order_by(AirQuality.date)
        )

        return list(self.session.scalars(statement).all())

    def get_city_average_aqi(self, city: str) -> float | None:
        statement = select(func.avg(AirQuality.aqi)).where(AirQuality.city == city)
        average_aqi = self.session.scalar(statement)

        return float(average_aqi) if average_aqi is not None else None

    def get_best_cities(self, limit: int = 3) -> list[tuple[str, float]]:
        statement = (
            select(AirQuality.city, func.avg(AirQuality.aqi).label("average_aqi"))
            .group_by(AirQuality.city)
            .order_by(func.avg(AirQuality.aqi))
            .limit(limit)
        )

        results = self.session.execute(statement).all()

        return [(city, float(average_aqi)) for city, average_aqi in results]

    def get_alerts(
        self,
        city: str | None = None,
        alert_date: date | None = None,
    ) -> list[Alert]:
        statement = select(Alert)

        if city is not None:
            statement = statement.where(Alert.city == city)

        if alert_date is not None:
            statement = statement.where(Alert.date == alert_date)

        statement = statement.order_by(Alert.date)

        return list(self.session.scalars(statement).all())

    def add_measurement(self, measurement: AirQuality) -> None:
        self.session.add(measurement)

    def add_alert(self, alert: Alert) -> None:
        self.session.add(alert)
