
from datetime import date

from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from database.models.alert import Alert


def get_alerts(
    session: Session,
    city: str | None = None,
    alert_date: date | None = None,
) -> list[Alert]:
    repository = AirQualityRepository(session)

    return repository.get_alerts(
        city=city,
        alert_date=alert_date,
    )
