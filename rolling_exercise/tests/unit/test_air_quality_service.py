
import logging
from unittest.mock import MagicMock

import allure
import pandas as pd
import pytest

from config.settings import settings
from data.repository import AirQualityRepository
from database.models.air_quality import AirQuality
from logic.air_quality_service import AirQualityService
from logic.exceptions import NoRecordsFoundError
from response_schemas.air_quality import AirQualityUploadResponse


@pytest.fixture
@allure.title("Mock Air Quality Service repository")
def mock_repository() -> MagicMock:
    return MagicMock(spec=AirQualityRepository)


@pytest.fixture
@allure.title("Mock database session")
def mock_session() -> MagicMock:
    return MagicMock()


@pytest.fixture
@allure.title("Create Air Quality Service")
def service(
    mock_repository: MagicMock,
    mock_session: MagicMock,
) -> AirQualityService:
    return AirQualityService(mock_repository, mock_session)


def prepare_alerts_dataframe(measurement_dataframe: pd.DataFrame) -> pd.DataFrame:
    return measurement_dataframe.loc[
        measurement_dataframe["aqi"] > settings.AQI_ALERT_THRESHOLD,
        ["date", "city", "aqi"],
    ]


@allure.story("CSV Upload")
@allure.title("Upload measurements and create alerts")
def test_upload_air_quality_data(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    mock_repository: MagicMock,
    mock_session: MagicMock,
    measurement_dataframe: pd.DataFrame,
) -> None:
    alerts_dataframe = prepare_alerts_dataframe(measurement_dataframe)
    ignored_rows = 0
    measurement_ids = list(
        range(101, 101 + len(measurement_dataframe))
    )

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurement_dataframe, alerts_dataframe, ignored_rows),
    )
    mock_repository.insert_measurements.return_value = measurement_ids

    response = service.upload_air_quality_data(MagicMock())

    assert response == AirQualityUploadResponse(
        total_rows=len(measurement_dataframe) + ignored_rows,
        inserted_rows=len(measurement_dataframe),
        ignored_rows=ignored_rows,
        alerts_created=len(alerts_dataframe),
    )

    mock_repository.insert_measurements.assert_called_once_with(
        measurement_dataframe
    )

    expected_ids = dict(zip(measurement_dataframe.index, measurement_ids))
    expected_alerts = alerts_dataframe.assign(
        measurement_id=alerts_dataframe.index.map(expected_ids)
    )

    inserted_alerts = mock_repository.insert_alerts.call_args.args[0]
    pd.testing.assert_frame_equal(inserted_alerts, expected_alerts)

    mock_session.begin.assert_called_once()


@allure.story("CSV Upload")
@allure.title("Upload measurements without creating alerts")
def test_upload_air_quality_data_without_alerts(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    mock_repository: MagicMock,
    measurement_dataframe: pd.DataFrame,
) -> None:
    measurements = measurement_dataframe.assign(aqi=0)
    alerts_dataframe = measurements.iloc[0:0][["date", "city", "aqi"]]

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurements, alerts_dataframe, 0),
    )
    mock_repository.insert_measurements.return_value = list(
        range(101, 101 + len(measurements))
    )

    response = service.upload_air_quality_data(MagicMock())

    assert response.alerts_created == 0
    mock_repository.insert_alerts.assert_not_called()
    mock_repository.insert_measurements.assert_called_once_with(measurements)


@allure.story("CSV Upload")
@allure.title("Log a summary after processing an uploaded CSV")
def test_upload_air_quality_data_logs_summary(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    mock_repository: MagicMock,
    measurement_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    alerts_dataframe = measurement_dataframe.iloc[0:0][["date", "city", "aqi"]]
    ignored_rows = 0

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurement_dataframe, alerts_dataframe, ignored_rows),
    )
    mock_repository.insert_measurements.return_value = list(
        range(101, 101 + len(measurement_dataframe))
    )

    with caplog.at_level(logging.INFO, logger="logic.air_quality_service"):
        service.upload_air_quality_data(MagicMock())

    assert (
        f"Processed {len(measurement_dataframe) + ignored_rows} CSV rows: "
        f"inserted {len(measurement_dataframe)} measurements, "
        f"ignored {ignored_rows} rows, created 0 alerts"
    ) in caplog.text


@allure.story("Measurement Retrieval")
@allure.title("Retrieve measurements using city and date filters")
def test_get_measurements(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    expected_measurements = [MagicMock(spec=AirQuality)]
    mock_repository.get_measurements.return_value = expected_measurements

    result = service.get_measurements(
        city="Tel Aviv",
        start_date=pd.Timestamp("2026-11-01").date(),
        end_date=pd.Timestamp("2026-11-30").date(),
    )

    assert result == expected_measurements
    mock_repository.get_measurements.assert_called_once_with(
        "Tel Aviv",
        pd.Timestamp("2026-11-01").date(),
        pd.Timestamp("2026-11-30").date(),
    )


@allure.story("Measurement Retrieval")
@allure.title("Retrieve measurements without filters")
def test_get_measurements_without_filters(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    mock_repository.get_measurements.return_value = []

    result = service.get_measurements()

    assert result == []
    mock_repository.get_measurements.assert_called_once_with(None, None, None)


@allure.story("Measurement Retrieval")
@allure.title("Retrieve AQI history for a city")
def test_get_city_aqi_history(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    expected_measurements = [MagicMock(spec=AirQuality)]
    mock_repository.get_measurements.return_value = expected_measurements

    result = service.get_city_aqi_history("Tel Aviv")

    assert result == expected_measurements
    mock_repository.get_measurements.assert_called_once_with(
        "Tel Aviv",
        None,
        None,
    )


@allure.story("AQI Analytics")
@allure.title("Calculate the average AQI for a city")
def test_get_city_average_aqi(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    mock_repository.get_city_average_aqi.return_value = 75.5

    result = service.get_city_average_aqi("Tel Aviv")

    assert result == ("Tel Aviv", 75.5)
    mock_repository.get_city_average_aqi.assert_called_once_with("Tel Aviv")


@allure.story("AQI Analytics")
@allure.title("Raise an error when a city has no AQI records")
def test_get_city_average_aqi_without_records(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    mock_repository.get_city_average_aqi.return_value = None

    with pytest.raises(
        NoRecordsFoundError,
        match="No records found for city 'Tel Aviv'",
    ):
        service.get_city_average_aqi("Tel Aviv")


@allure.story("AQI Analytics")
@allure.title("Retrieve the three cities with the best average AQI")
def test_get_best_cities(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    expected_cities = [
        ("Tel Aviv", 45.0),
        ("Haifa", 55.0),
        ("Jerusalem", 65.0),
    ]
    mock_repository.get_best_cities.return_value = expected_cities

    result = service.get_best_cities()

    assert result == expected_cities
    mock_repository.get_best_cities.assert_called_once_with()


@allure.story("AQI Analytics")
@allure.title("Raise an error when no city records exist")
def test_get_best_cities_without_records(
    service: AirQualityService,
    mock_repository: MagicMock,
) -> None:
    mock_repository.get_best_cities.return_value = []

    with pytest.raises(NoRecordsFoundError, match="No city records found"):
        service.get_best_cities()


@allure.story("CSV Upload")
@allure.title("Roll back the database transaction when alert insertion fails")
def test_upload_air_quality_data_rolls_back_on_alert_insertion_failure(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    mock_repository: MagicMock,
    mock_session: MagicMock,
    measurement_dataframe: pd.DataFrame,
) -> None:
    alerts_dataframe = prepare_alerts_dataframe(measurement_dataframe)

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurement_dataframe, alerts_dataframe, 0),
    )

    mock_repository.insert_measurements.return_value = list(
        range(101, 101 + len(measurement_dataframe))
    )
    mock_repository.insert_alerts.side_effect = RuntimeError(
        "Alert insertion failed"
    )

    with pytest.raises(RuntimeError, match="Alert insertion failed"):
        service.upload_air_quality_data(MagicMock())

    transaction = mock_session.begin.return_value
    transaction.__exit__.assert_called_once()

    assert transaction.__exit__.call_args.args[0] is RuntimeError
