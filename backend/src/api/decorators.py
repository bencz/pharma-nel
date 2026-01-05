"""
API Decorators.

Decorators for configuring route behavior, including error handling.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.routing import APIRoute

ERROR_MESSAGE_ATTR = "_error_message"

DEFAULT_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."


def error_message(message: str) -> Callable:
    """
    Decorator to configure a custom error message for internal errors on a route.

    This message is shown to users when an unexpected exception occurs,
    instead of exposing internal error details.

    Usage:
        @router.post("/extract")
        @error_message("An error occurred while processing your document.")
        async def extract_entities(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        setattr(func, ERROR_MESSAGE_ATTR, message)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        setattr(wrapper, ERROR_MESSAGE_ATTR, message)
        return wrapper

    return decorator


def get_error_message(func: Callable) -> str:
    """Get the configured error message for a route function."""
    return getattr(func, ERROR_MESSAGE_ATTR, DEFAULT_ERROR_MESSAGE)


def get_safe_error_message(request: Request) -> str:
    """
    Get a safe, user-friendly error message from the route's @error_message decorator.

    This prevents internal error details from being exposed to users.
    The message is configured per-route using the @error_message decorator.
    """
    route = request.scope.get("route")

    if route and isinstance(route, APIRoute) and route.endpoint:
        return get_error_message(route.endpoint)

    return DEFAULT_ERROR_MESSAGE
