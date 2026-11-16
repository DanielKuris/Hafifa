from datetime import date

import allure
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from config.settings import settings


@pytest.fixture
@allure.title("Upload CSV and populate the database")
def uploaded_csv(
    client: TestClient,
    csv_dataframe: pd.DataFrame,
) -> dict[str, int]:
    upload_dataframe = csv_dataframe.assign(
        CO2=lambda dataframe: dataframe["CO2"].where(
            ~dataframe["city"].isin(["Delhi", "Mumbai"]),
            150,
        )
    )

    response = client.post(
        "/air-quality/upload",
        files={
            "file": (
                "measurements.csv",
                upload_dataframe.to_csv(index=False).encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    return response.json()


@allure.story("CSV Upload")
@allure.title("Upload CSV and return the upload summary")
def test_upload_measurements(
    uploaded_csv: dict[str, int],
    csv_dataframe: pd.DataFrame,
) -> None:
    expected_alerts = csv_dataframe["city"].isin(["Delhi", "Mumbai"]).sum()

    assert uploaded_csv == {
        "total_rows": len(csv_dataframe),
        "inserted_rows": len(csv_dataframe),
        "ignored_rows": 0,
        "alerts_created": expected_alerts,
    }


@allure.story("Measurements")
@allure.title("Retrieve all uploaded measurements")
def test_read_measurements(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    response = client.get("/air-quality/measurements")
    measurements = response.json()

    assert response.status_code == 200
    assert len(measurements) == uploaded_csv["inserted_rows"]
    assert {
        "id",
        "date",
        "city",
        "pm25",
        "no2",
        "co2",
        "aqi",
        "aqi_level",
    }.issubset(measurements[0])


@allure.story("Measurements")
@allure.title("Filter measurements by city")
def test_read_measurements_by_city(
    client: TestClient,
    uploaded_csv: dict[str, int],
    measurement_dataframe: pd.DataFrame,
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params={"city": "Amsterdam"},
    )
    measurements = response.json()

    expected_count = len(
        measurement_dataframe[measurement_dataframe["city"] == "Amsterdam"]
    )

    assert response.status_code == 200
    assert len(measurements) == expected_count
    assert all(
        measurement["city"] == "Amsterdam"
        for measurement in measurements
    )


@allure.story("Measurements")
@allure.title("Filter measurements by date range")
def test_read_measurements_by_date_range(
    client: TestClient,
    uploaded_csv: dict[str, int],
    measurement_dataframe: pd.DataFrame,
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params={
            "start_date": "2025-01-03",
            "end_date": "2025-01-05",
        },
    )
    measurements = response.json()

    expected_count = len(
        measurement_dataframe[
            measurement_dataframe["date"].between(
                date(2025, 1, 3),
                date(2025, 1, 5),
            )
        ]
    )

    assert response.status_code == 200
    assert len(measurements) == expected_count
    assert all(
        "2025-01-03" <= measurement["date"] <= "2025-01-05"
        for measurement in measurements
    )


@allure.story("Measurements")
@allure.title("Combine city and date filters")
def test_read_measurements_with_combined_filters(
    client: TestClient,
    uploaded_csv: dict[str, int],
    measurement_dataframe: pd.DataFrame,
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params={
            "city": "Amsterdam",
            "start_date": "2025-01-03",
            "end_date": "2025-01-03",
        },
    )
    measurements = response.json()

    expected_count = len(
        measurement_dataframe[
            (measurement_dataframe["city"] == "Amsterdam")
            & (measurement_dataframe["date"] == date(2025, 1, 3))
        ]
    )

    assert response.status_code == 200
    assert len(measurements) == expected_count
    assert all(
        measurement["city"] == "Amsterdam"
        and measurement["date"] == "2025-01-03"
        for measurement in measurements
    )


@allure.story("Measurements")
@allure.title("Return an empty list when no measurements match")
def test_read_measurements_without_matches(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    response = client.get(
        "/air-quality/measurements",
        params={"city": "Tokyo"},
    )

    assert response.status_code == 200
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

    assert response.status_code == 422


@allure.story("City History")
@allure.title("Retrieve a city's air quality history")
def test_read_city_aqi_history(
    client: TestClient,
    uploaded_csv: dict[str, int],
    measurement_dataframe: pd.DataFrame,
) -> None:
    response = client.get("/air-quality/cities/Delhi/history")
    measurements = response.json()

    expected_count = len(
        measurement_dataframe[measurement_dataframe["city"] == "Delhi"]
    )

    assert response.status_code == 200
    assert len(measurements) == expected_count
    assert all(
        measurement["city"] == "Delhi"
        for measurement in measurements
    )


@allure.story("City History")
@allure.title("Return an empty list when a city has no history")
def test_read_city_aqi_history_without_records(
    client: TestClient,
) -> None:
    response = client.get("/air-quality/cities/Tokyo/history")

    assert response.status_code == 200
    assert response.json() == []


@allure.story("City Average")
@allure.title("Calculate a city's average AQI")
def test_read_city_average_aqi(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    measurements = client.get("/air-quality/measurements").json()
    expected_average = pd.DataFrame(measurements).loc[
        lambda dataframe: dataframe["city"] == "Amsterdam",
        "aqi",
    ].mean()

    response = client.get("/air-quality/cities/Amsterdam/average")

    assert response.status_code == 200
    assert response.json()["city"] == "Amsterdam"
    assert response.json()["average_aqi"] == pytest.approx(expected_average)


@allure.story("City Average")
@allure.title("Return not found when a city has no average AQI")
def test_read_city_average_aqi_without_records(
    client: TestClient,
) -> None:
    response = client.get("/air-quality/cities/Tokyo/average")

    assert response.status_code == 404
    assert response.json()["errtype"] == "Not Found"


@allure.story("Best Cities")
@allure.title("Retrieve cities ranked by average AQI")
def test_read_best_cities(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    measurements = pd.DataFrame(
        client.get("/air-quality/measurements").json()
    )

    expected_cities = (
        measurements.groupby("city")["aqi"]
        .mean()
        .sort_values()
        .head(settings.LIMIT_BEST_CITIES)
    )

    response = client.get("/air-quality/best-cities")
    actual_cities = response.json()

    assert response.status_code == 200
    assert [city["city"] for city in actual_cities] == list(
        expected_cities.index
    )

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

    assert response.status_code == 404
    assert response.json()["errtype"] == "Not Found"


@allure.story("Alerts")
@allure.title("Retrieve all generated alerts")
def test_read_alerts(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    response = client.get("/alerts/")
    alerts = response.json()

    assert response.status_code == 200
    assert len(alerts) == uploaded_csv["alerts_created"]
    assert alerts
    assert {
        "id",
        "date",
        "city",
        "aqi",
    }.issubset(alerts[0])
    assert all(
        alert["aqi"] > settings.AQI_ALERT_THRESHOLD
        for alert in alerts
    )


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts exist")
def test_read_alerts_without_records(
    client: TestClient,
) -> None:
    response = client.get("/alerts/")

    assert response.status_code == 200
    assert response.json() == []


@allure.story("Alerts")
@allure.title("Filter generated alerts by date")
def test_read_alerts_by_date(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    all_alerts = client.get("/alerts/").json()
    alert_date = all_alerts[0]["date"]

    response = client.get(f"/alerts/by-date/{alert_date}")

    expected_alerts = [
        alert
        for alert in all_alerts
        if alert["date"] == alert_date
    ]

    assert response.status_code == 200
    assert response.json() == expected_alerts


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts match the date")
def test_read_alerts_by_date_without_matches(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    response = client.get("/alerts/by-date/2025-01-08")

    assert response.status_code == 200
    assert response.json() == []


@allure.story("Request Validation")
@allure.title("Reject an invalid alert date")
def test_read_alerts_by_invalid_date(
    client: TestClient,
) -> None:
    response = client.get("/alerts/by-date/invalid-date")

    assert response.status_code == 422


@allure.story("Alerts")
@allure.title("Filter generated alerts by city")
def test_read_alerts_by_city(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    all_alerts = client.get("/alerts/").json()
    alert_city = all_alerts[0]["city"]

    response = client.get(f"/alerts/by-city/{alert_city}")

    expected_alerts = [
        alert
        for alert in all_alerts
        if alert["city"] == alert_city
    ]

    assert response.status_code == 200
    assert response.json() == expected_alerts


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts match the city")
def test_read_alerts_by_city_without_matches(
    client: TestClient,
    uploaded_csv: dict[str, int],
) -> None:
    response = client.get("/alerts/by-city/Tokyo")

    assert response.status_code == 200
    assert response.json() == []


@allure.story("CSV Upload")
@allure.title("Reject an upload request without a file")
def test_upload_measurements_without_file(
    client: TestClient,
) -> None:
    response = client.post("/air-quality/upload")

    assert response.status_code == 422