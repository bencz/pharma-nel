"""
Extraction-related domain exceptions.
"""

from src.domain.exceptions.base import DomainException


class ExtractionFailedError(DomainException):
    """Raised when NER/NEL extraction fails."""

    status_code = 500
    code = "EXTRACTION_FAILED"

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Entity extraction failed: {reason}",
            details={"reason": reason},
        )


class InvalidPDFError(DomainException):
    """Raised when PDF processing fails."""

    status_code = 400
    code = "INVALID_PDF"

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"Invalid or unreadable PDF: {filename}",
            details={"filename": filename, "reason": reason},
        )


class TextTooLongError(DomainException):
    """Raised when input text exceeds maximum allowed length."""

    status_code = 400
    code = "TEXT_TOO_LONG"

    def __init__(self, length: int, max_length: int) -> None:
        super().__init__(
            message=f"Text length ({length}) exceeds maximum allowed ({max_length})",
            details={"length": length, "max_length": max_length},
        )


class NoEntitiesFoundError(DomainException):
    """Raised when no pharmaceutical entities are found in text."""

    status_code = 404
    code = "NO_ENTITIES_FOUND"

    def __init__(self) -> None:
        super().__init__(message="No pharmaceutical entities found in the provided text")


class ExtractionNotFoundError(DomainException):
    """Raised when extraction is not found by ID."""

    status_code = 404
    code = "EXTRACTION_NOT_FOUND"

    def __init__(self, extraction_id: str) -> None:
        super().__init__(
            message=f"Extraction '{extraction_id}' not found",
            details={"extraction_id": extraction_id},
        )
