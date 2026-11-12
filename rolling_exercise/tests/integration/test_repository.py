from datetime import date

import allure
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from config.settings import settings
from data.repository import AirQualityRepository


@pytest.fixture
@allure.title("Create air quality repository")
def repository(db_session: Session) -> AirQualityRepository:
    return AirQualityRepository(db_session)


@pytest.fixture
@allure.title("Prepare measurement data")
def measurement_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date(2025, 1, 3),
                "city": "Amsterdam",
                "pm25": 10.0,
                "no2": 10.0,
                "co2": 10.0,
                "aqi": 10,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 3),
                "city": "Amsterdam",
                "pm25": 20.0,
                "no2": 20.0,
                "co2": 20.0,
                "aqi": 20,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 1),
                "city": "Berlin",
                "pm25": 30.0,
                "no2": 30.0,
                "co2": 30.0,
                "aqi": 30,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 2),
                "city": "Amsterdam",
                "pm25": 40.0,
                "no2": 40.0,
                "co2": 40.0,
                "aqi": 40,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 4),
                "city": "Cairo",
                "pm25": 50.0,
                "no2": 50.0,
                "co2": 50.0,
                "aqi": 50,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 5),
                "city": "Delhi",
                "pm25": 60.0,
                "no2": 60.0,
                "co2": 60.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 10,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 5),
                "city": "Delhi",
                "pm25": 70.0,
                "no2": 70.0,
                "co2": 70.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 20,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 6),
                "city": "Cairo",
                "pm25": 80.0,
                "no2": 80.0,
                "co2": 80.0,
                "aqi": 80,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 7),
                "city": "Mumbai",
                "pm25": 90.0,
                "no2": 90.0,
                "co2": 90.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 30,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 7),
                "city": "Mumbai",
                "pm25": 100.0,
                "no2": 100.0,
                "co2": 100.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 40,
                "aqi_level": "Hazardous",
            },
        ]
    )


def _create_alert_dataframe(
    measurement_dataframe: pd.DataFrame,
    measurement_ids: list[int],
) -> pd.DataFrame:
    records = [
        {
            "date": record["date"],
            "city": record["city"],
            "aqi": record["aqi"],
            "measurement_id": measurement_id,
        }
        for record, measurement_id in zip(
            measurement_dataframe.to_dict(orient="records"),
            measurement_ids,
            strict=True,
        )
        if record["aqi"] > settings.AQI_ALERT_THRESHOLD
    ]

    return pd.DataFrame(records)


@pytest.fixture
@allure.title("Populate repository with measurements")
def populated_repository(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> AirQualityRepository:
    repository.insert_measurements(measurement_dataframe)

    return repository


@pytest.fixture
@allure.title("Populate repository with measurements and alerts")
def populated_repository_with_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> AirQualityRepository:
    measurement_ids = repository.insert_measurements(measurement_dataframe)
    alert_dataframe = _create_alert_dataframe(
        measurement_dataframe,
        measurement_ids,
    )
    repository.insert_alerts(alert_dataframe)

    return repository


@allure.feature("Air Quality Repository")
@allure.story("Insert Measurements")
@allure.title("Insert measurements into the database")
def test_insert_measurements(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurement_ids = repository.insert_measurements(measurement_dataframe)
    measurements = repository.get_measurements()

    assert len(measurement_ids) == len(measurement_dataframe)
    assert len(measurements) == len(measurement_dataframe)
    assert set(measurement_ids) == {measurement.id for measurement in measurements}


@allure.feature("Air Quality Repository")
@allure.story("Insert Alerts")
@allure.title("Insert alerts linked to their measurements")
def test_insert_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurement_ids = repository.insert_measurements(measurement_dataframe)
    alert_dataframe = _create_alert_dataframe(
        measurement_dataframe,
        measurement_ids,
    )

    repository.insert_alerts(alert_dataframe)
    alerts = repository.get_alerts()

    assert len(alerts) == len(alert_dataframe)
    assert {alert.measurement.id for alert in alerts} == {
        record["measurement_id"] for record in alert_dataframe.to_dict(orient="records")
    }


@allure.feature("Air Quality Repository")
@allure.story("Retrieve Measurements")
@allure.title("Retrieve all measurements ordered by date")
def test_get_measurements(
    populated_repository: AirQualityRepository,
) -> None:
    measurements = populated_repository.get_measurements()

    assert len(measurements) == 10
    assert [measurement.date for measurement in measurements] == sorted(
        measurement.date for measurement in measurements
    )


@allure.feature("Air Quality Repository")
@allure.story("Retrieve Measurements")
@allure.title("Retrieve measurements using city and date filters")
def test_get_measurements_with_filters(
    populated_repository: AirQualityRepository,
) -> None:
    measurements = populated_repository.get_measurements(
        city="Amsterdam",
        start_date=date(2025, 1, 2),
        end_date=date(2025, 1, 3),
    )

    assert len(measurements) == 3
    assert {measurement.city for measurement in measurements} == {"Amsterdam"}
    assert [measurement.date for measurement in measurements] == [
        date(2025, 1, 2),
        date(2025, 1, 3),
        date(2025, 1, 3),
    ]


@allure.feature("Air Quality Repository")
@allure.story("Calculate City Average")
@allure.title("Calculate the average AQI for a city")
def test_get_city_average_aqi(
    populated_repository: AirQualityRepository,
) -> None:
    average_aqi = populated_repository.get_city_average_aqi("Amsterdam")

    assert average_aqi == pytest.approx(70 / 3)


@allure.feature("Air Quality Repository")
@allure.story("Calculate City Average")
@allure.title("Return None when a city has no measurements")
def test_get_city_average_aqi_without_measurements(
    repository: AirQualityRepository,
) -> None:
    average_aqi = repository.get_city_average_aqi("Amsterdam")

    assert average_aqi is None


@allure.feature("Air Quality Repository")
@allure.story("Rank Cities")
@allure.title("Retrieve cities ranked by average AQI")
def test_get_best_cities(
    populated_repository: AirQualityRepository,
) -> None:
    best_cities = populated_repository.get_best_cities(limit=3)

    assert [city for city, _ in best_cities] == [
        "Amsterdam",
        "Berlin",
        "Cairo",
    ]
    assert [average for _, average in best_cities] == pytest.approx([70 / 3, 30, 65])


@allure.feature("Air Quality Repository")
@allure.story("Rank Cities")
@allure.title("Return an empty list when no cities have measurements")
def test_get_best_cities_without_measurements(
    repository: AirQualityRepository,
) -> None:
    best_cities = repository.get_best_cities()

    assert best_cities == []


@allure.feature("Air Quality Repository")
@allure.story("Retrieve Alerts")
@allure.title("Retrieve all alerts ordered by date")
def test_get_alerts(
    populated_repository_with_alerts: AirQualityRepository,
) -> None:
    alerts = populated_repository_with_alerts.get_alerts()

    assert len(alerts) == 4
    assert [alert.date for alert in alerts] == [
        date(2025, 1, 5),
        date(2025, 1, 5),
        date(2025, 1, 7),
        date(2025, 1, 7),
    ]
    assert {alert.city for alert in alerts} == {"Delhi", "Mumbai"}


@allure.feature("Air Quality Repository")
@allure.story("Retrieve Alerts")
@allure.title("Retrieve alerts using city and date filters")
def test_get_alerts_with_filters(
    populated_repository_with_alerts: AirQualityRepository,
) -> None:
    alerts = populated_repository_with_alerts.get_alerts(
        city="Mumbai",
        alert_date=date(2025, 1, 7),
    )

    assert len(alerts) == 2
    assert {alert.city for alert in alerts} == {"Mumbai"}
    assert {alert.date for alert in alerts} == {date(2025, 1, 7)}
