from typing import Any

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.common.errors import ApplicationError


def _error_body(*, code: str, message: str, trace_id: str, details: Any = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "trace_id": trace_id,
        }
    }


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            code=f"http_{exc.status_code}",
            message=detail,
            details=None if isinstance(exc.detail, str) else exc.detail,
            trace_id=request.state.trace_id,
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    return JSONResponse(
        status_code=422,
        content=_error_body(
            code="validation_error",
            message="Request validation failed",
            details=jsonable_encoder(exc.errors()),
            trace_id=request.state.trace_id,
        ),
    )


async def application_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApplicationError):
        raise exc
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            code=exc.code,
            message=str(exc),
            trace_id=request.state.trace_id,
        ),
    )
