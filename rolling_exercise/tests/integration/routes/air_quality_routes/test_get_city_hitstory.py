import allure
import pandas as pd
from fastapi.testclient import TestClient

from tests.fixtures.constants import (
    HTTP_OK,
    MISSING_CITY,
)


@allure.story("City History")
@allure.title("Retrieve a city's air quality history")
def test_read_city_aqi_history(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    city = measurement_dataframe["city"].iloc[0]

    response = client.get(f"/air-quality/cities/{city}/history")
    measurements = response.json()

    expected_measurements = measurement_dataframe.loc[
        measurement_dataframe["city"] == city
    ]

    assert response.status_code == HTTP_OK
    assert len(measurements) == len(expected_measurements)
    assert all(measurement["city"] == city for measurement in measurements)


@allure.story("City History")
@allure.title("Return an empty list when a city has no history")
def test_read_city_aqi_history_without_records(
    client: TestClient,
) -> None:
    response = client.get(f"/air-quality/cities/{MISSING_CITY}/history")

    assert response.status_code == HTTP_OK
    assert response.json() == []
