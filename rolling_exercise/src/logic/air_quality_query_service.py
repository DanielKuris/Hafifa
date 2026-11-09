from datetime import date

from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from logic.exceptions import MeasurementNotFoundError
from models.air_quality import AirQuality


def get_measurements(
    session: Session,
    city: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[AirQuality]:
    repository = AirQualityRepository(session)

    return repository.get_measurements(city, start_date, end_date)


def get_city_aqi_history(
    session: Session,
    city: str,
) -> list[AirQuality]:
    repository = AirQualityRepository(session)

    return repository.get_city_aqi_history(city)


def get_city_average_aqi(
    session: Session,
    city: str,
) -> dict[str, str | float]:
    repository = AirQualityRepository(session)

    average_aqi = repository.get_city_average_aqi(city)

    if average_aqi is None:
        raise MeasurementNotFoundError(f"No measurements found for city '{city}'.")

    return {
        "city": city,
        "average_aqi": average_aqi,
    }


def get_best_cities(
    session: Session,
) -> list[dict[str, str | float]]:
    repository = AirQualityRepository(session)

    results = repository.get_best_cities()

    return [
        {
            "city": city,
            "average_aqi": average_aqi,
        }
        for city, average_aqi in results
    ]
