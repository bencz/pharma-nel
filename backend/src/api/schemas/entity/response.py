"""
Entity endpoint response schemas.

Substance-centric model: /entity/{id} returns substance with all related data.
"""

from pydantic import BaseModel, Field

from src.api.schemas.base import BaseResponse


class PharmClassInfo(BaseModel):
    """Pharmacological class information."""

    key: str
    name: str
    class_type: str | None = None


class ManufacturerInfo(BaseModel):
    """Manufacturer information."""

    key: str
    name: str


class RouteInfo(BaseModel):
    """Administration route information."""

    key: str
    name: str


class DosageFormInfo(BaseModel):
    """Dosage form information."""

    key: str
    name: str


class ProductInfo(BaseModel):
    """Drug product information (NDC packaging)."""

    key: str
    product_number: str | None = None
    package_ndc: str | None = None
    brand_name: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    marketing_status: str | None = None
    description: str | None = None


class FDAApplicationInfo(BaseModel):
    """FDA application submission information."""

    key: str
    application_number: str
    submission_type: str | None = None
    submission_number: str | None = None
    submission_status: str | None = None
    submission_status_date: str | None = None
    review_priority: str | None = None


class DrugLabelInfo(BaseModel):
    """Drug label/package insert information (complete)."""

    key: str
    spl_id: str | None = None
    set_id: str | None = None
    version: str | None = None
    effective_time: str | None = None
    description: str | None = None
    clinical_pharmacology: str | None = None
    mechanism_of_action: str | None = None
    indications_and_usage: str | None = None
    dosage_and_administration: str | None = None
    contraindications: str | None = None
    warnings_and_cautions: str | None = None
    boxed_warning: str | None = None
    adverse_reactions: str | None = None
    drug_interactions: str | None = None


class InteractionInfo(BaseModel):
    """Drug-drug interaction information."""

    key: str
    severity: str | None = None
    description: str | None = None
    source_drug_rxcui: str | None = None
    source_drug_name: str | None = None
    target_drug_rxcui: str | None = None
    target_drug_name: str | None = None


class ReactionInfo(BaseModel):
    """Adverse reaction information."""

    key: str
    name: str
    meddra_version: str | None = None


class DrugInfo(BaseModel):
    """Drug (commercial product) information."""

    key: str
    application_number: str | None = None
    brand_names: list[str] = Field(default_factory=list)
    generic_names: list[str] = Field(default_factory=list)
    ndc_codes: list[str] = Field(default_factory=list)
    rxcui: list[str] = Field(default_factory=list)
    spl_id: list[str] = Field(default_factory=list)
    sponsor_name: str | None = None
    drug_type: str | None = None
    source: str = "api"
    is_enriched: bool = False


class SubstanceProfileData(BaseModel):
    """Complete substance profile with ALL related data from the knowledge graph."""

    key: str = Field(..., description="Substance unique key")
    name: str = Field(..., description="Substance name")
    unii: str | None = Field(default=None, description="FDA UNII identifier")
    rxcui: str | None = Field(default=None, description="RxNorm CUI")
    cas_number: str | None = Field(default=None, description="CAS Registry Number")
    formula: str | None = Field(default=None, description="Molecular formula")
    molecular_weight: float | None = Field(default=None, description="Molecular weight")
    smiles: str | None = Field(default=None, description="SMILES notation")
    inchi: str | None = Field(default=None, description="InChI identifier")
    inchi_key: str | None = Field(default=None, description="InChI key")
    pubchem_id: str | None = Field(default=None, description="PubChem compound ID")
    substance_class: str | None = Field(default=None, description="Substance classification")
    stereochemistry: str | None = Field(default=None, description="Stereochemistry information")
    is_enriched: bool = Field(default=False, description="Whether substance has been enriched")
    enriched_at: str | None = Field(default=None, description="When substance was enriched")

    drugs: list[DrugInfo] = Field(default_factory=list, description="Commercial drug products containing this substance")
    pharm_classes: list[PharmClassInfo] = Field(default_factory=list, description="Pharmacological classes")
    manufacturers: list[ManufacturerInfo] = Field(default_factory=list, description="Manufacturers")
    routes: list[RouteInfo] = Field(default_factory=list, description="Administration routes")
    dosage_forms: list[DosageFormInfo] = Field(default_factory=list, description="Dosage forms")
    products: list[ProductInfo] = Field(default_factory=list, description="NDC products/packages")
    applications: list[FDAApplicationInfo] = Field(default_factory=list, description="FDA applications")
    labels: list[DrugLabelInfo] = Field(default_factory=list, description="Drug labels/package inserts")
    interactions: list[InteractionInfo] = Field(default_factory=list, description="Drug-drug interactions")
    reactions: list[ReactionInfo] = Field(default_factory=list, description="Adverse reactions")


class SubstanceProfileResponse(BaseResponse[SubstanceProfileData]):
    """Response for GET /entity/{id} endpoint - substance-centric."""

    pass


class SubstanceResponse(BaseModel):
    """Substance/ingredient information (simplified)."""

    key: str
    name: str
    unii: str | None = None
    rxcui: str | None = None
    formula: str | None = None
    molecular_weight: float | None = None
    smiles: str | None = None
    cas_number: str | None = None
    substance_class: str | None = None


class DrugLabelResponse(BaseModel):
    """Drug label/package insert information."""

    spl_id: str | None = None
    description: str | None = None
    indications_and_usage: str | None = None
    dosage_and_administration: str | None = None
    contraindications: str | None = None
    warnings_and_cautions: str | None = None
    adverse_reactions: str | None = None
    drug_interactions: str | None = None
    mechanism_of_action: str | None = None


class EntityProfileData(BaseModel):
    """Complete entity profile data (drug-centric, for backwards compatibility)."""

    key: str = Field(..., description="Entity unique key")
    application_number: str | None = Field(default=None, description="FDA application number")
    brand_names: list[str] = Field(default_factory=list, description="Brand/trade names")
    generic_names: list[str] = Field(default_factory=list, description="Generic/INN names")
    ndc_codes: list[str] = Field(default_factory=list, description="NDC codes")
    rxcui: list[str] = Field(default_factory=list, description="RxNorm CUI identifiers")
    sponsor_name: str | None = Field(default=None, description="Sponsor/manufacturer name")
    drug_type: str | None = Field(default=None, description="Drug type (NDA, ANDA, BLA)")
    source: str = Field(default="api", description="Data source")
    is_enriched: bool = Field(default=False, description="Whether entity has been enriched")

    substances: list[SubstanceResponse] = Field(default_factory=list, description="Active ingredients")
    label: DrugLabelResponse | None = Field(default=None, description="Drug label information")


class EntityProfileResponse(BaseResponse[EntityProfileData]):
    """Response for GET /entity/{id} endpoint."""

    pass


class EntitySearchResult(BaseModel):
    """Single search result."""

    key: str
    name: str
    type: str
    score: float | None = None


class EntitySearchResponse(BaseResponse[list[EntitySearchResult]]):
    """Response for entity search."""

    pass
