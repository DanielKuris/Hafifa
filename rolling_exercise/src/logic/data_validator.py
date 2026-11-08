
import math
import re
from datetime import date


def validate_csv_row(
    row: dict[str | None, str | None],
) -> None:
    validate_date(row["date"])
    validate_city(row["city"])
    validate_pollutant_values(row)


def validate_required_fields(
    row: dict[str | None, str | None],
) -> None:
    required_fields = {"date", "city", "PM2.5", "NO2", "CO2"}

    if not required_fields.issubset(row):
        raise ValueError("CSV row is missing required columns")


def validate_date(value: str | None) -> None:
    if value is None:
        raise ValueError("Date cannot be empty")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        raise ValueError("Date must follow YYYY-MM-DD format")

    try:
        measured_date = date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Invalid date") from exc

    if measured_date > date.today():
        raise ValueError("Measurement date cannot be in the future")


def validate_city(value: str | None) -> None:
    if value is None or not value.strip():
        raise ValueError("City cannot be empty")


def validate_pollutant_values(
    row: dict[str | None, str | None],
) -> None:
    pollutant_columns = ("PM2.5", "NO2", "CO2")

    for column in pollutant_columns:
        validate_non_negative_number(row[column], column)


def validate_non_negative_number(
    value: str | None,
    field_name: str,
) -> None:
    if value is None:
        raise ValueError(f"{field_name} cannot be empty")

    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")

    if number < 0:
        raise ValueError(f"{field_name} cannot be negative")
