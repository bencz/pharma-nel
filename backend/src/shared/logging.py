"""
Structured Logging System with Trace/Correlation ID support.

Features:
- Correlation ID (trace_id) propagation across requests
- Structured JSON logging for production
- Context-aware logging with request metadata
- Async-safe context variables
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

import structlog
from structlog.types import EventDict, Processor

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
request_context_var: ContextVar[dict[str, Any] | None] = ContextVar("request_context", default=None)


def get_trace_id() -> str | None:
    return trace_id_var.get()


def set_trace_id(trace_id: str | None = None) -> str:
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    trace_id_var.set(trace_id)
    return trace_id


def get_request_context() -> dict[str, Any]:
    return request_context_var.get() or {}


def set_request_context(context: dict[str, Any]) -> None:
    request_context_var.set(context)


def clear_context() -> None:
    trace_id_var.set(None)
    request_context_var.set(None)


def add_trace_id(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
    trace_id = get_trace_id()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def add_request_context(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
    context = get_request_context()
    if context:
        event_dict.update(context)
    return event_dict


def add_timestamp(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_service_info(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "pharma-ner"
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    log_file: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON formatted logs (production). If False, colored console output (dev).
        log_file: Optional file path to write logs to.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_timestamp,
        add_service_info,
        add_trace_id,
        add_request_context,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        shared_processors.append(structlog.processors.format_exc_info)
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        for handler in handlers:
            logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = False

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
