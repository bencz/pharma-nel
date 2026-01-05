"""
Exception handling tests.
"""

from src.domain.exceptions.base import DomainException
from src.domain.exceptions.drug import DrugNotFoundError, InvalidDrugIdentifierError
from src.domain.exceptions.extraction import ExtractionFailedError, InvalidPDFError


def test_domain_exception_defaults():
    exc = DomainException()
    assert exc.status_code == 500
    assert exc.code == "DOMAIN_ERROR"
    assert exc.message == "An unexpected domain error occurred"
    assert exc.details == {}


def test_domain_exception_custom_message():
    exc = DomainException(message="Custom error", details={"key": "value"})
    assert exc.message == "Custom error"
    assert exc.details == {"key": "value"}


def test_drug_not_found_error():
    exc = DrugNotFoundError(drug_id="aspirin-123")
    assert exc.status_code == 404
    assert exc.code == "DRUG_NOT_FOUND"
    assert "aspirin-123" in exc.message
    assert exc.details["drug_id"] == "aspirin-123"


def test_invalid_drug_identifier_error():
    exc = InvalidDrugIdentifierError(identifier="invalid", identifier_type="UNII")
    assert exc.status_code == 400
    assert exc.code == "INVALID_DRUG_IDENTIFIER"
    assert "UNII" in exc.message


def test_extraction_failed_error():
    exc = ExtractionFailedError(reason="LLM timeout")
    assert exc.status_code == 500
    assert exc.code == "EXTRACTION_FAILED"
    assert "LLM timeout" in exc.message


def test_invalid_pdf_error():
    exc = InvalidPDFError(filename="test.pdf", reason="corrupted")
    assert exc.status_code == 400
    assert exc.code == "INVALID_PDF"
    assert exc.details["filename"] == "test.pdf"
