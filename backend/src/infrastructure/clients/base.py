"""
Base HTTP Client with connection pooling and retry logic.

All external API clients inherit from this base class.
"""

import asyncio
from typing import Any

import httpx

from src.infrastructure.exceptions.client import (
    ClientTimeoutError,
    HTTPClientError,
    RateLimitError,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class BaseHTTPClient:
    """Base HTTP client with connection pooling, retry logic, and structured logging."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verify_ssl: bool = True,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._verify_ssl = verify_ssl
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout),
                verify=self._verify_ssl,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                ),
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute HTTP request with retry logic."""
        client = await self._get_client()
        url = path

        for attempt in range(self._max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self._retry_delay * (attempt + 1)))
                    logger.warning(
                        "rate_limit_hit",
                        url=url,
                        retry_after=retry_after,
                        attempt=attempt + 1,
                    )
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(url=str(response.url), retry_after=retry_after)

                return response

            except httpx.TimeoutException:
                logger.warning(
                    "request_timeout",
                    url=url,
                    timeout=self._timeout,
                    attempt=attempt + 1,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise ClientTimeoutError(url=url, timeout=self._timeout)

            except httpx.RequestError as e:
                logger.warning(
                    "request_error",
                    url=url,
                    error=str(e),
                    attempt=attempt + 1,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise HTTPClientError(url=url, original_error=e)

        raise HTTPClientError(url=url)

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("POST", path, params=params, json=json, headers=headers)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseHTTPClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
