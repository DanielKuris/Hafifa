from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from logic.exceptions import NoRecordsFoundError
from response_schemas.error import ErrorResponse


def handle_measurement_not_found(
    request: Request,
    exc: NoRecordsFoundError,
) -> JSONResponse:
    status = HTTPStatus.NOT_FOUND

    return JSONResponse(
        status_code=status,
        content=ErrorResponse(
            errtype=status.phrase,
            message=str(exc),
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        NoRecordsFoundError,
        handle_measurement_not_found,
    )
