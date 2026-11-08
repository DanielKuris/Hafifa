from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import get_session
from logic.air_quality_service import upload_air_quality_data
from logic.query_service import (
    get_best_cities,
    get_city_aqi_history,
    get_city_average_aqi,
    get_measurements,
)
from schemas.air_quality import (
    AirQualityResponse,
    CityAverageResponse,
)
from schemas.upload import UploadResponse

router = APIRouter(prefix="/air-quality", tags=["Air Quality"])


@router.get(
    "/measurements",
    response_model=list[AirQualityResponse],
)
def read_measurements(
    city: str | None = Query(default=None, min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
    session: Session = Depends(get_session),
) -> list[AirQualityResponse]:
    return get_measurements(session, city, start_date, end_date)


@router.get(
    "/cities/{city}/history",
    response_model=list[AirQualityResponse],
)
def read_city_aqi_history(
    city: str,
    session: Session = Depends(get_session),
) -> list[AirQualityResponse]:
    return get_city_aqi_history(session, city)


@router.get(
    "/cities/{city}/average",
    response_model=CityAverageResponse,
)
def read_city_average_aqi(
    city: str,
    session: Session = Depends(get_session),
) -> CityAverageResponse:
    return get_city_average_aqi(session, city)


@router.get(
    "/best-cities",
    response_model=list[CityAverageResponse],
)
def read_best_cities(
    session: Session = Depends(get_session),
) -> list[CityAverageResponse]:
    return get_best_cities(session)


@router.post(
    "/upload",
    response_model=UploadResponse,
)
def upload_measurements(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    return upload_air_quality_data(session, file.file)
