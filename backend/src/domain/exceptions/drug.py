"""
Drug-related domain exceptions.
"""

from src.domain.exceptions.base import DomainException


class DrugNotFoundError(DomainException):
    """Raised when a drug is not found in the knowledge graph."""

    status_code = 404
    code = "DRUG_NOT_FOUND"

    def __init__(self, drug_id: str) -> None:
        super().__init__(
            message=f"Drug '{drug_id}' not found",
            details={"drug_id": drug_id},
        )


class SubstanceNotFoundError(DomainException):
    """Raised when a substance is not found in the knowledge graph."""

    status_code = 404
    code = "SUBSTANCE_NOT_FOUND"

    def __init__(self, substance_id: str) -> None:
        super().__init__(
            message=f"Substance '{substance_id}' not found",
            details={"substance_id": substance_id},
        )


class InvalidDrugIdentifierError(DomainException):
    """Raised when a drug identifier format is invalid."""

    status_code = 400
    code = "INVALID_DRUG_IDENTIFIER"

    def __init__(self, identifier: str, identifier_type: str) -> None:
        super().__init__(
            message=f"Invalid {identifier_type} format: '{identifier}'",
            details={"identifier": identifier, "identifier_type": identifier_type},
        )


class DrugEnrichmentError(DomainException):
    """Raised when drug enrichment from external APIs fails."""

    status_code = 502
    code = "DRUG_ENRICHMENT_FAILED"

    def __init__(self, drug_name: str, source: str, reason: str | None = None) -> None:
        super().__init__(
            message=f"Failed to enrich drug '{drug_name}' from {source}",
            details={"drug_name": drug_name, "source": source, "reason": reason},
        )
