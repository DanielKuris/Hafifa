
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
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from api.dependencies import get_session
from config.settings import settings
from main import app


@pytest.fixture(scope="session")
@allure.title("Create test database engine")
def test_engine() -> Generator[Engine]:
    if settings.TEST_DATABASE_URL is None:
        raise RuntimeError("TEST_DATABASE_URL is not configured")

    database_url = str(settings.TEST_DATABASE_URL)
    database_name = make_url(database_url).database

    if database_name != "air_quality_test_db":
        raise RuntimeError(f"Refusing to run tests against database: {database_name}")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    yield engine

    engine.dispose()


@pytest.fixture
@allure.title("Create isolated test database session")
def db_session(test_engine: Engine) -> Generator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
@allure.title("Create FastAPI test client")
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_session() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)


def format_fixture_value(value: object) -> str | None:
    if isinstance(value, (Engine, Session, TestClient, Mock)):
        return None

    if isinstance(value, pd.DataFrame):
        return value.to_string()

    return pformat(value, sort_dicts=False)


@pytest.fixture(autouse=True)
def attach_test_details(request: pytest.FixtureRequest) -> None:
    try:
        source = inspect.getsource(request.function)
    except (OSError, TypeError):
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

    for fixture_name in inspect.signature(request.function).parameters:
        if fixture_name == "request":
            continue

        fixture_value = request.getfixturevalue(fixture_name)
        formatted_value = format_fixture_value(fixture_value)

        if formatted_value is None:
            continue

        allure.attach(
            formatted_value,
            name=f"Fixture: {fixture_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
