"""
Extraction list endpoint response schemas.
"""

from pydantic import BaseModel, Field

from src.api.schemas.base import BaseResponse


class ExtractionProfileSummary(BaseModel):
    """Profile summary for extraction list."""

    key: str = Field(..., description="Profile key")
    full_name: str | None = Field(default=None, description="Full name")
    credentials: list[str] = Field(default_factory=list, description="Professional credentials")
    email: str | None = Field(default=None, description="Email address")


class ExtractionListItem(BaseModel):
    """Single extraction item in list response."""

    key: str = Field(..., description="Extraction key (file_hash)")
    file_hash: str | None = Field(default=None, description="SHA256 hash of source file")
    filename: str | None = Field(default=None, description="Original filename")
    status: str | None = Field(default=None, description="Extraction status")
    created_at: str | None = Field(default=None, description="ISO timestamp of extraction")
    doc_type: str | None = Field(default=None, description="Document type (resume, clinical, etc)")
    therapeutic_areas: list[str] = Field(default_factory=list, description="Therapeutic areas found")
    drug_density: str | None = Field(default=None, description="Drug mention density: LOW, MED, HIGH")
    total_entities: int = Field(default=0, description="Total entities extracted")
    avg_confidence: int = Field(default=0, description="Average confidence score 0-100")
    profile: ExtractionProfileSummary | None = Field(default=None, description="Linked profile if available")


class ExtractionListDataResponse(BaseModel):
    """Data payload for extraction list response."""

    extractions: list[ExtractionListItem] = Field(..., description="List of extractions")
    count: int = Field(..., description="Number of extractions returned")


class ExtractionListResponse(BaseResponse[ExtractionListDataResponse]):
    """Response for GET /extractions endpoint."""

    pass
