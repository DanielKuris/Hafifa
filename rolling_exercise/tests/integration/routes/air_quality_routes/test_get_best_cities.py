import allure
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from config.settings import settings
from tests.fixtures.constants import (
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_UNPROCESSABLE_ENTITY,
)


@allure.story("Best Cities")
@allure.title("Retrieve cities ranked by average AQI")
def test_read_best_cities(
    client: TestClient,
    populated_database_with_alerts: None,
    measurement_dataframe: pd.DataFrame,
) -> None:
    expected_cities = (
        measurement_dataframe.groupby("city")["aqi"]
        .mean()
        .sort_values()
        .head(settings.LIMIT_BEST_CITIES)
    )

    response = client.get("/air-quality/best-cities")
    actual_cities = response.json()

    assert response.status_code == HTTP_OK
    assert [city["city"] for city in actual_cities] == list(expected_cities.index)

    for actual, expected_average in zip(
        actual_cities,
        expected_cities,
        strict=True,
    ):
        assert actual["average_aqi"] == pytest.approx(expected_average)


@allure.story("Best Cities")
@allure.title("Return not found when no cities are available")
def test_read_best_cities_without_records(
    client: TestClient,
) -> None:
    response = client.get("/air-quality/best-cities")

    assert response.status_code == HTTP_NOT_FOUND
    assert response.json()["errtype"] == "Not Found"


@allure.story("CSV Upload")
@allure.title("Reject an upload request without a file")
def test_upload_measurements_without_file(
    client: TestClient,
) -> None:
    response = client.post("/air-quality/upload")

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY
