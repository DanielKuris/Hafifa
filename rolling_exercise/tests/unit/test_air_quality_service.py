import logging
from datetime import date
from unittest.mock import MagicMock

import allure
import pandas as pd
import pytest

from data.repository import AirQualityRepository
from database.models.air_quality import AirQuality
from logic.air_quality_service import AirQualityService
from logic.exceptions import NoRecordsFoundError
from response_schemas.air_quality import AirQualityUploadResponse


@pytest.fixture
@allure.title("Mock Air Quality Service repository")
def repository() -> MagicMock:
    return MagicMock(spec=AirQualityRepository)


@pytest.fixture
@allure.title("Mock database session")
def session() -> MagicMock:
    return MagicMock()


@pytest.fixture
@allure.title("Create Air Quality Service service")
def service(
    repository: MagicMock,
    session: MagicMock,
) -> AirQualityService:
    return AirQualityService(repository, session)


@pytest.fixture
@allure.title("Valid prepared measurement DataFrame")
def measurements_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [
                date(2026, 11, 8),
                date(2026, 11, 9),
                date(2026, 11, 10),
            ],
            "city": ["Tel Aviv", "Jerusalem", "Haifa"],
            "pm25": [12.5, 20.0, 15.0],
            "no2": [15.0, 25.0, 18.0],
            "co2": [300.0, 400.0, 350.0],
            "aqi": [50.0, 150.0, 300.0],
            "aqi_level": ["Good", "Unhealthy", "Very Unhealthy"],
        }
    )


@allure.feature("Air Quality Service")
@allure.story("CSV Upload")
@allure.title("Upload measurements and create alerts")
def test_upload_air_quality_data(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    repository: MagicMock,
    session: MagicMock,
    measurements_dataframe: pd.DataFrame,
) -> None:
    alerts_dataframe = measurements_dataframe.loc[
        [1, 2],
        ["date", "city", "aqi"],
    ]
    ignored_rows = 2

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (
            measurements_dataframe,
            alerts_dataframe,
            ignored_rows,
        ),
    )

    repository.insert_measurements.return_value = [101, 102, 103]

    response = service.upload_air_quality_data(MagicMock())

    assert response == AirQualityUploadResponse(
        total_rows=5,
        inserted_rows=3,
        ignored_rows=2,
        alerts_created=2,
    )

    repository.insert_measurements.assert_called_once_with(measurements_dataframe)

    repository.insert_alerts.assert_called_once()

    expected_alerts = alerts_dataframe.assign(measurement_id=[102, 103])

    inserted_alerts = repository.insert_alerts.call_args.args[0]
    pd.testing.assert_frame_equal(inserted_alerts, expected_alerts)

    session.begin.assert_called_once()


@allure.feature("Air Quality Service")
@allure.story("CSV Upload")
@allure.title("Upload measurements without creating alerts")
def test_upload_air_quality_data_without_alerts(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    repository: MagicMock,
    measurements_dataframe: pd.DataFrame,
) -> None:
    alerts_dataframe = measurements_dataframe.iloc[0:0][["date", "city", "aqi"]]

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurements_dataframe, alerts_dataframe, 0),
    )
    repository.insert_measurements.return_value = [101, 102, 103]

    response = service.upload_air_quality_data(MagicMock())

    assert response.alerts_created == 0
    repository.insert_alerts.assert_not_called()

    repository.insert_measurements.assert_called_once_with(measurements_dataframe)


@allure.feature("Air Quality Service")
@allure.story("CSV Upload")
@allure.title("Log a summary after processing an uploaded CSV")
def test_upload_air_quality_data_logs_summary(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    repository: MagicMock,
    measurements_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    alerts_dataframe = measurements_dataframe.iloc[0:0][["date", "city", "aqi"]]

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurements_dataframe, alerts_dataframe, 2),
    )
    repository.insert_measurements.return_value = [101, 102, 103]

    with caplog.at_level(
        logging.INFO,
        logger="logic.air_quality_service",
    ):
        service.upload_air_quality_data(MagicMock())

    assert (
        "Processed 5 CSV rows: inserted 3 measurements, "
        "ignored 2 rows, created 0 alerts"
    ) in caplog.text


@allure.feature("Air Quality Service")
@allure.story("Measurement Retrieval")
@allure.title("Retrieve measurements using city and date filters")
def test_get_measurements(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    expected_measurements = [MagicMock(spec=AirQuality)]

    repository.get_measurements.return_value = expected_measurements

    result = service.get_measurements(
        city="Tel Aviv",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )

    assert result == expected_measurements

    repository.get_measurements.assert_called_once_with(
        "Tel Aviv",
        date(2026, 11, 1),
        date(2026, 11, 30),
    )


@allure.feature("Air Quality Service")
@allure.story("Measurement Retrieval")
@allure.title("Retrieve measurements without filters")
def test_get_measurements_without_filters(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    repository.get_measurements.return_value = []

    result = service.get_measurements()

    assert result == []

    repository.get_measurements.assert_called_once_with(
        None,
        None,
        None,
    )


@allure.feature("Air Quality Service")
@allure.story("Measurement Retrieval")
@allure.title("Retrieve AQI history for a city")
def test_get_city_aqi_history(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    expected_measurements = [MagicMock(spec=AirQuality)]

    repository.get_measurements.return_value = expected_measurements

    result = service.get_city_aqi_history("Tel Aviv")

    assert result == expected_measurements

    repository.get_measurements.assert_called_once_with(
        "Tel Aviv",
        None,
        None,
    )


@allure.feature("Air Quality Service")
@allure.story("AQI Analytics")
@allure.title("Calculate the average AQI for a city")
def test_get_city_average_aqi(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    repository.get_city_average_aqi.return_value = 75.5

    result = service.get_city_average_aqi("Tel Aviv")

    assert result == ("Tel Aviv", 75.5)

    repository.get_city_average_aqi.assert_called_once_with("Tel Aviv")


@allure.feature("Air Quality Service")
@allure.story("AQI Analytics")
@allure.title("Raise an error when a city has no AQI records")
def test_get_city_average_aqi_without_records(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    repository.get_city_average_aqi.return_value = None

    with pytest.raises(
        NoRecordsFoundError,
        match="No records found for city 'Tel Aviv'",
    ):
        service.get_city_average_aqi("Tel Aviv")


@allure.feature("Air Quality Service")
@allure.story("AQI Analytics")
@allure.title("Retrieve the three cities with the best average AQI")
def test_get_best_cities(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    expected_cities = [
        ("Tel Aviv", 45.0),
        ("Haifa", 55.0),
        ("Jerusalem", 65.0),
    ]

    repository.get_best_cities.return_value = expected_cities

    result = service.get_best_cities()

    assert result == expected_cities

    repository.get_best_cities.assert_called_once_with()


@allure.feature("Air Quality Service")
@allure.story("AQI Analytics")
@allure.title("Raise an error when no city records exist")
def test_get_best_cities_without_records(
    service: AirQualityService,
    repository: MagicMock,
) -> None:
    repository.get_best_cities.return_value = []

    with pytest.raises(
        NoRecordsFoundError,
        match="No city records found",
    ):
        service.get_best_cities()


@allure.feature("Air Quality Service")
@allure.story("CSV Upload")
@allure.title("Roll back the database transaction when alert insertion fails")
def test_upload_air_quality_data_rolls_back_on_alert_insertion_failure(
    monkeypatch: pytest.MonkeyPatch,
    service: AirQualityService,
    repository: MagicMock,
    session: MagicMock,
    measurements_dataframe: pd.DataFrame,
) -> None:
    alerts_dataframe = measurements_dataframe.loc[
        [1, 2],
        ["date", "city", "aqi"],
    ]

    monkeypatch.setattr(
        "logic.air_quality_service.read_csv_and_prepare_measurements",
        lambda file: (measurements_dataframe, alerts_dataframe, 0),
    )

    repository.insert_measurements.return_value = [101, 102, 103]
    repository.insert_alerts.side_effect = RuntimeError("Alert insertion failed")

    with pytest.raises(RuntimeError, match="Alert insertion failed"):
        service.upload_air_quality_data(MagicMock())

    session.begin.return_value.__enter__.return_value = None
    session.begin.return_value.__exit__.assert_called_once()

    assert session.begin.return_value.__exit__.call_args.args[0] is RuntimeError
