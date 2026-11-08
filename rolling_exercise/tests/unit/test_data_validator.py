
from datetime import date, timedelta

import pytest

from logic.data_validator import (
    validate_city,
    validate_csv_row,
    validate_date,
    validate_non_negative_number,
    validate_pollutant_values,
    validate_required_fields,
)


@pytest.fixture
def valid_row() -> dict[str, str]:
    return {
        "date": "2026-11-01",
        "city": "Tel Aviv",
        "PM2.5": "12.5",
        "NO2": "20",
        "CO2": "400",
    }


def test_validate_csv_row(valid_row: dict[str, str]) -> None:
    validate_csv_row(valid_row)


def test_validate_required_fields(valid_row: dict[str, str]) -> None:
    validate_required_fields(valid_row)


def test_validate_required_fields_missing_column(
    valid_row: dict[str, str],
) -> None:
    del valid_row["CO2"]

    with pytest.raises(ValueError, match="missing required columns"):
        validate_required_fields(valid_row)


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "01-11-2026", "2026/11/01", "2026-02-30"],
)
def test_validate_date_invalid(value: str | None) -> None:
    with pytest.raises(ValueError):
        validate_date(value)


def test_validate_date_future() -> None:
    future_date = (date.today() + timedelta(days=1)).isoformat()

    with pytest.raises(ValueError, match="cannot be in the future"):
        validate_date(future_date)


def test_validate_date_valid() -> None:
    validate_date("2026-11-01")


@pytest.mark.parametrize("value", [None, "", "   "])
def test_validate_city_invalid(value: str | None) -> None:
    with pytest.raises(ValueError, match="City cannot be empty"):
        validate_city(value)


def test_validate_city_valid() -> None:
    validate_city("Tel Aviv")


@pytest.mark.parametrize(
    ("value", "field_name", "expected_message"),
    [
        (None, "PM2.5", "cannot be empty"),
        ("abc", "NO2", "must be numeric"),
        ("nan", "CO2", "must be finite"),
        ("inf", "CO2", "must be finite"),
        ("-1", "PM2.5", "cannot be negative"),
    ],
)
def test_validate_non_negative_number_invalid(
    value: str | None,
    field_name: str,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        validate_non_negative_number(value, field_name)


@pytest.mark.parametrize("value", ["0", "12.5", "400"])
def test_validate_non_negative_number_valid(value: str) -> None:
    validate_non_negative_number(value, "PM2.5")


def test_validate_pollutant_values_valid(
    valid_row: dict[str, str],
) -> None:
    validate_pollutant_values(valid_row)


def test_validate_pollutant_values_invalid(
    valid_row: dict[str, str],
) -> None:
    valid_row["NO2"] = "-5"

    with pytest.raises(ValueError, match="cannot be negative"):
        validate_pollutant_values(valid_row)
