from datetime import date
from io import BytesIO

import allure
import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from logic.air_quality_service import AirQualityService


@pytest.fixture
@allure.title("Create air quality repository")
def repository(db_session: Session) -> AirQualityRepository:
    return AirQualityRepository(db_session)


@pytest.fixture
@allure.title("Create air quality service")
def air_quality_service(
    repository: AirQualityRepository,
    db_session: Session,
) -> AirQualityService:
    return AirQualityService(repository, db_session)


@pytest.fixture
@allure.title("Prepare measurement data")
def measurement_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date(2025, 1, 1),
                "city": "Amsterdam",
                "pm25": 10.0,
                "no2": 20.0,
                "co2": 30.0,
                "aqi": 50,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 2),
                "city": "Berlin",
                "pm25": 40.0,
                "no2": 50.0,
                "co2": 60.0,
                "aqi": 350,
                "aqi_level": "Hazardous",
            },
        ]
    )


@pytest.fixture
@allure.title("Prepare alert data")
def alerts_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date(2025, 1, 2),
                "city": "Berlin",
                "aqi": 350,
            }
        ],
        index=[1],
    )


@allure.feature("Air Quality")
@allure.story("CSV Upload")
@allure.title("Roll back the database transaction when alert insertion fails")
def test_upload_air_quality_data_rolls_back_on_alert_insertion_failure(
    air_quality_service: AirQualityService,
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
    alerts_dataframe: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def prepare_measurements(
        file: BytesIO,
    ) -> tuple[pd.DataFrame, pd.DataFrame, int]:
        return measurement_dataframe, alerts_dataframe, 0

    original_insert_alerts = repository.insert_alerts

    def insert_alerts_with_invalid_measurement(
        dataframe: pd.DataFrame,
    ) -> None:
        invalid_dataframe = dataframe.copy()
        invalid_dataframe["measurement_id"] = -1
        original_insert_alerts(invalid_dataframe)

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        prepare_measurements,
    )
    monkeypatch.setattr(
        repository,
        "insert_alerts",
        insert_alerts_with_invalid_measurement,
    )

    with pytest.raises(IntegrityError):
        air_quality_service.upload_air_quality_data(BytesIO())

    assert repository.get_measurements() == []
    assert repository.get_alerts() == []
