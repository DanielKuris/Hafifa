from datetime import date

from data.repository import AirQualityRepository
from database.models.alert import Alert


class AlertService:
    def __init__(self, repository: AirQualityRepository) -> None:
        self.repository = repository

    def get_alerts(
        self,
        city: str | None = None,
        alert_date: date | None = None,
    ) -> list[Alert]:
        return self.repository.get_alerts(
            city=city,
            alert_date=alert_date,
        )
