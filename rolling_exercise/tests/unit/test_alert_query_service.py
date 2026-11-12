from datetime import date
from unittest.mock import MagicMock

import allure
import pytest

from data.repository import AirQualityRepository
from database.models.alert import Alert
from logic.alert_query_service import AlertService


@pytest.fixture
@allure.title("Mock alert repository")
def repository() -> MagicMock:
    return MagicMock(spec=AirQualityRepository)


@pytest.fixture
@allure.title("Create alert service")
def service(repository: MagicMock) -> AlertService:
    return AlertService(repository)


@allure.feature("Alerts Service")
@allure.story("Alert Retrieval")
@allure.title("Retrieve alerts using city and date filters")
def test_get_alerts_with_filters(
    service: AlertService,
    repository: MagicMock,
) -> None:
    expected_alerts = [MagicMock(spec=Alert), MagicMock(spec=Alert)]
    alert_date = date(2026, 11, 10)

    repository.get_alerts.return_value = expected_alerts

    result = service.get_alerts(
        city="Tel Aviv",
        alert_date=alert_date,
    )

    assert result == expected_alerts

    repository.get_alerts.assert_called_once_with(
        city="Tel Aviv",
        alert_date=alert_date,
    )


@allure.feature("Alerts Service")
@allure.story("Alert Retrieval")
@allure.title("Retrieve all alerts without filters")
def test_get_alerts_without_filters(
    service: AlertService,
    repository: MagicMock,
) -> None:
    repository.get_alerts.return_value = []

    result = service.get_alerts()

    assert result == []

    repository.get_alerts.assert_called_once_with(
        city=None,
        alert_date=None,
    )
