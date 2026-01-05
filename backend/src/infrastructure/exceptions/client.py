"""
HTTP client-related infrastructure exceptions.

These are internal exceptions for external API communication failures.
"""


class ClientException(Exception):
    """Base exception for HTTP client operations."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class HTTPClientError(ClientException):
    """Raised when an HTTP request fails."""

    def __init__(
        self,
        url: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ) -> None:
        message = f"HTTP request failed: {url}"
        if status_code:
            message += f" (status: {status_code})"
        super().__init__(message=message, original_error=original_error)
        self.url = url
        self.status_code = status_code


class ClientTimeoutError(ClientException):
    """Raised when an HTTP request times out."""

    def __init__(self, url: str, timeout: float) -> None:
        super().__init__(message=f"Request timed out after {timeout}s: {url}")
        self.url = url
        self.timeout = timeout


class RateLimitError(ClientException):
    """Raised when rate limit is exceeded."""

    def __init__(self, url: str, retry_after: int | None = None) -> None:
        message = f"Rate limit exceeded: {url}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message=message)
        self.url = url
        self.retry_after = retry_after


class ExternalAPIError(ClientException):
    """Raised when an external API returns an error response."""

    def __init__(self, api_name: str, error_message: str) -> None:
        super().__init__(message=f"{api_name} API error: {error_message}")
        self.api_name = api_name
        self.error_message = error_message
