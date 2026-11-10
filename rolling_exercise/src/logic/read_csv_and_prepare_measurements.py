
import logging
from typing import BinaryIO

import pandas as pd

from config.settings import settings
from data.csv_reader import read_csv
from logic.calculate_aqi import calculate_aqi
from logic.data_validator import validate_dataframe
from logic.exceptions import NoValidRowsError

logger = logging.getLogger(__name__)


def read_csv_and_prepare_measurements(
    file: BinaryIO,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    dataframe = read_csv(file)

    dataframe, ignored_rows = validate_dataframe(dataframe)

    if dataframe.empty:
        raise NoValidRowsError("CSV file contains no valid measurement rows")

    if ignored_rows:
        logger.info(f"Ignored {ignored_rows} invalid CSV rows")

    measurements_dataframe = prepare_measurements(dataframe)
    alerts_dataframe = create_alerts_dataframe(measurements_dataframe)

    return measurements_dataframe, alerts_dataframe, ignored_rows


def prepare_measurements(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.rename(
        columns={
            "PM2.5": "pm25",
            "NO2": "no2",
            "CO2": "co2",
        }
    ).copy()

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        format="%Y-%m-%d",
    ).dt.date

    dataframe["aqi_value"], dataframe["aqi_description"] = calculate_aqi(
        dataframe
    )

    return dataframe[
        [
            "date",
            "city",
            "pm25",
            "no2",
            "co2",
            "aqi_value",
            "aqi_description",
        ]
    ]


def create_alerts_dataframe(
    measurements_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    return (
        measurements_dataframe.loc[
            measurements_dataframe["aqi_value"] > settings.AQI_ALERT_THRESHOLD,
            ["date", "city", "aqi_value"],
        ]
        .rename(columns={"aqi_value": "aqi"})
        .copy()
    )
