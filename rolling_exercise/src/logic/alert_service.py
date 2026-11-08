from datetime import date

from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from models.alert import Alert


def get_alerts(session: Session) -> list[Alert]:
    repository = AirQualityRepository(session)

    return repository.get_alerts()


def get_alerts_by_city(
    session: Session,
    city: str,
) -> list[Alert]:
    repository = AirQualityRepository(session)

    return repository.get_alerts(city=city)


def get_alerts_by_date(
    session: Session,
    alert_date: date,
) -> list[Alert]:
    repository = AirQualityRepository(session)

    return repository.get_alerts(alert_date=alert_date)
