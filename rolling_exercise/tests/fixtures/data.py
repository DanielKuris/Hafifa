from datetime import date

import allure
import pandas as pd
import pytest

from config.settings import settings
from data.repository import AirQualityRepository
from response_schemas.alert import AlertResponse


@pytest.fixture
@allure.title("Prepare measurement data")
def measurement_dataframe_with_duplicates() -> pd.DataFrame:
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
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 10,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 5),
                "city": "Delhi",
                "pm25": 70.0,
                "no2": 70.0,
                "co2": 150.0,
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
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 30,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 7),
                "city": "Mumbai",
                "pm25": 100.0,
                "no2": 100.0,
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 40,
                "aqi_level": "Hazardous",
            },
        ]
    )


@pytest.fixture
@allure.title("Prepare measurement data")
def measurement_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date(2025, 1, 1),
                "city": "Amsterdam",
                "pm25": 10.0,
                "no2": 10.0,
                "co2": 10.0,
                "aqi": 10,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 2),
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
                "date": date(2025, 1, 3),
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
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 10,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 6),
                "city": "Delhi",
                "pm25": 70.0,
                "no2": 70.0,
                "co2": 150.0,
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
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 30,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 8),
                "city": "Mumbai",
                "pm25": 100.0,
                "no2": 100.0,
                "co2": 150.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 40,
                "aqi_level": "Hazardous",
            },
        ]
    )


@pytest.fixture
@allure.title("Prepare CSV upload data")
def sample_csv(measurement_dataframe: pd.DataFrame) -> bytes:
    dataframe = measurement_dataframe[["date", "city", "pm25", "no2", "co2"]].rename(
        columns={
            "pm25": "PM2.5",
            "no2": "NO2",
            "co2": "CO2",
        }
    )

    return dataframe.to_csv(index=False).encode("utf-8")


@pytest.fixture
@allure.title("Prepare CSV DataFrame with original column names")
def csv_dataframe(measurement_dataframe: pd.DataFrame) -> pd.DataFrame:
    return (
        measurement_dataframe[["date", "city", "pm25", "no2", "co2"]]
        .assign(date=lambda dataframe: dataframe["date"].astype(str))
        .rename(
            columns={
                "pm25": "PM2.5",
                "no2": "NO2",
                "co2": "CO2",
            }
        )
    )


@pytest.fixture
def measurements_that_would_produce_alerts(
    measurement_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    columns = list(AlertResponse.model_fields)

    columns.remove("id")

    return measurement_dataframe.loc[
        measurement_dataframe["aqi"] > settings.AQI_ALERT_THRESHOLD,
        columns,
    ]


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
@allure.title("Populate the database with measurements and alerts")
def populated_database_with_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurement_ids = repository.insert_measurements(measurement_dataframe)

    alerts_dataframe = _create_alert_dataframe(
        measurement_dataframe,
        measurement_ids,
    )

    if not alerts_dataframe.empty:
        repository.insert_alerts(alerts_dataframe)


@pytest.fixture
@allure.title("Populate database with air quality measurements")
def populated_repository(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> AirQualityRepository:
    repository.insert_measurements(measurement_dataframe)

    return repository
