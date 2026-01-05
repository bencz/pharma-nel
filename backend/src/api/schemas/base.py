"""
Base API schemas.

Provides standardized response format for all API endpoints.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail for API responses."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(default=None, description="Field that caused the error, if applicable")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")


class BaseResponse(BaseModel, Generic[T]):
    """
    Standardized API response wrapper.

    All API responses follow this format for consistency.
    """

    success: bool = Field(..., description="Whether the request was successful")
    data: T | None = Field(default=None, description="Response data on success")
    error: ErrorDetail | None = Field(default=None, description="Error details on failure")

    @classmethod
    def ok(cls, data: T) -> "BaseResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: ErrorDetail) -> "BaseResponse[T]":
        return cls(success=False, error=error)


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def from_total(cls, total: int, page: int, page_size: int) -> "PaginationMeta":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(total=total, page=page, page_size=page_size, total_pages=total_pages)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response wrapper."""

    success: bool = True
    data: list[T] = Field(default_factory=list)
    pagination: PaginationMeta
    error: ErrorDetail | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
