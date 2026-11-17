import allure
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tests.fixtures.constants import (
    AIR_QUALITY_FIELDS,
    HTTP_OK,
    HTTP_UNPROCESSABLE_ENTITY,
    MISSING_CITY,
)


@allure.story("Measurements")
@allure.title("Retrieve all uploaded measurements")
def test_read_measurements(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    response = client.get("/air-quality/measurements")
    measurements = response.json()

    assert response.status_code == HTTP_OK
    assert len(measurements) == len(measurement_dataframe)
    assert set(AIR_QUALITY_FIELDS).issubset(measurements[0])


@allure.story("Measurements")
@allure.title("Filter measurements by city")
def test_read_measurements_by_city(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    city = measurement_dataframe["city"].iloc[0]

    response = client.get(
        "/air-quality/measurements",
        params={"city": city},
    )
    measurements = response.json()

    expected_measurements = measurement_dataframe.loc[
        measurement_dataframe["city"] == city
    ]

    assert response.status_code == HTTP_OK
    assert len(measurements) == len(expected_measurements)
    assert all(measurement["city"] == city for measurement in measurements)


@allure.story("Measurements")
@allure.title("Filter measurements by date range")
def test_read_measurements_by_date_range(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    dates = sorted(measurement_dataframe["date"].unique())
    start_date, end_date = dates[1], dates[-2]

    response = client.get(
        "/air-quality/measurements",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
    measurements = response.json()

    expected_measurements = measurement_dataframe.loc[
        measurement_dataframe["date"].between(start_date, end_date)
    ]

    assert response.status_code == HTTP_OK
    assert len(measurements) == len(expected_measurements)
    assert all(
        start_date.isoformat() <= measurement["date"] <= end_date.isoformat()
        for measurement in measurements
    )


@allure.story("Measurements")
@allure.title("Combine city and date filters")
def test_read_measurements_with_combined_filters(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    first_measurement = measurement_dataframe.iloc[0]
    city = first_measurement["city"]
    measurement_date = first_measurement["date"].isoformat()

    response = client.get(
        "/air-quality/measurements",
        params={
            "city": city,
            "start_date": measurement_date,
            "end_date": measurement_date,
        },
    )
    measurements = response.json()

    expected_measurements = measurement_dataframe.loc[
        (measurement_dataframe["city"] == city)
        & (measurement_dataframe["date"] == first_measurement["date"])
    ]

    assert response.status_code == HTTP_OK
    assert len(measurements) == len(expected_measurements)
    assert all(
        measurement["city"] == city and measurement["date"] == measurement_date
        for measurement in measurements
    )


@allure.story("Measurements")
@allure.title("Return an empty list when no measurements match")
def test_read_measurements_without_matches(
    client: TestClient,
    populated_database_with_alerts: None,
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params={"city": MISSING_CITY},
    )

    assert response.status_code == HTTP_OK
    assert response.json() == []


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"city": ""}, id="empty-city"),
        pytest.param({"start_date": "invalid-date"}, id="invalid-start-date"),
        pytest.param({"end_date": "invalid-date"}, id="invalid-end-date"),
    ],
)
@allure.story("Request Validation")
@allure.title("Reject invalid measurement query parameters")
def test_read_measurements_with_invalid_parameters(
    client: TestClient,
    params: dict[str, str],
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params=params,
    )

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY
