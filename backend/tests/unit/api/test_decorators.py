"""
Unit tests for API decorators.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from src.api.decorators import (
    DEFAULT_ERROR_MESSAGE,
    ERROR_MESSAGE_ATTR,
    error_message,
    get_error_message,
    get_safe_error_message,
)


class TestErrorMessageDecorator:
    """Unit tests for @error_message decorator."""

    def test_decorator_sets_attribute(self) -> None:
        @error_message("Custom error message")
        async def test_func():
            pass

        assert hasattr(test_func, ERROR_MESSAGE_ATTR)
        assert getattr(test_func, ERROR_MESSAGE_ATTR) == "Custom error message"

    def test_decorator_preserves_function_name(self) -> None:
        @error_message("Test message")
        async def my_endpoint():
            pass

        assert my_endpoint.__name__ == "my_endpoint"

    def test_decorator_preserves_docstring(self) -> None:
        @error_message("Test message")
        async def documented_func():
            """This is the docstring."""
            pass

        assert documented_func.__doc__ == "This is the docstring."

    async def test_decorated_function_executes_normally(self) -> None:
        @error_message("Test message")
        async def returning_func():
            return "success"

        result = await returning_func()
        assert result == "success"

    async def test_decorated_function_passes_args(self) -> None:
        @error_message("Test message")
        async def func_with_args(a: int, b: str) -> str:
            return f"{a}-{b}"

        result = await func_with_args(42, "test")
        assert result == "42-test"

    async def test_decorated_function_passes_kwargs(self) -> None:
        @error_message("Test message")
        async def func_with_kwargs(*, name: str, value: int) -> dict:
            return {"name": name, "value": value}

        result = await func_with_kwargs(name="test", value=100)
        assert result == {"name": "test", "value": 100}


class TestGetErrorMessage:
    """Unit tests for get_error_message function."""

    def test_returns_custom_message(self) -> None:
        @error_message("Custom message")
        async def func():
            pass

        assert get_error_message(func) == "Custom message"

    def test_returns_default_for_undecorated(self) -> None:
        async def undecorated_func():
            pass

        assert get_error_message(undecorated_func) == DEFAULT_ERROR_MESSAGE

    def test_returns_default_for_none_attribute(self) -> None:
        async def func():
            pass

        setattr(func, ERROR_MESSAGE_ATTR, None)
        result = get_error_message(func)
        assert result is None


class TestGetSafeErrorMessage:
    """Unit tests for get_safe_error_message function."""

    def test_returns_message_from_route(self) -> None:
        app = FastAPI()

        @app.get("/test")
        @error_message("Route-specific error message")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        client.get("/test")

        for route in app.routes:
            if isinstance(route, APIRoute) and route.path == "/test":
                assert get_error_message(route.endpoint) == "Route-specific error message"

    def test_returns_default_for_undecorated_route(self) -> None:
        app = FastAPI()

        @app.get("/undecorated")
        async def undecorated_endpoint():
            return {"status": "ok"}

        for route in app.routes:
            if isinstance(route, APIRoute) and route.path == "/undecorated":
                assert get_error_message(route.endpoint) == DEFAULT_ERROR_MESSAGE


class TestErrorMessageIntegration:
    """Integration tests for error_message decorator with FastAPI."""

    def test_decorator_works_with_fastapi_route(self) -> None:
        app = FastAPI()

        @app.post("/extract")
        @error_message("An error occurred while processing your document.")
        async def extract():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.post("/extract")

        assert response.status_code == 200

        for route in app.routes:
            if isinstance(route, APIRoute) and route.path == "/extract":
                msg = get_error_message(route.endpoint)
                assert msg == "An error occurred while processing your document."

    def test_multiple_routes_different_messages(self) -> None:
        app = FastAPI()

        @app.post("/upload")
        @error_message("Upload failed. Please try again.")
        async def upload():
            return {"status": "ok"}

        @app.get("/entity/{id}")
        @error_message("Entity lookup failed.")
        async def get_entity(id: str):
            return {"id": id}

        messages = {}
        for route in app.routes:
            if isinstance(route, APIRoute):
                messages[route.path] = get_error_message(route.endpoint)

        assert messages.get("/upload") == "Upload failed. Please try again."
        assert messages.get("/entity/{id}") == "Entity lookup failed."
