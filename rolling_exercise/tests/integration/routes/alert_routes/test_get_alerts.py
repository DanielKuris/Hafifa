
from datetime import timedelta

import allure
import pandas as pd
from fastapi.testclient import TestClient
from tests.fixtures.constants import (
    ALERT_FIELDS,
    HTTP_OK,
    HTTP_UNPROCESSABLE_ENTITY,
    MISSING_CITY,
)


@allure.story("Alerts")
@allure.title("Retrieve all generated alerts")
def test_read_alerts(
    client: TestClient,
    populated_database_with_alerts: None,
    alert_measurements: pd.DataFrame,
) -> None:
    alert_measurements_fields = ALERT_FIELDS - {'id'}
    expected_alerts = alert_measurements.to_dict(orient="records")

    response = client.get("/alerts/")
    alerts = response.json()

    assert response.status_code == HTTP_OK
    assert len(alerts) == len(expected_alerts)
    assert alert_measurements_fields.issubset(alerts[0])

    assert sorted(
        tuple(alert[field] for field in alert_measurements_fields)
        for alert in alerts
    ) == sorted(
        tuple(
            str(alert[field]) if field == "date" else alert[field]
            for field in alert_measurements_fields
        )
        for alert in expected_alerts
    )


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts exist")
def test_read_alerts_without_records(
    client: TestClient,
) -> None:
    response = client.get("/alerts/")

    assert response.status_code == HTTP_OK
    assert response.json() == []


@allure.story("Alerts")
@allure.title("Filter generated alerts by date")
def test_read_alerts_by_date(
    client: TestClient,
    populated_database_with_alerts: None,
    alert_measurements: pd.DataFrame,
) -> None:
    assert not alert_measurements.empty, (
        "Test requires at least one alert measurement"
    )

    alert_date = alert_measurements["date"].iloc[0]

    expected_alerts = alert_measurements.loc[
        alert_measurements["date"] == alert_date
    ]

    response = client.get(
        f"/alerts/by-date/{alert_date.isoformat()}"
    )
    alerts = response.json()

    assert response.status_code == HTTP_OK
    assert len(alerts) == len(expected_alerts)
    assert all(alert["date"] == alert_date.isoformat() for alert in alerts)


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts match the date")
def test_read_alerts_by_date_without_matches(
    client: TestClient,
    populated_database_with_alerts: None,
    alert_measurements: pd.DataFrame,
) -> None:
    assert not alert_measurements.empty, (
        "Test requires at least one alert measurement"
    )

    missing_date = alert_measurements["date"].max() + timedelta(days=1)

    response = client.get(
        f"/alerts/by-date/{missing_date.isoformat()}"
    )

    assert response.status_code == HTTP_OK
    assert response.json() == []


@allure.story("Request Validation")
@allure.title("Reject an invalid alert date")
def test_read_alerts_by_invalid_date(
    client: TestClient,
) -> None:
    response = client.get("/alerts/by-date/invalid-date")

    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY


@allure.story("Alerts")
@allure.title("Filter generated alerts by city")
def test_read_alerts_by_city(
    client: TestClient,
    populated_database_with_alerts: None,
    alert_measurements: pd.DataFrame,
) -> None:
    assert not alert_measurements.empty, (
        "Test requires at least one alert measurement"
    )

    city = alert_measurements["city"].iloc[0]

    expected_alerts = alert_measurements.loc[
        alert_measurements["city"] == city
    ]

    response = client.get(f"/alerts/by-city/{city}")
    alerts = response.json()

    assert response.status_code == HTTP_OK
    assert len(alerts) == len(expected_alerts)
    assert all(alert["city"] == city for alert in alerts)


@allure.story("Alerts")
@allure.title("Return an empty list when no alerts match the city")
def test_read_alerts_by_city_without_matches(
    client: TestClient,
    populated_database_with_alerts: None,
) -> None:
    response = client.get(f"/alerts/by-city/{MISSING_CITY}")

    assert response.status_code == HTTP_OK
    assert response.json() == []
