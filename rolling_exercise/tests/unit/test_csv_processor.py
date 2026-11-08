import logging
from collections.abc import Iterator
from io import BytesIO
from typing import BinaryIO

import pytest

import logic.csv_processor as csv_processor
from logic.csv_processor import (
    CSVProcessingResult,
    CSVProcessingStats,
    create_measurement,
    process_csv,
)
from logic.exceptions import InvalidCSVError, NoValidRowsError
from models.air_quality import AirQuality


@pytest.fixture
def valid_row() -> dict[str | None, str | None]:
    return {
        "date": "2026-11-01",
        "city": "Tel Aviv",
        "PM2.5": "12.5",
        "NO2": "20",
        "CO2": "400",
    }


def mock_csv_rows(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str | None, str | None]],
) -> None:
    monkeypatch.setattr(
        csv_processor,
        "read_csv_rows",
        lambda _file: iter(rows),
    )


def test_process_csv_returns_processing_result(
    monkeypatch: pytest.MonkeyPatch,
    valid_row: dict[str | None, str | None],
) -> None:
    mock_csv_rows(monkeypatch, [valid_row])

    result = process_csv(BytesIO())

    assert isinstance(result, CSVProcessingResult)
    assert isinstance(result.stats, CSVProcessingStats)
    assert result.stats.total_rows == 0
    assert result.stats.ignored_rows == 0


def test_process_csv_valid_row(
    monkeypatch: pytest.MonkeyPatch,
    valid_row: dict[str | None, str | None],
) -> None:
    mock_csv_rows(monkeypatch, [valid_row])
    monkeypatch.setattr(
        csv_processor,
        "calculate_aqi",
        lambda _pm25, _no2, _co2: (42, "Good"),
    )

    result = process_csv(BytesIO())
    measurements = list(result.measurements)

    assert len(measurements) == 1
    assert measurements[0].city == "Tel Aviv"
    assert measurements[0].pm25 == 12.5
    assert measurements[0].no2 == 20
    assert measurements[0].co2 == 400
    assert measurements[0].aqi == 42
    assert measurements[0].aqi_level == "Good"
    assert result.stats.total_rows == 1
    assert result.stats.ignored_rows == 0


def test_process_csv_mixed_valid_and_invalid_rows(
    monkeypatch: pytest.MonkeyPatch,
    valid_row: dict[str | None, str | None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    invalid_row = valid_row.copy()
    invalid_row["NO2"] = "-5"

    mock_csv_rows(monkeypatch, [valid_row, invalid_row])
    monkeypatch.setattr(
        csv_processor,
        "calculate_aqi",
        lambda _pm25, _no2, _co2: (42, "Good"),
    )

    with caplog.at_level(logging.WARNING):
        result = process_csv(BytesIO())
        measurements = list(result.measurements)

    assert len(measurements) == 1
    assert result.stats.total_rows == 2
    assert result.stats.ignored_rows == 1
    assert "Skipping CSV row 3" in caplog.text


def test_process_csv_all_rows_invalid(
    monkeypatch: pytest.MonkeyPatch,
    valid_row: dict[str | None, str | None],
) -> None:
    invalid_row = valid_row.copy()
    invalid_row["NO2"] = "-5"

    mock_csv_rows(monkeypatch, [invalid_row])

    result = process_csv(BytesIO())

    with pytest.raises(NoValidRowsError, match="no valid measurement rows"):
        list(result.measurements)

    assert result.stats.total_rows == 1
    assert result.stats.ignored_rows == 1


def test_process_csv_empty_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_csv_rows(monkeypatch, [])

    result = process_csv(BytesIO())

    with pytest.raises(NoValidRowsError, match="contains no data rows"):
        list(result.measurements)

    assert result.stats.total_rows == 0
    assert result.stats.ignored_rows == 0


def test_process_csv_missing_required_columns(
    monkeypatch: pytest.MonkeyPatch,
    valid_row: dict[str | None, str | None],
) -> None:
    del valid_row["CO2"]
    mock_csv_rows(monkeypatch, [valid_row])

    result = process_csv(BytesIO())

    with pytest.raises(InvalidCSVError, match="missing required columns"):
        list(result.measurements)


def test_create_measurement(
    valid_row: dict[str | None, str | None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        csv_processor,
        "calculate_aqi",
        lambda _pm25, _no2, _co2: (42, "Good"),
    )

    measurement = create_measurement(valid_row)

    assert isinstance(measurement, AirQuality)
    assert measurement.city == "Tel Aviv"
    assert measurement.aqi == 42
    assert measurement.aqi_level == "Good"