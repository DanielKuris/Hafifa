import allure
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tests.fixtures.constants import (
    HTTP_NOT_FOUND,
    HTTP_OK,
    MISSING_CITY,
)

@allure.story("City Average")
@allure.title("Calculate a city's average AQI")
def test_read_city_average_aqi(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    city = measurement_dataframe["city"].iloc[0]

    expected_average = measurement_dataframe.loc[
        measurement_dataframe["city"] == city,
        "aqi",
    ].mean()

    response = client.get(f"/air-quality/cities/{city}/average")
    average = response.json()

    assert response.status_code == HTTP_OK
    assert average["city"] == city
    assert average["average_aqi"] == pytest.approx(expected_average)


@allure.story("City Average")
@allure.title("Return not found when a city has no average AQI")
def test_read_city_average_aqi_without_records(
    client: TestClient,
) -> None:
    response = client.get(f"/air-quality/cities/{MISSING_CITY}/average")

    assert response.status_code == HTTP_NOT_FOUND
    assert response.json()["errtype"] == "Not Found"