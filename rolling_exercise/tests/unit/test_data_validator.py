import logging
from datetime import date, timedelta

import pandas as pd
import pytest

from logic.data_validator import validate_dataframe
from logic.exceptions import ColumnsMismatchError


@pytest.fixture
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


def test_validate_dataframe_all_valid(
    valid_dataframe: pd.DataFrame,
) -> None:
    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 4
    assert ignored_rows == 0
    pd.testing.assert_frame_equal(result, valid_dataframe)


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


def test_validate_dataframe_missing_required_column(
    valid_dataframe: pd.DataFrame,
) -> None:
    dataframe = valid_dataframe.drop(columns=["PM2.5"])

    with pytest.raises(ColumnsMismatchError):
        validate_dataframe(dataframe)


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


def test_validate_dataframe_future_dates(
    valid_dataframe: pd.DataFrame,
) -> None:
    future_date = date.today() + timedelta(days=1)
    valid_dataframe.loc[0, "date"] = future_date.isoformat()

    result, ignored_rows = validate_dataframe(valid_dataframe)

    assert len(result) == 3
    assert ignored_rows == 1
    assert result["city"].tolist() == ["Jerusalem", "Haifa", "Eilat"]


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
