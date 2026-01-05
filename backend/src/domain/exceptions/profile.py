"""
Profile-related domain exceptions.
"""

from src.domain.exceptions.base import DomainException


class ProfileNotFoundError(DomainException):
    """Raised when profile is not found by ID."""

    status_code = 404
    code = "PROFILE_NOT_FOUND"

    def __init__(self, profile_id: str) -> None:
        super().__init__(
            message=f"Profile '{profile_id}' not found",
            details={"profile_id": profile_id},
        )
