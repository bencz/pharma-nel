"""
Global Exception Handlers.

THIS IS THE ONLY PLACE WHERE EXCEPTIONS ARE CAUGHT.
All domain and infrastructure exceptions propagate here.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.decorators import get_safe_error_message
from src.api.schemas.base import BaseResponse, ErrorDetail
from src.domain.exceptions.base import DomainException
from src.infrastructure.exceptions.client import ClientException
from src.infrastructure.exceptions.database import DatabaseException
from src.shared.logging import get_logger

logger = get_logger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle domain-level exceptions with appropriate status codes."""
    logger.warning(
        "domain_exception",
        exception_type=exc.__class__.__name__,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponse.fail(
            ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            )
        ).model_dump(),
    )


async def database_exception_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    """Handle database exceptions - log details but return generic message."""
    logger.error(
        "database_exception",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        original_error=str(exc.original_error) if exc.original_error else None,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=BaseResponse.fail(
            ErrorDetail(
                code="DATABASE_ERROR",
                message="An internal database error occurred",
            )
        ).model_dump(),
    )


async def client_exception_handler(request: Request, exc: ClientException) -> JSONResponse:
    """Handle external client exceptions - log details but return generic message."""
    logger.error(
        "client_exception",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        original_error=str(exc.original_error) if exc.original_error else None,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=502,
        content=BaseResponse.fail(
            ErrorDetail(
                code="EXTERNAL_SERVICE_ERROR",
                message="An external service error occurred",
            )
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions - log full details, return safe user message."""
    logger.error(
        "unhandled_exception",
        exception_type=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    safe_message = get_safe_error_message(request)

    return JSONResponse(
        status_code=500,
        content=BaseResponse.fail(
            ErrorDetail(
                code="INTERNAL_ERROR",
                message=safe_message,
            )
        ).model_dump(),
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(DatabaseException, database_exception_handler)
    app.add_exception_handler(ClientException, client_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
