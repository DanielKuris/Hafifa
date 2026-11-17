import allure
import pandas as pd
import pytest

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
    assert {measurement.id for measurement in measurements} == set(measurement_ids)


@allure.story("Insert Alerts")
@allure.title("Insert alerts linked to their measurements")
def test_insert_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
    measurements_that_would_produce_alerts: pd.DataFrame,
) -> None:
    measurement_ids = repository.insert_measurements(measurement_dataframe)

    measurement_ids_by_index = dict(
        zip(measurement_dataframe.index, measurement_ids, strict=True)
    )

    alerts_dataframe = measurements_that_would_produce_alerts.assign(
        measurement_id=measurements_that_would_produce_alerts.index.map(
            measurement_ids_by_index
        )
    )

    repository.insert_alerts(alerts_dataframe)
    alerts = repository.get_alerts()

    assert len(alerts) == len(alerts_dataframe)
    assert {alert.measurement.id for alert in alerts} == set(
        alerts_dataframe["measurement_id"]
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
    measurement_dataframe: pd.DataFrame,
) -> None:
    city = measurement_dataframe["city"].iloc[0]
    city_measurements = measurement_dataframe.loc[measurement_dataframe["city"] == city]

    start_date = city_measurements["date"].min()
    end_date = city_measurements["date"].max()

    expected_measurements = city_measurements.loc[
        city_measurements["date"].between(start_date, end_date)
    ]

    measurements = populated_repository.get_measurements(
        city=city,
        start_date=start_date,
        end_date=end_date,
    )

    assert len(measurements) == len(expected_measurements)
    assert {(measurement.date, measurement.city) for measurement in measurements} == {
        (row.date, row.city) for row in expected_measurements.itertuples()
    }


@allure.story("Calculate City Average")
@allure.title("Calculate the average AQI for a city")
def test_get_city_average_aqi(
    populated_repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    city = measurement_dataframe["city"].iloc[0]
    expected_average = measurement_dataframe.loc[
        measurement_dataframe["city"] == city,
        "aqi",
    ].mean()

    average_aqi = populated_repository.get_city_average_aqi(city)

    assert average_aqi == pytest.approx(expected_average)


@allure.story("Calculate City Average")
@allure.title("Return None when a city has no measurements")
def test_get_city_average_aqi_without_measurements(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    existing_cities = set(measurement_dataframe["city"])
    nonexistent_city = next(
        city for city in ("Nonexistent City",) if city not in existing_cities
    )

    assert repository.get_city_average_aqi(nonexistent_city) is None


@allure.story("Rank Cities")
@allure.title("Retrieve cities ranked by average AQI")
def test_get_best_cities(
    populated_repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    limit = measurement_dataframe["city"].nunique() - 2

    expected_cities = (
        measurement_dataframe.groupby("city")["aqi"].mean().sort_values().head(limit)
    )

    best_cities = populated_repository.get_best_cities(limit=limit)

    assert [city for city, _ in best_cities] == expected_cities.index.tolist()
    assert [average for _, average in best_cities] == pytest.approx(
        expected_cities.tolist()
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
    populated_database_with_alerts: None,
    repository: AirQualityRepository,
    measurements_that_would_produce_alerts: pd.DataFrame,
) -> None:
    alerts = repository.get_alerts()

    assert len(alerts) == len(measurements_that_would_produce_alerts)
    assert sorted((alert.date, alert.city, alert.aqi) for alert in alerts) == sorted(
        (row.date, row.city, row.aqi)
        for row in measurements_that_would_produce_alerts.itertuples()
    )


@allure.story("Retrieve Alerts")
@allure.title("Retrieve alerts using city and date filters")
def test_get_alerts_with_filters(
    populated_database_with_alerts: None,
    repository: AirQualityRepository,
    measurements_that_would_produce_alerts: pd.DataFrame,
) -> None:
    first_alert = measurements_that_would_produce_alerts.iloc[0]
    city = first_alert["city"]
    alert_date = first_alert["date"]

    expected_alerts = measurements_that_would_produce_alerts.loc[
        (measurements_that_would_produce_alerts["city"] == city)
        & (measurements_that_would_produce_alerts["date"] == alert_date)
    ]

    alerts = repository.get_alerts(
        city=city,
        alert_date=alert_date,
    )

    assert len(alerts) == len(expected_alerts)
    assert {(alert.date, alert.city, alert.aqi) for alert in alerts} == {
        (row.date, row.city, row.aqi) for row in expected_alerts.itertuples()
    }
