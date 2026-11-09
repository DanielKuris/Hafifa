
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from logic.exceptions import MeasurementNotFoundError
from logic.air_quality_query_service import (
    get_best_cities,
    get_city_aqi_history,
    get_city_average_aqi,
    get_measurements,
)
from models.air_quality import AirQuality


def create_measurement(
    measured_date: date,
    city: str,
    aqi: float,
) -> AirQuality:
    return AirQuality(
        date=measured_date,
        city=city,
        pm25=10.0,
        no2=20.0,
        co2=30.0,
        aqi=aqi,
        aqi_level="Good",
    )


def test_get_measurements_returns_multiple_measurements() -> None:
    session = MagicMock(spec=Session)
    measurements = [
        create_measurement(date(2026, 1, 1), "London", 40),
        create_measurement(date(2026, 1, 2), "London", 50),
    ]

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_measurements.return_value = measurements

        result = get_measurements(
            session,
            city="London",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
        )

    assert result == measurements
    repository_class.assert_called_once_with(session)
    repository_class.return_value.get_measurements.assert_called_once_with(
        "London",
        date(2026, 1, 1),
        date(2026, 1, 2),
    )


def test_get_measurements_returns_empty_list() -> None:
    session = MagicMock(spec=Session)

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_measurements.return_value = []

        result = get_measurements(session)

    assert result == []
    repository_class.return_value.get_measurements.assert_called_once_with(
        None,
        None,
        None,
    )


def test_get_city_aqi_history_returns_multiple_measurements() -> None:
    session = MagicMock(spec=Session)
    measurements = [
        create_measurement(date(2026, 1, 1), "London", 40),
        create_measurement(date(2026, 1, 2), "London", 50),
    ]

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_city_aqi_history.return_value = measurements

        result = get_city_aqi_history(session, "London")

    assert result == measurements
    repository_class.return_value.get_city_aqi_history.assert_called_once_with(
        "London"
    )


def test_get_city_aqi_history_returns_empty_list() -> None:
    session = MagicMock(spec=Session)

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_city_aqi_history.return_value = []

        result = get_city_aqi_history(session, "London")

    assert result == []


def test_get_city_average_aqi_returns_average() -> None:
    session = MagicMock(spec=Session)

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_city_average_aqi.return_value = 45.0

        result = get_city_average_aqi(session, "London")

    assert result == {
        "city": "London",
        "average_aqi": 45.0,
    }
    repository_class.return_value.get_city_average_aqi.assert_called_once_with(
        "London"
    )


def test_get_city_average_aqi_raises_when_city_has_no_measurements() -> None:
    session = MagicMock(spec=Session)

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_city_average_aqi.return_value = None

        with pytest.raises(MeasurementNotFoundError):
            get_city_average_aqi(session, "London")


def test_get_best_cities_returns_multiple_cities() -> None:
    session = MagicMock(spec=Session)
    repository_results = [
        ("London", 35.0),
        ("Paris", 42.0),
        ("Berlin", 48.0),
    ]

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_best_cities.return_value = repository_results

        result = get_best_cities(session)

    assert result == [
        {"city": "London", "average_aqi": 35.0},
        {"city": "Paris", "average_aqi": 42.0},
        {"city": "Berlin", "average_aqi": 48.0},
    ]


def test_get_best_cities_returns_empty_list() -> None:
    session = MagicMock(spec=Session)

    with patch("logic.query_service.AirQualityRepository") as repository_class:
        repository_class.return_value.get_best_cities.return_value = []

        result = get_best_cities(session)

    assert result == []
