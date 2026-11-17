import logging
from datetime import date, timedelta

import allure
import pandas as pd
import pytest

from logic.data_validator import validate_dataframe
from logic.exceptions import ColumnsMismatchError


@allure.story("Data Normalization")
@allure.title("Successfully validate and normalize all valid rows")
def test_validate_dataframe_all_valid(
    measurement_dataframe: pd.DataFrame,
    csv_dataframe: pd.DataFrame,
) -> None:
    result, ignored_rows = validate_dataframe(csv_dataframe)

    assert len(result) == len(measurement_dataframe)
    assert ignored_rows == 0

    assert result["date"].tolist() == measurement_dataframe["date"].tolist()
    assert result["city"].tolist() == measurement_dataframe["city"].tolist()

    assert result[["pm25", "no2", "co2"]].dtypes.eq("float64").all()
    assert not {"PM2.5", "NO2", "CO2"}.intersection(result.columns)


@allure.story("Row Validation")
@allure.title("Reject all rows containing invalid data")
def test_validate_dataframe_all_invalid(
    csv_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dataframe = csv_dataframe.copy()
    dataframe["date"] = "invalid"
    dataframe["city"] = ""

    with caplog.at_level(logging.WARNING):
        result, ignored_rows = validate_dataframe(dataframe)

    assert result.empty
    assert ignored_rows == len(dataframe)
    assert caplog.text.count("Skipping CSV row") == len(dataframe)


@allure.story("Row Validation")
@allure.title("Accept valid rows and ignore invalid rows")
def test_validate_dataframe_mixed_validity(
    measurement_dataframe: pd.DataFrame,
    csv_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dataframe = csv_dataframe.copy()
    dataframe.loc[1, "PM2.5"] = -10
    dataframe.loc[2, "date"] = "invalid"

    with caplog.at_level(logging.WARNING):
        result, ignored_rows = validate_dataframe(dataframe)

    expected = measurement_dataframe.drop(index=[1, 2])

    assert len(result) == len(expected)
    assert ignored_rows == 2
    assert result["city"].tolist() == expected["city"].tolist()
    assert result.index.tolist() == expected.index.tolist()
    assert caplog.text.count("Skipping CSV row") == 2


@allure.story("Required Columns")
@allure.title("Reject a CSV missing a required column")
def test_validate_dataframe_missing_required_column(
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.drop(columns=["PM2.5"])

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(dataframe)

    assert "Missing required columns: PM2.5" in str(exc_info.value)


@allure.story("Required Columns")
@allure.title("Reject a CSV containing an unexpected column")
def test_validate_dataframe_unexpected_column(
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.assign(temperature=20)

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(dataframe)

    assert "Unexpected columns: temperature" in str(exc_info.value)


@allure.story("Required Columns")
@allure.title("Report missing and unexpected columns together")
def test_validate_dataframe_missing_and_unexpected_columns(
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.drop(columns=["PM2.5"]).assign(temperature=20)

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(dataframe)

    error_message = str(exc_info.value)

    assert "Missing required columns: PM2.5" in error_message
    assert "Unexpected columns: temperature" in error_message


@allure.story("Row Validation")
@allure.title("Reject negative, non-numeric, infinite and missing pollutant values")
def test_validate_dataframe_invalid_pollutant_values(
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.copy()
    dataframe["NO2"] = dataframe["NO2"].astype(object)

    dataframe.loc[0, "PM2.5"] = -1
    dataframe.loc[1, "NO2"] = "invalid"
    dataframe.loc[2, "CO2"] = float("inf")
    dataframe.loc[3, "PM2.5"] = None

    result, ignored_rows = validate_dataframe(dataframe)

    assert len(result) == len(dataframe) - 4
    assert ignored_rows == 4
    assert result.index.tolist() == list(range(4, len(dataframe)))


@allure.story("Row Validation")
@allure.title("Reject measurements with future dates")
def test_validate_dataframe_future_dates(
    measurement_dataframe: pd.DataFrame,
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.copy()
    dataframe.loc[0, "date"] = (date.today() + timedelta(days=1)).isoformat()

    result, ignored_rows = validate_dataframe(dataframe)

    expected = measurement_dataframe.drop(index=0)

    assert len(result) == len(dataframe) - 1
    assert ignored_rows == 1
    assert result["city"].tolist() == expected["city"].tolist()


@allure.story("Row Validation")
@allure.title("Reject missing and empty city names")
def test_validate_dataframe_invalid_cities(
    measurement_dataframe: pd.DataFrame,
    csv_dataframe: pd.DataFrame,
) -> None:
    dataframe = csv_dataframe.copy()
    dataframe.loc[0, "city"] = ""
    dataframe.loc[1, "city"] = "   "
    dataframe.loc[2, "city"] = None

    result, ignored_rows = validate_dataframe(dataframe)

    expected = measurement_dataframe.drop(index=[0, 1, 2])

    assert len(result) == len(dataframe) - 3
    assert ignored_rows == 3
    assert result["city"].tolist() == expected["city"].tolist()
