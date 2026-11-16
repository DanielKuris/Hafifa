
from io import BytesIO

import allure
import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError

from config.settings import settings
from data.repository import AirQualityRepository
from logic.air_quality_service import AirQualityService


@allure.story("CSV Upload")
@allure.title("Roll back the database transaction when alert insertion fails")
def test_upload_air_quality_data_rolls_back_on_alert_insertion_failure(
    air_quality_service: AirQualityService,
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alerts_dataframe = measurement_dataframe.loc[
        measurement_dataframe["aqi"] > settings.AQI_ALERT_THRESHOLD,
        ["date", "city", "aqi"],
    ]

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurement_dataframe, alerts_dataframe, 0),
    )

    original_insert_alerts = repository.insert_alerts

    def insert_alerts_with_invalid_measurement(
        dataframe: pd.DataFrame,
    ) -> None:
        dataframe["measurement_id"] = -1
        original_insert_alerts(dataframe)

    monkeypatch.setattr(
        repository,
        "insert_alerts",
        insert_alerts_with_invalid_measurement,
    )

    with pytest.raises(IntegrityError):
        air_quality_service.upload_air_quality_data(BytesIO())

    assert repository.get_measurements() == []
    assert repository.get_alerts() == []
