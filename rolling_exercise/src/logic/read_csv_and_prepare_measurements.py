import logging
from typing import BinaryIO

import pandas as pd

from config.settings import settings
from data.csv_reader import read_csv
from logic.calculate_aqi import calculate_aqi
from logic.data_validator import validate_dataframe
from logic.exceptions import NoValidRowsError
from response_schemas.air_quality import AirQualityResponse

logger = logging.getLogger(__name__)


def read_csv_and_prepare_measurements(
    file: BinaryIO,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    dataframe = read_csv(file)

    if dataframe.empty:
        raise NoValidRowsError("CSV file contains no data rows")

    dataframe, ignored_rows = validate_dataframe(dataframe)

    if dataframe.empty:
        raise NoValidRowsError("CSV file contains no valid measurement rows")

    if ignored_rows:
        logger.info(f"Ignored {ignored_rows} invalid CSV rows")

    dataframe["aqi"], dataframe["aqi_level"] = calculate_aqi(dataframe)

    measurement_columns = [
        field for field in AirQualityResponse.model_fields if field != "id"
    ]

    dataframe = dataframe[measurement_columns]

    alerts_dataframe = dataframe.loc[
        dataframe["aqi"] > settings.AQI_ALERT_THRESHOLD,
        ["date", "city", "aqi"],
    ]

    return dataframe, alerts_dataframe, ignored_rows
