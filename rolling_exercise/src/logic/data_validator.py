import logging
from collections.abc import Iterable
from datetime import date

import numpy as np
import pandas as pd

from logic.exceptions import ColumnsMismatchError
from response_schemas.air_quality import AirQualityResponse

logger = logging.getLogger(__name__)


def validate_dataframe(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    column_mapping = {
        "PM2.5": "pm25",
        "NO2": "no2",
        "CO2": "co2",
    }

    validate_required_fields(dataframe, column_mapping)
    dataframe.rename(columns=column_mapping, inplace=True)

    valid = validate_dates(dataframe)
    valid &= validate_cities(dataframe)
    valid &= validate_pollutants(dataframe, column_mapping.values())

    ignored_rows = int((~valid).sum())
    log_invalid_rows(valid)

    dataframe.drop(index=dataframe.index[~valid], inplace=True)

    return dataframe, ignored_rows


def validate_required_fields(
    dataframe: pd.DataFrame,
    column_mapping: dict[str, str],
) -> None:
    required_fields = set(AirQualityResponse.model_fields) - {
        "id",
        "aqi",
        "aqi_level",
    }
    required_fields.difference_update(column_mapping.values())
    required_fields.update(column_mapping)

    actual_fields = set(dataframe.columns)

    missing_fields = required_fields - actual_fields
    unexpected_fields = actual_fields - required_fields

    errors = []

    if missing_fields:
        errors.append(f"Missing required columns: {', '.join(sorted(missing_fields))}")

    if unexpected_fields:
        errors.append(f"Unexpected columns: {', '.join(sorted(unexpected_fields))}")

    if errors:
        raise ColumnsMismatchError("; ".join(errors))


def validate_dates(dataframe: pd.DataFrame) -> pd.Series:
    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        format="%Y-%m-%d",
        errors="coerce",
    ).dt.date

    return dataframe["date"].notna() & dataframe["date"].le(date.today())


def validate_cities(dataframe: pd.DataFrame) -> pd.Series:
    dataframe["city"] = dataframe["city"].astype("string").str.strip()
    cities = dataframe["city"]

    return cities.notna() & cities.ne("")


def validate_pollutants(
    dataframe: pd.DataFrame,
    fields: Iterable[str],
) -> pd.Series:
    valid = pd.Series(True, index=dataframe.index)

    for field in fields:
        values = pd.to_numeric(dataframe[field], errors="coerce").astype("float64")
        dataframe[field] = values
        valid &= values.notna() & np.isfinite(values) & values.ge(0)

    return valid


def log_invalid_rows(valid: pd.Series) -> None:
    for row_number, is_valid in enumerate(valid):
        if not is_valid:
            logger.warning(f"Skipping CSV row {row_number + 2}: invalid data")
