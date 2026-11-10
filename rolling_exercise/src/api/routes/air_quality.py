
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import get_session
from logic.air_quality_service import (
    get_best_cities,
    get_city_aqi_history,
    get_city_average_aqi,
    get_measurements,
    upload_air_quality_data,
)
from response_schemas.air_quality import (
    AirQualityResponse,
    CityAverageResponse,
)
from response_schemas.upload import UploadResponse

router = APIRouter(prefix="/air-quality", tags=["Air Quality"])


@router.get(
    "/measurements",
    response_model=list[AirQualityResponse],
)
def read_measurements(
    session: Annotated[Session, Depends(get_session)],
    city: Annotated[str | None, Query(min_length=1)] = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[AirQualityResponse]:
    return get_measurements(
        session,
        city=city,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/cities/{city}/history",
    response_model=list[AirQualityResponse],
)
def read_city_aqi_history(
    city: str,
    session: Annotated[Session, Depends(get_session)],
) -> list[AirQualityResponse]:
    return get_city_aqi_history(session, city)


@router.get(
    "/cities/{city}/average",
    response_model=CityAverageResponse,
)
def read_city_average_aqi(
    city: str,
    session: Annotated[Session, Depends(get_session)],
) -> CityAverageResponse:
    city_name, average_aqi = get_city_average_aqi(session, city)

    return CityAverageResponse(
        city=city_name,
        average_aqi=average_aqi,
    )


@router.get(
    "/best-cities",
    response_model=list[CityAverageResponse],
)
def read_best_cities(
    session: Annotated[Session, Depends(get_session)],
) -> list[CityAverageResponse]:
    return [
        CityAverageResponse(city=city, average_aqi=average_aqi)
        for city, average_aqi in get_best_cities(session)
    ]

@router.post(
    "/upload",
    response_model=UploadResponse,
)
def upload_measurements(
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_session)],
) -> UploadResponse:
    return upload_air_quality_data(session, file.file)
