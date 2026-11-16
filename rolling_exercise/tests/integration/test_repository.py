
from datetime import date

import allure
import pandas as pd
import pytest

from config.settings import settings
from data.repository import AirQualityRepository


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
    assert {measurement.id for measurement in measurements} == set(
        measurement_ids
    )


@allure.story("Insert Alerts")
@allure.title("Insert alerts linked to their measurements")
def test_insert_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurement_ids = repository.insert_measurements(measurement_dataframe)

    alert_dataframe = pd.DataFrame(
        [
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
    )

    repository.insert_alerts(alert_dataframe)
    alerts = repository.get_alerts()

    assert len(alerts) == len(alert_dataframe)
    assert {alert.measurement.id for alert in alerts} == set(
        alert_dataframe["measurement_id"]
    )


@allure.story("Retrieve Measurements")
@allure.title("Retrieve all measurements ordered by date")
def test_get_measurements(
    populated_repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurements = populated_repository.get_measurements()

    assert len(measurements) == len(measurement_dataframe)
    assert [measurement.date for measurement in measurements] == sorted(
        measurement.date for measurement in measurements
    )


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


@allure.story("Calculate City Average")
@allure.title("Calculate the average AQI for a city")
def test_get_city_average_aqi(
    populated_repository: AirQualityRepository,
) -> None:
    average_aqi = populated_repository.get_city_average_aqi("Amsterdam")

    assert average_aqi == pytest.approx(70 / 3)


@allure.story("Calculate City Average")
@allure.title("Return None when a city has no measurements")
def test_get_city_average_aqi_without_measurements(
    repository: AirQualityRepository,
) -> None:
    assert repository.get_city_average_aqi("Amsterdam") is None


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
    assert [average for _, average in best_cities] == pytest.approx(
        [70 / 3, 30, 65]
    )


@allure.story("Rank Cities")
@allure.title("Return an empty list when no cities have measurements")
def test_get_best_cities_without_measurements(
    repository: AirQualityRepository,
) -> None:
    assert repository.get_best_cities() == []


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
