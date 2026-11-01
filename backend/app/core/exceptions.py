import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def error_response(request: Request, code: str, message: str, details=None, status_code: int = 400):
    request_id = (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
        or uuid.uuid4().hex
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error_code": code,
            "message": message,
            "details": details or [],
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return error_response(
            request,
            "VALIDATION_ERROR",
            "The submitted request is invalid.",
            exc.errors(),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        logging.getLogger("neurosoc.db").warning(
            "database integrity error request_id=%s",
            getattr(request.state, "request_id", "unknown"),
            exc_info=exc,
        )
        return error_response(
            request,
            "DATABASE_CONFLICT",
            "The request conflicts with existing data.",
            [],
            status.HTTP_409_CONFLICT,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
        logging.getLogger("neurosoc.app").exception(
            "Unhandled error request_id=%s", request_id, exc_info=exc
        )
        return error_response(
            request,
            "INTERNAL_ERROR",
            "An unexpected server error occurred.",
            [],
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
