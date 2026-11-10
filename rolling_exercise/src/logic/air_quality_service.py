import logging
from datetime import date
from typing import BinaryIO

from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from database.models.air_quality import AirQuality
from logic.exceptions import MeasurementNotFoundError
from logic.read_csv_and_prepare_measurements import (
    read_csv_and_prepare_measurements,
)

logger = logging.getLogger(__name__)


class AirQualityService:
    def __init__(self, session: Session) -> None:
        self.repository = AirQualityRepository(session)
        self.session = session

    def upload_air_quality_data(self, file: BinaryIO) -> dict[str, int]:
        measurements_dataframe, alerts_dataframe, ignored_rows = (
            read_csv_and_prepare_measurements(file)
        )

        measurements_dataframe = measurements_dataframe.rename(
            columns={
                "aqi_value": "aqi",
                "aqi_description": "aqi_level",
            }
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

            self.repository.insert_alerts(alerts_dataframe)

        logger.info(
            f"Processed {len(measurements_dataframe) + ignored_rows} CSV rows: "
            f"inserted {len(measurements_dataframe)} measurements, "
            f"ignored {ignored_rows} rows, "
            f"created {len(alerts_dataframe)} alerts"
        )

        return {
            "total_rows": len(measurements_dataframe) + ignored_rows,
            "inserted_rows": len(measurements_dataframe),
            "ignored_rows": ignored_rows,
            "alerts_created": len(alerts_dataframe),
        }

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
            raise MeasurementNotFoundError(f"No measurements found for city '{city}'.")

        return city, average_aqi

    def get_best_cities(self) -> list[tuple[str, float]]:
        results = self.repository.get_best_cities()

        return results
