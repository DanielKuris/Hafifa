
import inspect
from collections.abc import Generator
from datetime import date
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

from config.settings import settings
from main import app
from api.dependencies import get_session
from data.repository import AirQualityRepository
from logic.alert_query_service import AlertService
from logic.air_quality_service import AirQualityService


@pytest.fixture(scope="session")
@allure.title("Create test database engine")
def test_engine() -> Generator[Engine]:
    if settings.DATABASE_URL is None:
        raise RuntimeError("DATABASE_URL is not configured")

    database_url = str(settings.DATABASE_URL)
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

@pytest.fixture
@allure.title("Prepare CSV upload data")
def sample_csv(measurement_dataframe: pd.DataFrame) -> bytes:
    csv_dataframe = measurement_dataframe[
        ["date", "city", "pm25", "no2", "co2"]
    ].rename(
        columns={
            "pm25": "PM2.5",
            "no2": "NO2",
            "co2": "CO2",
        }
    )

    return csv_dataframe.to_csv(index=False).encode("utf-8")

@pytest.fixture
@allure.title("Prepare measurement data")
def measurement_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date(2025, 1, 3),
                "city": "Amsterdam",
                "pm25": 10.0,
                "no2": 10.0,
                "co2": 10.0,
                "aqi": 10,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 3),
                "city": "Amsterdam",
                "pm25": 20.0,
                "no2": 20.0,
                "co2": 20.0,
                "aqi": 20,
                "aqi_level": "Good",
            },
            {
                "date": date(2025, 1, 1),
                "city": "Berlin",
                "pm25": 30.0,
                "no2": 30.0,
                "co2": 30.0,
                "aqi": 30,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 2),
                "city": "Amsterdam",
                "pm25": 40.0,
                "no2": 40.0,
                "co2": 40.0,
                "aqi": 40,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 4),
                "city": "Cairo",
                "pm25": 50.0,
                "no2": 50.0,
                "co2": 50.0,
                "aqi": 50,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 5),
                "city": "Delhi",
                "pm25": 60.0,
                "no2": 60.0,
                "co2": 60.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 10,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 5),
                "city": "Delhi",
                "pm25": 70.0,
                "no2": 70.0,
                "co2": 70.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 20,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 6),
                "city": "Cairo",
                "pm25": 80.0,
                "no2": 80.0,
                "co2": 80.0,
                "aqi": 80,
                "aqi_level": "Moderate",
            },
            {
                "date": date(2025, 1, 7),
                "city": "Mumbai",
                "pm25": 90.0,
                "no2": 90.0,
                "co2": 90.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 30,
                "aqi_level": "Hazardous",
            },
            {
                "date": date(2025, 1, 7),
                "city": "Mumbai",
                "pm25": 100.0,
                "no2": 100.0,
                "co2": 100.0,
                "aqi": settings.AQI_ALERT_THRESHOLD + 40,
                "aqi_level": "Hazardous",
            },
        ]
    )

@pytest.fixture
@allure.title("Prepare CSV DataFrame with original column names")
def csv_dataframe(measurement_dataframe: pd.DataFrame) -> pd.DataFrame:
    return measurement_dataframe[
        ["date", "city", "pm25", "no2", "co2"]
    ].assign(
        date=lambda dataframe: dataframe["date"].astype(str)
    ).rename(
        columns={
            "pm25": "PM2.5",
            "no2": "NO2",
            "co2": "CO2",
        }
    )


def _create_alert_dataframe(
    measurement_dataframe: pd.DataFrame,
    measurement_ids: list[int],
) -> pd.DataFrame:
    records = [
        {
            "date": record["date"],
            "city": record["city"],
            "aqi": record["aqi"],
            "measurement_id": measurement_id,
        }
        for record, measurement_id in zip(
            measurement_dataframe.to_dict(orient="records"),
            measurement_ids,
            strict=True,
        )
        if record["aqi"] > settings.AQI_ALERT_THRESHOLD
    ]

    return pd.DataFrame(records)


@pytest.fixture
@allure.title("Populate database with air quality measurements")
def populated_repository(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> AirQualityRepository:
    repository.insert_measurements(measurement_dataframe)

    return repository


@pytest.fixture
@allure.title("Populate database with measurements and alerts")
def populated_repository_with_alerts(
    repository: AirQualityRepository,
    measurement_dataframe: pd.DataFrame,
) -> AirQualityRepository:
    measurement_ids = repository.insert_measurements(measurement_dataframe)
    alerts_dataframe = _create_alert_dataframe(
        measurement_dataframe,
        measurement_ids,
    )
    repository.insert_alerts(alerts_dataframe)

    return repository


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
