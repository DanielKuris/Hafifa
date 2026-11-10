from datetime import date

import pandas as pd
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from database.models.air_quality import AirQuality
from database.models.alert import Alert


class AirQualityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert_measurements(self, dataframe: pd.DataFrame) -> list[int]:
        records = dataframe.to_dict(orient="records")

        statement = insert(AirQuality).returning(
            AirQuality.id,
            sort_by_parameter_order=True,
        )

        return list(self.session.scalars(statement, records).all())

    def insert_alerts(self, dataframe: pd.DataFrame) -> None:
        if dataframe.empty:
            return

        records = dataframe.to_dict(orient="records")

        statement = insert(Alert)

        self.session.execute(statement, records)

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

    def get_city_average_aqi(self, city: str) -> float | None:
        statement = select(func.avg(AirQuality.aqi)).where(AirQuality.city == city)

        average_aqi = self.session.scalar(statement)

        return float(average_aqi) if average_aqi is not None else None

    def get_best_cities(self, limit: int = 3) -> list[tuple[str, float]]:
        average_aqi = func.avg(AirQuality.aqi).label("average_aqi")

        statement = (
            select(AirQuality.city, average_aqi)
            .group_by(AirQuality.city)
            .order_by(average_aqi, AirQuality.city)
            .limit(limit)
        )

        results = self.session.execute(statement).all()

        return [(city, float(average)) for city, average in results]

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
