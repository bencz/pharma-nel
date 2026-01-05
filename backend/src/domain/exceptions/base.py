"""
Base domain exceptions.

All domain exceptions inherit from DomainException.
Exception handling happens ONLY at middleware level.
"""

from typing import Any


class DomainException(Exception):
    """Base exception for all domain-level errors."""

    status_code: int = 500
    code: str = "DOMAIN_ERROR"
    message: str = "An unexpected domain error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"
