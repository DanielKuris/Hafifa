
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from logic.exceptions import MeasurementNotFoundError
from response_schemas.error import ErrorResponse


def handle_measurement_not_found(
    request: Request,
    exc: MeasurementNotFoundError,
) -> JSONResponse:
    status_code = 404

    response = ErrorResponse(
        status_code=status_code,
        error="Not Found",
        message=str(exc),
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        MeasurementNotFoundError,
        handle_measurement_not_found,
    )
