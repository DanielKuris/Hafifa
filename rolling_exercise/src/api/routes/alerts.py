from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_alert_service
from logic.alert_query_service import AlertService
from response_schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def read_alerts(
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> list[AlertResponse]:
    return service.get_alerts()


@router.get(
    "/by-date/{alert_date}",
    response_model=list[AlertResponse],
)
def read_alerts_by_date(
    alert_date: date,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> list[AlertResponse]:
    return service.get_alerts(alert_date=alert_date)


@router.get(
    "/by-city/{city}",
    response_model=list[AlertResponse],
)
def read_alerts_by_city(
    city: str,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> list[AlertResponse]:
    return service.get_alerts(city=city)
