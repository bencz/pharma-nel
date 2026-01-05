"""
Profile endpoint response schemas.
"""

from pydantic import BaseModel, Field

from src.api.schemas.base import BaseResponse


class ProfileLocation(BaseModel):
    """Profile location information."""

    city: str | None = Field(default=None, description="City")
    state: str | None = Field(default=None, description="State/Province")
    country: str | None = Field(default=None, description="Country")


class ProfileInfo(BaseModel):
    """Basic profile information."""

    key: str = Field(..., description="Profile key")
    full_name: str | None = Field(default=None, description="Full name")
    credentials: list[str] = Field(default_factory=list, description="Professional credentials")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    linkedin: str | None = Field(default=None, description="LinkedIn URL")
    location: ProfileLocation | None = Field(default=None, description="Location")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")


class ProfileExtraction(BaseModel):
    """Extraction summary for frontend display."""

    key: str = Field(..., description="Extraction key - use GET /extract/{key} for details")
    filename: str | None = Field(default=None, description="Original filename")
    status: str | None = Field(default=None, description="Extraction status")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    doc_type: str | None = Field(default=None, description="Document type")
    therapeutic_areas: list[str] = Field(default_factory=list, description="Therapeutic areas")
    total_entities: int = Field(default=0, description="Total entities extracted")
    avg_confidence: int = Field(default=0, description="Average confidence score")


class SubstanceDrug(BaseModel):
    """Drug related to a substance."""

    key: str = Field(..., description="Drug key")
    brand_names: list[str] = Field(default_factory=list, description="Brand names")
    generic_names: list[str] = Field(default_factory=list, description="Generic names")
    sponsor_name: str | None = Field(default=None, description="Sponsor/manufacturer")
    application_number: str | None = Field(default=None, description="FDA application number")


class SubstanceRoute(BaseModel):
    """Administration route for a substance."""

    key: str = Field(..., description="Route key")
    name: str | None = Field(default=None, description="Route name (e.g., ORAL, INTRAVENOUS)")


class SubstancePharmClass(BaseModel):
    """Pharmacological class for a substance."""

    key: str = Field(..., description="Pharm class key")
    name: str | None = Field(default=None, description="Class name")
    class_type: str | None = Field(default=None, description="Class type (EPC, MoA, PE, CS)")


class SubstanceDosageForm(BaseModel):
    """Dosage form for a substance."""

    key: str = Field(..., description="Dosage form key")
    name: str | None = Field(default=None, description="Dosage form (e.g., TABLET, CAPSULE)")


class SubstanceManufacturer(BaseModel):
    """Manufacturer of drugs containing a substance."""

    key: str = Field(..., description="Manufacturer key")
    name: str | None = Field(default=None, description="Manufacturer name")


class ProfileSubstance(BaseModel):
    """Substance the profile is interested in."""

    key: str = Field(..., description="Substance key - use GET /entity/{key} for full details")
    name: str | None = Field(default=None, description="Substance name")
    unii: str | None = Field(default=None, description="UNII identifier")
    rxcui: str | None = Field(default=None, description="RxNorm CUI")
    is_enriched: bool = Field(default=False, description="Whether substance has FDA data")
    drugs: list[SubstanceDrug] = Field(default_factory=list, description="Related drugs")
    routes: list[SubstanceRoute] = Field(default_factory=list, description="Administration routes")
    dosage_forms: list[SubstanceDosageForm] = Field(default_factory=list, description="Dosage forms")
    pharm_classes: list[SubstancePharmClass] = Field(default_factory=list, description="Pharmacological classes")
    manufacturers: list[SubstanceManufacturer] = Field(default_factory=list, description="Manufacturers")
    drug_count: int = Field(default=0, description="Number of related drugs")


class ProfileStats(BaseModel):
    """Profile statistics."""

    total_extractions: int = Field(default=0, description="Total extractions")
    total_substances: int = Field(default=0, description="Total substances of interest")


class ProfileDetailData(BaseModel):
    """Profile details with related entities."""

    profile: ProfileInfo = Field(..., description="Profile information")
    extractions: list[ProfileExtraction] = Field(default_factory=list, description="Extraction summaries")
    substances: list[ProfileSubstance] = Field(default_factory=list, description="Substances of interest")
    stats: ProfileStats = Field(default_factory=ProfileStats, description="Summary statistics")


class ProfileDetailResponse(BaseResponse[ProfileDetailData]):
    """Response for GET /profile/{profile_id} endpoint."""

    pass


class ProfileListItem(BaseModel):
    """Profile summary for list view."""

    key: str = Field(..., description="Profile key")
    full_name: str | None = Field(default=None, description="Full name")
    credentials: list[str] = Field(default_factory=list, description="Professional credentials")
    email: str | None = Field(default=None, description="Email address")
    linkedin: str | None = Field(default=None, description="LinkedIn URL")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")
    extraction_count: int = Field(default=0, description="Number of extractions")
    substance_count: int = Field(default=0, description="Number of substances of interest")


class ProfileListData(BaseModel):
    """Data for profile list response."""

    profiles: list[ProfileListItem] = Field(..., description="List of profiles")
    count: int = Field(..., description="Number of profiles returned")


class ProfileListResponse(BaseResponse[ProfileListData]):
    """Response for GET /profiles endpoint."""

    pass
