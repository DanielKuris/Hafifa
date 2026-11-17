import logging
from collections.abc import Callable
from io import BytesIO

import allure
import pandas as pd
import pytest

from logic.exceptions import NoValidRowsError
from logic.read_csv_and_prepare_measurements import read_csv_and_prepare_measurements
from response_schemas.air_quality import AirQualityResponse


@pytest.fixture
@allure.title("Mock AQI calculation")
def mock_calculate_aqi(
    measurement_dataframe: pd.DataFrame,
) -> Callable[[pd.DataFrame], tuple[pd.Series, pd.Series]]:
    def calculate_aqi(dataframe: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        dataframe.columns = [
            {"PM2.5": "pm25", "NO2": "no2", "CO2": "co2"}.get(column, column)
            for column in dataframe.columns
        ]

        return (
            measurement_dataframe["aqi"],
            measurement_dataframe["aqi_level"],
        )

    return calculate_aqi


@allure.story("CSV Preparation")
@allure.title("Raise EmptyDataError for an empty CSV file")
def test_empty_csv_raises_error() -> None:
    with pytest.raises(pd.errors.EmptyDataError):
        read_csv_and_prepare_measurements(BytesIO(b""))


@allure.story("CSV Preparation")
@allure.title("Reject a CSV containing only headers")
def test_headers_only_csv_raises_error(
    csv_dataframe: pd.DataFrame,
) -> None:
    csv_file = BytesIO(csv_dataframe.head(0).to_csv(index=False).encode("utf-8"))

    with pytest.raises(NoValidRowsError):
        read_csv_and_prepare_measurements(csv_file)


@allure.story("CSV Preparation")
@allure.title("Reject a CSV containing no valid measurement rows")
def test_no_valid_rows_raises_error(
    monkeypatch: pytest.MonkeyPatch,
    csv_dataframe: pd.DataFrame,
) -> None:
    monkeypatch.setattr(
        "logic.read_csv_and_prepare_measurements.validate_dataframe",
        lambda dataframe: (dataframe.iloc[0:0], len(dataframe)),
    )

    csv_file = BytesIO(csv_dataframe.to_csv(index=False).encode("utf-8"))

    with pytest.raises(NoValidRowsError):
        read_csv_and_prepare_measurements(csv_file)


@allure.story("CSV Preparation")
@allure.title(
    "Read CSV, calculate AQI, validate measurements, and extract alert records"
)
def test_prepare_measurements(
    monkeypatch: pytest.MonkeyPatch,
    measurement_dataframe: pd.DataFrame,
    measurements_that_would_produce_alerts: pd.DataFrame,
    sample_csv: bytes,
    mock_calculate_aqi: Callable[[pd.DataFrame], tuple[pd.Series, pd.Series]],
) -> None:
    monkeypatch.setattr(
        "logic.read_csv_and_prepare_measurements.validate_dataframe",
        lambda dataframe: (dataframe, 0),
    )
    monkeypatch.setattr(
        "logic.read_csv_and_prepare_measurements.calculate_aqi",
        mock_calculate_aqi,
    )

    measurements, alerts, ignored_rows = read_csv_and_prepare_measurements(
        BytesIO(sample_csv)
    )

    expected_measurements = measurement_dataframe.assign(
        date=measurement_dataframe["date"].astype(str)
    )

    expected_alerts = measurements_that_would_produce_alerts.assign(
        date=measurements_that_would_produce_alerts["date"].astype(str)
    )

    assert measurements.columns.tolist() == [
        field for field in AirQualityResponse.model_fields if field != "id"
    ]

    pd.testing.assert_frame_equal(
        measurements.reset_index(drop=True),
        expected_measurements.reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        alerts.reset_index(drop=True),
        expected_alerts.reset_index(drop=True),
    )

    assert ignored_rows == 0


@allure.story("CSV Preparation")
@allure.title("Log the number of ignored CSV rows")
def test_logs_ignored_rows(
    monkeypatch: pytest.MonkeyPatch,
    csv_dataframe: pd.DataFrame,
    mock_calculate_aqi: Callable[[pd.DataFrame], tuple[pd.Series, pd.Series]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arbitrary_ignored_rows = 2

    monkeypatch.setattr(
        "logic.read_csv_and_prepare_measurements.validate_dataframe",
        lambda dataframe: (dataframe, arbitrary_ignored_rows),
    )
    monkeypatch.setattr(
        "logic.read_csv_and_prepare_measurements.calculate_aqi",
        mock_calculate_aqi,
    )

    csv_content = csv_dataframe.to_csv(index=False).encode("utf-8")

    with caplog.at_level(
        logging.INFO,
        logger=read_csv_and_prepare_measurements.__module__,
    ):
        read_csv_and_prepare_measurements(BytesIO(csv_content))

    assert f"Ignored {arbitrary_ignored_rows} invalid CSV rows" in caplog.text
