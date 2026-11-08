from datetime import date

from pydantic import BaseModel, ConfigDict


class AirQualityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    city: str
    pm25: float
    no2: float
    co2: float
    aqi: float
    aqi_level: str

class CityAverageResponse(BaseModel):
    city: str
    average_aqi: float
