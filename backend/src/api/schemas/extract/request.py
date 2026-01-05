"""
Extract endpoint request schemas.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ExtractMode(str, Enum):
    """Extraction mode."""

    TEXT = "text"
    PDF_TEXT = "pdf_text"
    PDF_NATIVE = "pdf_native"


class ExtractRequest(BaseModel):
    """Request for text extraction."""

    text: str = Field(..., min_length=10, max_length=100000, description="Text to extract entities from")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=8000, ge=1000, le=16000, description="Max tokens for response")

    model_config = {"json_schema_extra": {"example": {"text": "The patient was prescribed Aspirin 81mg and Lipitor 20mg daily.", "temperature": 0.1, "max_tokens": 8000}}}
