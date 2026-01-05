"""
Extract endpoint response schemas.
"""


from pydantic import BaseModel, Field

from src.api.schemas.base import BaseResponse


class NELLinkResponse(BaseModel):
    """NEL link information."""

    linked_to: str
    relationship: str
    link_confidence: int
    source: str | None = None


class ExtractedEntityResponse(BaseModel):
    """A single extracted entity."""

    name: str = Field(..., description="Entity name as found in text")
    type: str = Field(..., description="Entity type: BRAND, GENERIC, CODE, INGREDIENT")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    context: str | None = Field(default=None, alias="ctx", description="Surrounding context")
    status: str = Field(..., description="NER_ONLY or NEL")
    nel: NELLinkResponse | None = Field(default=None, description="NEL linking info if status=NEL")


class QualityCountsResponse(BaseModel):
    """Confidence level counts."""

    total: int = 0
    high: int = 0
    med: int = 0
    low: int = 0


class NERNELCountsResponse(BaseModel):
    """NER vs NEL counts."""

    ner_only: int = 0
    nel: int = 0


class AmbiguousEntityResponse(BaseModel):
    """An ambiguous entity."""

    text: str
    reason: str


class ExtractionQualityResponse(BaseModel):
    """Quality metrics."""

    completeness: int = Field(..., ge=0, le=100)
    avg_confidence: int = Field(..., ge=0, le=100)
    counts: QualityCountsResponse
    ner_nel_counts: NERNELCountsResponse
    ambiguous: list[AmbiguousEntityResponse] = Field(default_factory=list)
    maybe_missed: list[str] = Field(default_factory=list)
    notes: str | None = None


class ValidationResponse(BaseModel):
    """Validation results."""

    passed: bool
    issues: list[str] = Field(default_factory=list)
    checks_performed: dict[str, bool] = Field(default_factory=dict)


class MetaResponse(BaseModel):
    """Extraction metadata."""

    doc_type: str | None = None
    therapeutic_areas: list[str] = Field(default_factory=list)
    drug_density: str = "LOW"
    total_entities: int = 0


class ExtractionDataResponse(BaseModel):
    """Extraction result data."""

    entities: list[ExtractedEntityResponse]
    quality: ExtractionQualityResponse
    validation: ValidationResponse
    meta: MetaResponse
    model_used: str | None = None
    tokens_used: int = 0


class ExtractionResponse(BaseResponse[ExtractionDataResponse]):
    """Response for extraction endpoint."""

    pass


class SubstanceReference(BaseModel):
    """Reference to an enriched substance in the database."""

    name: str = Field(..., description="Substance name as extracted")
    substance_id: str = Field(..., description="Substance ID in ArangoDB")
    url: str = Field(..., description="URL to query substance details")


class ProfileLocationResponse(BaseModel):
    """Location information."""

    city: str | None = None
    state: str | None = None
    country: str | None = None


class ProfileInfoResponse(BaseModel):
    """Profile information extracted from document."""

    profile_id: str = Field(..., description="Profile ID in ArangoDB")
    full_name: str | None = None
    credentials: list[str] = Field(default_factory=list)
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    location: ProfileLocationResponse | None = None


class EntityNELResponse(BaseModel):
    """Simple entity with NEL link."""

    name: str = Field(..., description="Entity name as found in text")
    type: str = Field(..., description="Entity type: BRAND, GENERIC, CODE, INGREDIENT")
    linked_to: str | None = Field(default=None, description="NEL linked entity name")
    relationship: str | None = Field(default=None, description="NEL relationship type")
    substance_id: str | None = Field(default=None, description="Enriched substance ID if available")
    url: str | None = Field(default=None, description="URL to query substance details")


class ProfileResponse(BaseModel):
    """Profile information in extract response."""

    id: str = Field(..., description="Profile GUID")
    full_name: str | None = None
    credentials: list[str] = Field(default_factory=list)
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    location: ProfileLocationResponse | None = None


class ExtractAndEnrichDataResponse(BaseModel):
    """Simplified extraction and enrichment result."""

    extraction_id: str = Field(..., description="Extraction document ID (file_hash)")
    profile: ProfileResponse | None = Field(default=None, description="Profile if personal info found")
    entities: list[EntityNELResponse] = Field(..., description="Entities with NEL links")


class ExtractAndEnrichResponse(BaseResponse[ExtractAndEnrichDataResponse]):
    """Response for extract and enrich endpoint."""

    pass
