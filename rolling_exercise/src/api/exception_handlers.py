import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from logic.exceptions import MeasurementNotFoundError
from response_schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


async def handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    response = ErrorResponse(
        status_code=exc.status_code,
        error=HTTPStatus(exc.status_code).phrase,
        message=str(exc.detail),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
        headers=exc.headers,
    )


async def handle_validation_exception(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )

    response = ErrorResponse(
        status_code=422,
        error="Validation Error",
        message=details,
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(),
    )


async def handle_database_exception(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception(
        f"Database error while processing {request.method} {request.url.path}"
    )

    response = ErrorResponse(
        status_code=500,
        error="Database Error",
        message="A database error occurred while processing the request.",
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
    )


async def handle_unexpected_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        f"Unexpected error while processing {request.method} {request.url.path}"
    )

    response = ErrorResponse(
        status_code=500,
        error="Internal Server Error",
        message="An unexpected error occurred while processing the request.",
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
    )


async def handle_measurement_not_found(
    request: Request,
    exc: MeasurementNotFoundError,
) -> JSONResponse:
    response = ErrorResponse(
        status_code=404,
        error="Not Found",
        message=str(exc),
    )

    return JSONResponse(
        status_code=404,
        content=response.model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        StarletteHTTPException,
        handle_http_exception,
    )
    app.add_exception_handler(
        RequestValidationError,
        handle_validation_exception,
    )
    app.add_exception_handler(
        SQLAlchemyError,
        handle_database_exception,
    )
    app.add_exception_handler(
        Exception,
        handle_unexpected_exception,
    )
    app.add_exception_handler(
        MeasurementNotFoundError,
        handle_measurement_not_found,
    )
