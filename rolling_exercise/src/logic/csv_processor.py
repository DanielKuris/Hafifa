import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from itertools import chain
from typing import BinaryIO

from data.csv_reader import read_csv_rows
from logic.calculate_aqi import calculate_aqi
from logic.data_validator import validate_csv_row, validate_required_fields
from logic.exceptions import InvalidCSVError, NoValidRowsError
from models.air_quality import AirQuality


logger = logging.getLogger(__name__)


@dataclass
class CSVProcessingStats:
    total_rows: int = 0
    ignored_rows: int = 0


@dataclass
class CSVProcessingResult:
    measurements: Iterator[AirQuality]
    stats: CSVProcessingStats


def process_csv(file: BinaryIO) -> CSVProcessingResult:
    stats = CSVProcessingStats()

    return CSVProcessingResult(
        measurements=iter_measurements(file, stats),
        stats=stats,
    )


def iter_measurements(
    file: BinaryIO,
    stats: CSVProcessingStats,
) -> Iterator[AirQuality]:
    rows = read_csv_rows(file)
    first_row = next(rows, None)

    if first_row is None:
        raise NoValidRowsError("CSV file contains no data rows")

    try:
        validate_required_fields(first_row)
    except ValueError as exc:
        raise InvalidCSVError(str(exc)) from exc

    for row_number, row in enumerate(chain((first_row,), rows), start=2):
        stats.total_rows += 1

        try:
            validate_csv_row(row)
            measurement = create_measurement(row)
        except ValueError as exc:
            logger.warning(f"Skipping CSV row {row_number}: {exc}")
            stats.ignored_rows += 1
            continue

        yield measurement

    if stats.total_rows == stats.ignored_rows:
        raise NoValidRowsError("CSV file contains no valid measurement rows")


def create_measurement(
    row: Mapping[str | None, str | None],
) -> AirQuality:
    measured_date = date.fromisoformat(row["date"].strip())
    city = row["city"].strip()
    pm25 = float(row["PM2.5"])
    no2 = float(row["NO2"])
    co2 = float(row["CO2"])

    aqi, aqi_level = calculate_aqi(pm25, no2, co2)

    return AirQuality(
        date=measured_date,
        city=city,
        pm25=pm25,
        no2=no2,
        co2=co2,
        aqi=aqi,
        aqi_level=aqi_level,
    )