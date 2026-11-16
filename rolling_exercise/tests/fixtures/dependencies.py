from collections.abc import Generator

import allure
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from api.dependencies import get_session
from config.settings import settings
from data.repository import AirQualityRepository
from logic.alert_query_service import AlertService
from logic.air_quality_service import AirQualityService
from main import app
from tests.fixtures.constants import TEST_DATABASE_NAME
import pytest

@pytest.fixture(scope="session")
@allure.title("Create test database engine")
def test_engine() -> Generator[Engine]:
    if settings.DATABASE_URL is None:
        raise RuntimeError("DATABASE_URL is not configured")

    database_url = str(settings.DATABASE_URL)
    database_name = make_url(database_url).database

    if database_name != TEST_DATABASE_NAME:
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
@allure.title("Create isolated test database session")
def db_session(test_engine: Engine) -> Generator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
@allure.title("Create FastAPI test client")
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_session() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
@allure.title("Create air quality repository")
def repository(db_session: Session) -> AirQualityRepository:
    return AirQualityRepository(db_session)


@pytest.fixture
@allure.title("Create air quality service")
def air_quality_service(
    repository: AirQualityRepository,
    db_session: Session,
) -> AirQualityService:
    return AirQualityService(repository, db_session)


@pytest.fixture
@allure.title("Create alert service")
def alert_service(repository: AirQualityRepository) -> AlertService:
    return AlertService(repository)