"""
Unit tests for BaseHTTPClient.

Tests retry logic, timeout handling, and rate limiting.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.clients.base import BaseHTTPClient
from src.infrastructure.exceptions.client import (
    ClientTimeoutError,
    HTTPClientError,
    RateLimitError,
)


class TestBaseHTTPClient:
    """Unit tests for BaseHTTPClient."""

    @pytest.fixture
    def client(self) -> BaseHTTPClient:
        return BaseHTTPClient(
            base_url="https://api.example.com",
            timeout=10.0,
            max_retries=3,
            retry_delay=0.01,
            verify_ssl=True,
        )

    async def test_get_client_creates_async_client(self, client: BaseHTTPClient) -> None:
        async_client = await client._get_client()
        assert isinstance(async_client, httpx.AsyncClient)
        await client.close()

    async def test_get_client_reuses_existing(self, client: BaseHTTPClient) -> None:
        client1 = await client._get_client()
        client2 = await client._get_client()
        assert client1 is client2
        await client.close()

    async def test_close_closes_client(self, client: BaseHTTPClient) -> None:
        await client._get_client()
        assert client._client is not None
        await client.close()
        assert client._client is None

    @pytest.mark.parametrize("method", ["GET", "POST"])
    async def test_request_success(self, client: BaseHTTPClient, method: str) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.return_value = mock_response
            mock_get_client.return_value = mock_async_client

            response = await client._request(method, "/test")

            assert response.status_code == 200
            mock_async_client.request.assert_called_once()

    async def test_request_retries_on_timeout(self, client: BaseHTTPClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.side_effect = [
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                mock_response,
            ]
            mock_get_client.return_value = mock_async_client

            response = await client._request("GET", "/test")

            assert response.status_code == 200
            assert mock_async_client.request.call_count == 3

    async def test_request_raises_timeout_after_max_retries(
        self, client: BaseHTTPClient
    ) -> None:
        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.side_effect = httpx.TimeoutException("timeout")
            mock_get_client.return_value = mock_async_client

            with pytest.raises(ClientTimeoutError):
                await client._request("GET", "/test")

            assert mock_async_client.request.call_count == 3

    async def test_request_raises_http_error_after_max_retries(
        self, client: BaseHTTPClient
    ) -> None:
        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.side_effect = httpx.RequestError("connection error")
            mock_get_client.return_value = mock_async_client

            with pytest.raises(HTTPClientError):
                await client._request("GET", "/test")

            assert mock_async_client.request.call_count == 3

    async def test_request_handles_rate_limit(self, client: BaseHTTPClient) -> None:
        mock_rate_limit_response = MagicMock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {"Retry-After": "1"}
        mock_rate_limit_response.url = "https://api.example.com/test"

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.side_effect = [
                mock_rate_limit_response,
                mock_success_response,
            ]
            mock_get_client.return_value = mock_async_client

            response = await client._request("GET", "/test")

            assert response.status_code == 200
            assert mock_async_client.request.call_count == 2

    async def test_request_raises_rate_limit_after_max_retries(
        self, client: BaseHTTPClient
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}
        mock_response.url = "https://api.example.com/test"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_async_client = AsyncMock()
            mock_async_client.request.return_value = mock_response
            mock_get_client.return_value = mock_async_client

            with pytest.raises(RateLimitError):
                await client._request("GET", "/test")

    async def test_get_method(self, client: BaseHTTPClient) -> None:
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = MagicMock(status_code=200)

            await client.get("/test", params={"key": "value"})

            mock_request.assert_called_once_with(
                "GET", "/test", params={"key": "value"}, headers=None
            )

    async def test_post_method(self, client: BaseHTTPClient) -> None:
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = MagicMock(status_code=200)

            await client.post("/test", json={"data": "value"})

            mock_request.assert_called_once_with(
                "POST", "/test", params=None, json={"data": "value"}, headers=None
            )

    async def test_context_manager(self) -> None:
        async with BaseHTTPClient("https://api.example.com") as client:
            assert client._client is not None
        assert client._client is None
