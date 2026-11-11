import logging
from datetime import date
from typing import BinaryIO

from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from database.models.air_quality import AirQuality
from logic.exceptions import NoRecordsFoundError
from logic.read_csv_and_prepare_measurements import (
    read_csv_and_prepare_measurements,
)
from response_schemas.air_quality import AirQualityUploadResponse

logger = logging.getLogger(__name__)


class AirQualityService:
    def __init__(
        self,
        repository: AirQualityRepository,
        session: Session,
    ) -> None:
        self.repository = repository
        self.session = session

    def upload_air_quality_data(
        self,
        file: BinaryIO,
    ) -> AirQualityUploadResponse:
        measurements_dataframe, alerts_dataframe, ignored_rows = (
            read_csv_and_prepare_measurements(file)
        )

        with self.session.begin():
            measurement_ids = self.repository.insert_measurements(
                measurements_dataframe
            )

            measurement_ids_by_index = dict(
                zip(
                    measurements_dataframe.index,
                    measurement_ids,
                    strict=True,
                )
            )

            alerts_dataframe = alerts_dataframe.assign(
                measurement_id=alerts_dataframe.index.map(measurement_ids_by_index)
            )

            if not alerts_dataframe.empty:
                self.repository.insert_alerts(alerts_dataframe)

        inserted_rows = len(measurements_dataframe)
        alerts_created = len(alerts_dataframe)
        total_rows = inserted_rows + ignored_rows

        logger.info(
            f"Processed {total_rows} CSV rows: "
            f"inserted {inserted_rows} measurements, "
            f"ignored {ignored_rows} rows, "
            f"created {alerts_created} alerts"
        )

        return AirQualityUploadResponse(
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            ignored_rows=ignored_rows,
            alerts_created=alerts_created,
        )

    def get_measurements(
        self,
        city: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[AirQuality]:
        return self.repository.get_measurements(
            city,
            start_date,
            end_date,
        )

    def get_city_aqi_history(self, city: str) -> list[AirQuality]:
        return self.get_measurements(city=city)

    def get_city_average_aqi(self, city: str) -> tuple[str, float]:
        average_aqi = self.repository.get_city_average_aqi(city)

        if average_aqi is None:
            raise NoRecordsFoundError(f"No records found for city '{city}'.")

        return city, average_aqi

    def get_best_cities(self) -> list[tuple[str, float]]:
        best_cities = self.repository.get_best_cities()

        if not best_cities:
            raise NoRecordsFoundError("No city records found.")

        return best_cities
