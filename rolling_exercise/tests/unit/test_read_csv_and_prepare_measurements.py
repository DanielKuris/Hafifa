import logging
from datetime import date
from io import BytesIO

import allure
import pandas as pd
import pytest

import logic.read_csv_and_prepare_measurements as processor
from logic.exceptions import NoValidRowsError
from response_schemas.air_quality import AirQualityResponse


@pytest.fixture
@allure.title("Valid normalized measurement DataFrame")
def valid_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [
                date(2026, 11, 8),
                date(2026, 11, 9),
                date(2026, 11, 10),
                date(2026, 11, 11),
            ],
            "city": [
                "Tel Aviv",
                "Jerusalem",
                "Haifa",
                "Eilat",
            ],
            "pm25": [12.5, 20.0, 15.0, 8.0],
            "no2": [15.0, 25.0, 18.0, 10.0],
            "co2": [300.0, 400.0, 350.0, 250.0],
        }
    )


@allure.feature("Data Processing")
@allure.story("CSV Preparation")
@allure.title("Reject an empty CSV file")
def test_empty_csv_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        processor,
        "read_csv",
        lambda file: pd.DataFrame(),
    )

    with pytest.raises(NoValidRowsError, match="contains no data rows"):
        processor.read_csv_and_prepare_measurements(BytesIO())


@allure.feature("Data Processing")
@allure.story("CSV Preparation")
@allure.title("Reject a CSV containing no valid measurement rows")
def test_no_valid_rows_raises_error(
    monkeypatch: pytest.MonkeyPatch,
    valid_dataframe: pd.DataFrame,
) -> None:
    monkeypatch.setattr(
        processor,
        "read_csv",
        lambda file: valid_dataframe,
    )
    monkeypatch.setattr(
        processor,
        "validate_dataframe",
        lambda dataframe: (dataframe.iloc[0:0], len(dataframe)),
    )

    with pytest.raises(
        NoValidRowsError,
        match="contains no valid measurement rows",
    ):
        processor.read_csv_and_prepare_measurements(BytesIO())


@allure.feature("Data Processing")
@allure.story("CSV Preparation")
@allure.title("Prepare measurements and identify alert records")
def test_prepare_measurements(
    monkeypatch: pytest.MonkeyPatch,
    valid_dataframe: pd.DataFrame,
) -> None:
    ignored_rows = 2
    aqi_values = pd.Series([50.0, 150.0, 300.0, 80.0])
    aqi_levels = pd.Series(["Good", "Unhealthy", "Very Unhealthy", "Moderate"])

    monkeypatch.setattr(
        processor,
        "read_csv",
        lambda file: valid_dataframe,
    )
    monkeypatch.setattr(
        processor,
        "validate_dataframe",
        lambda dataframe: (dataframe, ignored_rows),
    )
    monkeypatch.setattr(
        processor,
        "calculate_aqi",
        lambda dataframe: (aqi_values, aqi_levels),
    )
    monkeypatch.setattr(processor.settings, "AQI_ALERT_THRESHOLD", 100)

    measurements, alerts, actual_ignored_rows = (
        processor.read_csv_and_prepare_measurements(BytesIO())
    )

    expected_columns = [
        field for field in AirQualityResponse.model_fields if field != "id"
    ]

    assert measurements.columns.tolist() == expected_columns
    assert measurements["aqi"].tolist() == [50.0, 150.0, 300.0, 80.0]
    assert measurements["aqi_level"].tolist() == [
        "Good",
        "Unhealthy",
        "Very Unhealthy",
        "Moderate",
    ]

    assert alerts.columns.tolist() == ["date", "city", "aqi"]
    assert alerts["city"].tolist() == ["Jerusalem", "Haifa"]
    assert alerts["aqi"].tolist() == [150.0, 300.0]

    assert actual_ignored_rows == ignored_rows


@allure.feature("Data Processing")
@allure.story("CSV Preparation")
@allure.title("Log the number of ignored CSV rows")
def test_logs_ignored_rows(
    monkeypatch: pytest.MonkeyPatch,
    valid_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        processor,
        "read_csv",
        lambda file: valid_dataframe,
    )
    monkeypatch.setattr(
        processor,
        "validate_dataframe",
        lambda dataframe: (dataframe, 2),
    )
    monkeypatch.setattr(
        processor,
        "calculate_aqi",
        lambda dataframe: (
            pd.Series([50.0, 60.0, 70.0, 80.0]),
            pd.Series(["Good", "Good", "Good", "Moderate"]),
        ),
    )

    with caplog.at_level(logging.INFO, logger=processor.__name__):
        processor.read_csv_and_prepare_measurements(BytesIO())

    assert "Ignored 2 invalid CSV rows" in caplog.text
