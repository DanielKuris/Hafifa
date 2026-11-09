import logging
from io import BytesIO

import pytest

from logic.csv_processor import (
    CSVProcessingResult,
    CSVProcessingStats,
    process_csv,
)
from logic.exceptions import InvalidCSVError, NoValidRowsError
from models.air_quality import AirQuality


@pytest.fixture
def valid_csv() -> bytes:
    return (
        b"date,city,PM2.5,NO2,CO2\n"
        b"2026-11-01,Tel Aviv,12.5,20,400\n"
        b"2026-11-02,Haifa,15,25,420\n"
    )


def create_csv_file(content: bytes) -> BytesIO:
    return BytesIO(content)


def test_process_csv_returns_processing_result(
    valid_csv: bytes,
) -> None:
    result = process_csv(create_csv_file(valid_csv))

    assert isinstance(result, CSVProcessingResult)
    assert iter(result.measurements) is result.measurements
    assert isinstance(result.stats, CSVProcessingStats)
    assert result.stats.total_rows == 0
    assert result.stats.ignored_rows == 0


def test_process_csv_multiple_valid_rows(
    valid_csv: bytes,
) -> None:
    result = process_csv(create_csv_file(valid_csv))

    measurements = list(result.measurements)

    assert len(measurements) == 2
    assert all(isinstance(item, AirQuality) for item in measurements)

    assert measurements[0].city == "Tel Aviv"
    assert measurements[0].pm25 == 12.5
    assert measurements[0].no2 == 20
    assert measurements[0].co2 == 400

    assert measurements[1].city == "Haifa"
    assert measurements[1].pm25 == 15
    assert measurements[1].no2 == 25
    assert measurements[1].co2 == 420

    assert result.stats.total_rows == 2
    assert result.stats.ignored_rows == 0


def test_process_csv_mixed_valid_and_invalid_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    csv_content = (
        b"date,city,PM2.5,NO2,CO2\n"
        b"2026-11-01,Tel Aviv,12.5,20,400\n"
        b"2026-11-02,Haifa,15,-5,420\n"
        b"2026-11-03,Jerusalem,18,30,450\n"
    )

    result = process_csv(create_csv_file(csv_content))

    with caplog.at_level(logging.WARNING):
        measurements = list(result.measurements)

    assert len(measurements) == 2
    assert result.stats.total_rows == 3
    assert result.stats.ignored_rows == 1
    assert "Skipping CSV row 3" in caplog.text


def test_process_csv_all_rows_invalid() -> None:
    csv_content = (
        b"date,city,PM2.5,NO2,CO2\n"
        b"2026-11-01,Tel Aviv,12.5,-5,400\n"
        b"2026-11-02,Haifa,-15,25,420\n"
    )

    result = process_csv(create_csv_file(csv_content))

    with pytest.raises(NoValidRowsError, match="no valid measurement rows"):
        list(result.measurements)

    assert result.stats.total_rows == 2
    assert result.stats.ignored_rows == 2


def test_process_csv_empty_file() -> None:
    result = process_csv(create_csv_file(b""))

    with pytest.raises(NoValidRowsError, match="contains no data rows"):
        list(result.measurements)

    assert result.stats.total_rows == 0
    assert result.stats.ignored_rows == 0


def test_process_csv_missing_required_columns() -> None:
    csv_content = b"date,city,PM2.5,NO2\n2026-11-01,Tel Aviv,12.5,20\n"

    result = process_csv(create_csv_file(csv_content))

    with pytest.raises(InvalidCSVError, match="missing required columns"):
        list(result.measurements)


def test_process_csv_closes_reader_when_generator_is_closed(
    valid_csv: bytes,
) -> None:
    file = create_csv_file(valid_csv)
    result = process_csv(file)

    next(result.measurements)
    result.measurements.close()

    assert not file.closed
    assert result.stats.total_rows == 1
