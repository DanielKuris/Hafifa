import inspect
from collections.abc import Generator
from pprint import pformat
from unittest.mock import Mock

import allure
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from logic.air_quality_service import AirQualityService
from logic.alert_query_service import AlertService


def format_fixture_value(value: object) -> str | None:
    excluded_types = (
        Engine,
        Session,
        TestClient,
        Mock,
        AirQualityRepository,
        AirQualityService,
        AlertService,
    )

    if isinstance(value, excluded_types):
        return None

    if isinstance(value, pd.DataFrame):
        return value.to_string()

    return pformat(value, sort_dicts=False)


@pytest.fixture(autouse=True)
def attach_test_details(request: pytest.FixtureRequest) -> Generator[None]:
    try:
        source = inspect.getsource(request.function)
    except OSError, TypeError:
        source = None

    if source is not None:
        highlighted_source = highlight(
            source,
            PythonLexer(),
            HtmlFormatter(
                full=True,
                linenos="table",
                style="native",
            ),
        )

        allure.attach(
            highlighted_source,
            name="Test source code",
            attachment_type=allure.attachment_type.HTML,
        )

    yield

    for fixture_name, fixture_value in request.node.funcargs.items():
        formatted_value = format_fixture_value(fixture_value)

        if formatted_value is None:
            continue

        allure.attach(
            formatted_value,
            name=f"Fixture: {fixture_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
