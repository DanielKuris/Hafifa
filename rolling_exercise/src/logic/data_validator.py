import logging
import math
from datetime import date

import pandas as pd

from logic.exceptions import InvalidCSVError

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"date", "city", "PM2.5", "NO2", "CO2"}
POLLUTANT_COLUMNS = ("PM2.5", "NO2", "CO2")


def validate_dataframe(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    validate_required_fields(dataframe)

    valid = pd.Series(True, index=dataframe.index)

    valid &= validate_dates(dataframe["date"])
    valid &= validate_cities(dataframe["city"])
    valid &= validate_pollutants(dataframe)

    ignored_rows = int((~valid).sum())
    log_invalid_rows(dataframe, valid)

    return dataframe.loc[valid].copy(), ignored_rows


def validate_required_fields(dataframe: pd.DataFrame) -> None:
    missing_fields = REQUIRED_FIELDS.difference(dataframe.columns)

    if missing_fields:
        raise InvalidCSVError(
            f"CSV is missing required columns: {', '.join(sorted(missing_fields))}"
        )


def validate_dates(values: pd.Series) -> pd.Series:
    dates = values.astype("string").str.strip()

    parsed_dates = pd.to_datetime(
        dates,
        format="%Y-%m-%d",
        errors="coerce",
    )

    return (
        dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
        & parsed_dates.notna()
        & (parsed_dates <= pd.Timestamp(date.today()))
    )


def validate_cities(values: pd.Series) -> pd.Series:
    cities = values.astype("string").str.strip()

    return cities.notna() & cities.ne("")


def validate_pollutants(dataframe: pd.DataFrame) -> pd.Series:
    valid = pd.Series(True, index=dataframe.index)

    for column in POLLUTANT_COLUMNS:
        valid &= validate_pollutant(dataframe[column])

    return valid


def validate_pollutant(values: pd.Series) -> pd.Series:
    numeric_values = pd.to_numeric(values, errors="coerce")

    return (
        values.notna()
        & values.astype("string").str.strip().ne("")
        & numeric_values.notna()
        & numeric_values.map(math.isfinite)
        & numeric_values.ge(0)
    )


def log_invalid_rows(
    dataframe: pd.DataFrame,
    valid: pd.Series,
) -> None:
    for row_number in range(len(dataframe)):
        if not valid.iloc[row_number]:
            logger.warning(f"Skipping CSV row {row_number + 2}: invalid data")
