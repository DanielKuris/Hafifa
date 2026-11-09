from collections.abc import Iterator
from contextlib import closing
from typing import BinaryIO

from sqlalchemy.orm import Session

from config.settings import settings
from data.repository import AirQualityRepository
from logic.csv_processor import process_csv
from models.air_quality import AirQuality
from models.alert import Alert


def upload_air_quality_data(
    session: Session,
    file: BinaryIO,
) -> dict[str, int]:
    repository = AirQualityRepository(session)
    processing_result = process_csv(file)

    with closing(processing_result.measurements) as measurements, session.begin():
        inserted_rows, alerts_created = save_measurements(
            repository,
            measurements,
        )

    return {
        "total_rows": processing_result.stats.total_rows,
        "inserted_rows": inserted_rows,
        "ignored_rows": processing_result.stats.ignored_rows,
        "alerts_created": alerts_created,
    }


def save_measurements(
    repository: AirQualityRepository,
    measurements: Iterator[AirQuality],
) -> tuple[int, int]:
    inserted_rows = 0
    alerts_created = 0
    pending_objects = 0

    for measurement in measurements:
        repository.add_measurement(measurement)
        inserted_rows += 1
        pending_objects += 1

        if measurement.aqi > settings.AQI_ALERT_THRESHOLD:
            repository.add_alert(create_alert(measurement))
            alerts_created += 1
            pending_objects += 1

        if pending_objects >= settings.DB_FLUSH_BATCH_SIZE:
            repository.flush()
            pending_objects = 0

    return inserted_rows, alerts_created


def create_alert(measurement: AirQuality) -> Alert:
    return Alert(
        date=measurement.date,
        city=measurement.city,
        aqi=measurement.aqi,
        measurement=measurement,
    )
