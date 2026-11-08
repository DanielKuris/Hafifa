
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from api.dependencies import get_session
from config.settings import settings
from main import app


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    if settings.TEST_DATABASE_URL is None:
        raise RuntimeError("TEST_DATABASE_URL is not configured")

    database_url = str(settings.TEST_DATABASE_URL)
    database_name = make_url(database_url).database

    if database_name != "air_quality_test_db":
        raise RuntimeError(
            f"Refusing to run tests against database: {database_name}"
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)
