"""
Request Logging Middleware.

Handles:
- Trace ID generation/propagation
- Request context setup
- Request/Response logging
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.logging import (
    clear_context,
    get_logger,
    set_request_context,
    set_trace_id,
)

logger = get_logger(__name__)

TRACE_ID_HEADER = "X-Trace-ID"
REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and trace ID propagation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        set_trace_id(trace_id)
        set_request_context({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
        })

        start_time = time.perf_counter()

        logger.info(
            "request_started",
            query_params=dict(request.query_params),
            user_agent=request.headers.get("user-agent"),
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers[TRACE_ID_HEADER] = trace_id
        response.headers[REQUEST_ID_HEADER] = request_id

        clear_context()

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
