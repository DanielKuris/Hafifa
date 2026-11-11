from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from data.repository import AirQualityRepository
from database.session import SessionLocal
from logic.air_quality_service import AirQualityService
from logic.alert_query_service import AlertService


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session


def get_air_quality_repository(
    session: Annotated[Session, Depends(get_session)],
) -> AirQualityRepository:
    return AirQualityRepository(session)


def get_air_quality_service(
    repository: Annotated[
        AirQualityRepository,
        Depends(get_air_quality_repository),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> AirQualityService:
    return AirQualityService(repository, session)


def get_alert_service(
    repository: Annotated[
        AirQualityRepository,
        Depends(get_air_quality_repository),
    ],
) -> AlertService:
    return AlertService(repository)
