import logging
from datetime import date, timedelta

import allure
import pandas as pd
import pytest

from logic.data_validator import validate_dataframe
from logic.exceptions import ColumnsMismatchError


@pytest.fixture
@allure.title("Valid CSV DataFrame with original column names")
def valid_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [
                "2026-11-08",
                "2026-11-09",
                "2026-11-10",
                "2026-11-11",
            ],
            "city": [
                "Tel Aviv",
                "Jerusalem",
                "Haifa",
                "Eilat",
            ],
            "PM2.5": [12.5, 20.0, 15.0, 8.0],
            "NO2": [15.0, 25.0, 18.0, 10.0],
            "CO2": [300.0, 400.0, 350.0, 250.0],
        }
    )


@allure.feature("Data Validation")
@allure.story("Data Normalization")
@allure.title("Successfully validate and normalize all valid rows")
def test_validate_dataframe_all_valid(
    valid_dataframe: pd.DataFrame,
) -> None:
    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 4
    assert ignored_rows == 0

    assert result["date"].tolist() == [
        date(2026, 11, 8),
        date(2026, 11, 9),
        date(2026, 11, 10),
        date(2026, 11, 11),
    ]

    assert result["city"].tolist() == [
        "Tel Aviv",
        "Jerusalem",
        "Haifa",
        "Eilat",
    ]

    assert result[["pm25", "no2", "co2"]].dtypes.eq("float64").all()
    assert "PM2.5" not in result.columns
    assert "NO2" not in result.columns
    assert "CO2" not in result.columns


@allure.feature("Data Validation")
@allure.story("Row Validation")
@allure.title("Reject all rows containing invalid data")
def test_validate_dataframe_all_invalid(
    valid_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    valid_dataframe["date"] = "invalid"
    valid_dataframe["city"] = ""
    valid_dataframe["PM2.5"] = -1

    with caplog.at_level(logging.WARNING):
        result, ignored_rows = validate_dataframe(valid_dataframe)

    assert result.empty
    assert ignored_rows == 4
    assert caplog.text.count("Skipping CSV row") == 4


@allure.feature("Data Validation")
@allure.story("Row Validation")
@allure.title("Accept valid rows and ignore invalid rows")
def test_validate_dataframe_mixed_validity(
    valid_dataframe: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    valid_dataframe.loc[1, "PM2.5"] = -10
    valid_dataframe.loc[2, "date"] = "invalid"

    with caplog.at_level(logging.WARNING):
        result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 2
    assert ignored_rows == 2
    assert result["city"].tolist() == ["Tel Aviv", "Eilat"]
    assert result.index.tolist() == [0, 3]

    assert caplog.text.count("Skipping CSV row") == 2


@allure.feature("Data Validation")
@allure.story("Required Columns")
@allure.title("Reject a CSV missing a required column")
def test_validate_dataframe_missing_required_column(
    valid_dataframe: pd.DataFrame,
) -> None:
    dataframe = valid_dataframe.drop(columns=["PM2.5"])

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(dataframe)

    assert "Missing required columns: PM2.5" in str(exc_info.value)


@allure.feature("Data Validation")
@allure.story("Required Columns")
@allure.title("Reject a CSV containing an unexpected column")
def test_validate_dataframe_unexpected_column(
    valid_dataframe: pd.DataFrame,
) -> None:
    valid_dataframe["temperature"] = [20, 21, 22, 23]

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(valid_dataframe)

    assert "Unexpected columns: temperature" in str(exc_info.value)


@allure.feature("Data Validation")
@allure.story("Required Columns")
@allure.title("Report missing and unexpected columns together")
def test_validate_dataframe_missing_and_unexpected_columns(
    valid_dataframe: pd.DataFrame,
) -> None:
    dataframe = valid_dataframe.drop(columns=["PM2.5"])
    dataframe["temperature"] = [20, 21, 22, 23]

    with pytest.raises(ColumnsMismatchError) as exc_info:
        validate_dataframe(dataframe)

    error_message = str(exc_info.value)

    assert "Missing required columns: PM2.5" in error_message
    assert "Unexpected columns: temperature" in error_message


@allure.feature("Data Validation")
@allure.story("Row Validation")
@allure.title("Reject negative, non-numeric, infinite and missing pollutant values")
def test_validate_dataframe_invalid_pollutant_values(
    valid_dataframe: pd.DataFrame,
) -> None:
    valid_dataframe["NO2"] = valid_dataframe["NO2"].astype(object)

    valid_dataframe.loc[0, "PM2.5"] = -1
    valid_dataframe.loc[1, "NO2"] = "invalid"
    valid_dataframe.loc[2, "CO2"] = float("inf")
    valid_dataframe.loc[3, "PM2.5"] = None

    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert result.empty
    assert ignored_rows == 4


@allure.feature("Data Validation")
@allure.story("Row Validation")
@allure.title("Reject measurements with future dates")
def test_validate_dataframe_future_dates(
    valid_dataframe: pd.DataFrame,
) -> None:
    future_date = date.today() + timedelta(days=1)
    valid_dataframe.loc[0, "date"] = future_date.isoformat()

    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 3
    assert ignored_rows == 1
    assert result["city"].tolist() == ["Jerusalem", "Haifa", "Eilat"]


@allure.feature("Data Validation")
@allure.story("Row Validation")
@allure.title("Reject missing and empty city names")
def test_validate_dataframe_invalid_cities(
    valid_dataframe: pd.DataFrame,
) -> None:
    valid_dataframe.loc[0, "city"] = ""
    valid_dataframe.loc[1, "city"] = "   "
    valid_dataframe.loc[2, "city"] = None

    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 1
    assert ignored_rows == 3
    assert result["city"].tolist() == ["Eilat"]
