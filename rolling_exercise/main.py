from fastapi import FastAPI

from api.exception_handlers import handle_measurement_not_found
from api.routes.air_quality import router as air_quality_router
from api.routes.alerts import router as alerts_router
from logic.exceptions import MeasurementNotFoundError

app = FastAPI()

app.include_router(air_quality_router)
app.include_router(alerts_router)

app.add_exception_handler(
    MeasurementNotFoundError,
    handle_measurement_not_found,
)
