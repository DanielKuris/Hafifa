from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_session
from logic.alert_service import (
    get_alerts,
    get_alerts_by_city,
    get_alerts_by_date,
)
from schemas.alert import AlertResponse


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def read_alerts(
    session: Session = Depends(get_session),
) -> list[AlertResponse]:
    return get_alerts(session)


@router.get(
    "/by-date/{alert_date}",
    response_model=list[AlertResponse],
)
def read_alerts_by_date(
    alert_date: date,
    session: Session = Depends(get_session),
) -> list[AlertResponse]:
    return get_alerts_by_date(session, alert_date)


@router.get(
    "/by-city/{city}",
    response_model=list[AlertResponse],
)
def read_alerts_by_city(
    city: str,
    session: Session = Depends(get_session),
) -> list[AlertResponse]:
    return get_alerts_by_city(session, city)