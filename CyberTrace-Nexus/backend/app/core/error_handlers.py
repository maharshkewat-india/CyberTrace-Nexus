"""
error_handlers.py - Consistent error response format for FastAPI.

All endpoints return errors in the same format:

{
  "error_code": "error_type",
  "detail": "Human-readable error message",
  "timestamp": "ISO 8601 UTC timestamp"
}
"""

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)


def _is_sensitive_error(exception: BaseException) -> bool:
    msg = str(exception).lower()
    return any(k in msg for k in ("sql", "traceback", "file \"", "home/", "user\\"))


def _generate_error_code(exception: BaseException) -> str:
    if isinstance(exception, ValidationError):
        return "VALIDATION_ERROR"
    if isinstance(exception, StarletteHTTPException):
        code = exception.status_code
        if code == 404: return "NOT_FOUND"
        if code == 401: return "UNAUTHORIZED"
        if code == 403: return "FORBIDDEN"
        if code == 409: return "CONFLICT"
        if code == 422: return "VALIDATION_ERROR"
        if code >= 500: return "SERVER_ERROR"
        return "CLIENT_ERROR"
    exc_type = type(exception).__name__
    if "ValueError" in exc_type: return "VALUE_ERROR"
    if "PermissionError" in exc_type: return "PERMISSION_ERROR"
    if "FileNotFound" in exc_type: return "FILE_NOT_FOUND"
    if "Integrity" in exc_type or "Unique" in str(exception): return "DUPLICATE_ERROR"
    return "ERROR"


def _get_error_detail(exception: BaseException) -> str:
    if isinstance(exception, StarletteHTTPException):
        return exception.detail if exception.detail else str(exception)
    if isinstance(exception, ValidationError):
        if exception.errors():
            return exception.errors()[0]["msg"]
        return "Validation error"
    msg = str(exception).split("\n")[0].split(";")[0]
    if "UNIQUE constraint failed" in msg or "UNIQUE constraint" in msg:
        return "A record with this value already exists"
    if "foreign key constraint" in msg.lower():
        return "Referenced record not found"
    if "file" in msg.lower() and "not found" in msg.lower():
        return "File not found"
    if "permission" in msg.lower():
        return "Permission denied"
    if "authentication" in msg.lower():
        return "Authentication failed"
    if "SQLITE_CONSTRAINT" in msg:
        return "Database constraint violation"
    return msg if msg else f"{type(exception).__name__}: An error occurred"


async def create_error_response(request: Request, exception: BaseException) -> JSONResponse:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path = getattr(request, "url", None)
    path_str = str(path.path) if path else "unknown"
    method = getattr(request, "method", "UNKNOWN")
    if _is_sensitive_error(exception):
        logger.warning(f"Error on {method} {path_str}: {type(exception).__name__}")
    else:
        logger.error(f"Error on {method} {path_str}: {exception}")
    detail = _get_error_detail(exception)
    error_code = _generate_error_code(exception)
    status_code = 500
    if isinstance(exception, StarletteHTTPException):
        status_code = exception.status_code
    elif isinstance(exception, ValidationError):
        status_code = 422
    return JSONResponse(status_code=status_code, content={
        "error_code": error_code,
        "detail": detail,
        "timestamp": timestamp,
    })


def add_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, create_error_response)
    app.add_exception_handler(StarletteHTTPException, create_error_response)
    app.add_exception_handler(ValidationError, create_error_response)


def log_error(exception: BaseException, request: Any, **kwargs: Any) -> None:
    logger.error(
        f"Error processing {getattr(request, 'method', 'UNKNOWN')}: {type(exception).__name__}: {exception}",
        **kwargs,
    )
