from io import BytesIO

import allure
import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError

from data.repository import AirQualityRepository
from logic.air_quality_service import AirQualityService


@allure.story("CSV Upload")
@allure.title("Roll back the database transaction when alert insertion fails")
def test_upload_air_quality_data_rolls_back_on_alert_insertion_failure(
    air_quality_service: AirQualityService,
    repository: AirQualityRepository,
    csv_dataframe: pd.DataFrame,
    alert_measurements: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    assert not alert_measurements.empty, (
        "Test requires at least one alert measurement"
    )

    original_insert_measurements = repository.insert_measurements

    def insert_measurements_with_invalid_ids(
        dataframe: pd.DataFrame,
    ) -> list[int]:
        inserted_ids = original_insert_measurements(dataframe)

        return [-1] * len(inserted_ids)

    monkeypatch.setattr(
        repository,
        "insert_measurements",
        insert_measurements_with_invalid_ids,
    )

    csv_file = BytesIO(
        csv_dataframe.to_csv(index=False).encode("utf-8")
    )

    with pytest.raises(IntegrityError):
        air_quality_service.upload_air_quality_data(csv_file)

    assert repository.get_measurements() == []
    assert repository.get_alerts() == []