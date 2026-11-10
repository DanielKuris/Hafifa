from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_session
from logic.alert_query_service import get_alerts
from response_schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def read_alerts(
    session: Annotated[Session, Depends(get_session)],
) -> list[AlertResponse]:
    return get_alerts(session)


@router.get(
    "/by-date/{alert_date}",
    response_model=list[AlertResponse],
)
def read_alerts_by_date(
    alert_date: date,
    session: Annotated[Session, Depends(get_session)],
) -> list[AlertResponse]:
    return get_alerts(session, alert_date=alert_date)


@router.get(
    "/by-city/{city}",
    response_model=list[AlertResponse],
)
def read_alerts_by_city(
    city: str,
    session: Annotated[Session, Depends(get_session)],
) -> list[AlertResponse]:
    return get_alerts(session, city=city)
