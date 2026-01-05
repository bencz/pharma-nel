"""
Extraction Domain Entities.

Entities related to NER/NEL extraction results.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Self


class EntityType(str, Enum):
    """Type of pharmaceutical entity."""

    BRAND = "BRAND"
    GENERIC = "GENERIC"
    CODE = "CODE"
    INGREDIENT = "INGREDIENT"


class EntityStatus(str, Enum):
    """Status of entity recognition/linking."""

    NER_ONLY = "NER_ONLY"
    NEL = "NEL"


class RelationshipType(str, Enum):
    """Type of relationship between entities."""

    BRAND_OF = "brand_of"
    GENERIC_OF = "generic_of"
    SAME_AS = "same_as"
    INGREDIENT_OF = "ingredient_of"
    CONTAINS = "contains"


class DrugDensity(str, Enum):
    """Drug mention density in document."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"

@dataclass(slots=True)
class Location:
    """Location information."""

    city: str | None = None
    state: str | None = None
    country: str | None = None


@dataclass(slots=True)
class PersonalInfo:
    """Personal information extracted from resume."""

    full_name: str | None = None
    credentials: list[str] = field(default_factory=list)
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    location: Location | None = None


@dataclass(slots=True)
class NELLink:
    """Named Entity Linking information."""

    linked_to: str
    relationship: RelationshipType
    link_confidence: int
    source: str | None = None


@dataclass(slots=True)
class ExtractedEntity:
    """A single extracted pharmaceutical entity."""

    name: str
    type: EntityType
    confidence: int
    context: str | None = None
    status: EntityStatus = EntityStatus.NER_ONLY
    nel: NELLink | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.type.value,
            "confidence": self.confidence,
            "ctx": self.context,
            "status": self.status.value,
        }
        if self.nel:
            result["nel"] = {
                "linked_to": self.nel.linked_to,
                "relationship": self.nel.relationship.value,
                "link_confidence": self.nel.link_confidence,
                "source": self.nel.source,
            }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractedEntity":
        nel = None
        if "nel" in data and data["nel"]:
            nel_data = data["nel"]
            nel = NELLink(
                linked_to=nel_data["linked_to"],
                relationship=RelationshipType(nel_data["relationship"]),
                link_confidence=nel_data["link_confidence"],
                source=nel_data.get("source"),
            )

        return cls(
            name=data["name"],
            type=EntityType(data["type"]),
            confidence=data["confidence"],
            context=data.get("ctx"),
            status=EntityStatus(data.get("status", "NER_ONLY")),
            nel=nel,
        )


@dataclass(slots=True)
class QualityCounts:
    """Confidence level counts."""

    total: int = 0
    high: int = 0
    med: int = 0
    low: int = 0


@dataclass(slots=True)
class NERNELCounts:
    """NER vs NEL counts."""

    ner_only: int = 0
    nel: int = 0


@dataclass(slots=True)
class AmbiguousEntity:
    """An ambiguous entity that needs review."""

    text: str
    reason: str


@dataclass(slots=True)
class ExtractionQuality:
    """Quality metrics for extraction."""

    completeness: int = 0
    avg_confidence: int = 0
    counts: QualityCounts = field(default_factory=QualityCounts)
    ner_nel_counts: NERNELCounts = field(default_factory=NERNELCounts)
    ambiguous: list[AmbiguousEntity] = field(default_factory=list)
    maybe_missed: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class ExtractionValidation:
    """Validation results for extraction."""

    passed: bool = False
    issues: list[str] = field(default_factory=list)
    checks_performed: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractionMeta:
    """Metadata about the extraction."""

    doc_type: str | None = None
    therapeutic_areas: list[str] = field(default_factory=list)
    drug_density: DrugDensity = DrugDensity.LOW
    total_entities: int = 0


@dataclass(slots=True)
class ExtractionResult:
    """Complete result of NER/NEL extraction."""

    entities: list[ExtractedEntity] = field(default_factory=list)
    quality: ExtractionQuality = field(default_factory=ExtractionQuality)
    validation: ExtractionValidation = field(default_factory=ExtractionValidation)
    meta: ExtractionMeta = field(default_factory=ExtractionMeta)
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)

    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    model_used: str | None = None
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "quality": {
                "completeness": self.quality.completeness,
                "avg_confidence": self.quality.avg_confidence,
                "counts": {
                    "total": self.quality.counts.total,
                    "high": self.quality.counts.high,
                    "med": self.quality.counts.med,
                    "low": self.quality.counts.low,
                },
                "ner_nel_counts": {
                    "ner_only": self.quality.ner_nel_counts.ner_only,
                    "nel": self.quality.ner_nel_counts.nel,
                },
                "ambiguous": [{"text": a.text, "reason": a.reason} for a in self.quality.ambiguous],
                "maybe_missed": self.quality.maybe_missed,
                "notes": self.quality.notes,
            },
            "validation": {
                "passed": self.validation.passed,
                "issues": self.validation.issues,
                "checks_performed": self.validation.checks_performed,
            },
            "personal_info": {
                "full_name": self.personal_info.full_name,
                "credentials": self.personal_info.credentials,
                "email": self.personal_info.email,
                "phone": self.personal_info.phone,
                "linkedin": self.personal_info.linkedin,
                "location": {
                    "city": self.personal_info.location.city,
                    "state": self.personal_info.location.state,
                    "country": self.personal_info.location.country,
                } if self.personal_info.location else None,
            },
            "meta": {
                "doc_type": self.meta.doc_type,
                "therapeutic_areas": self.meta.therapeutic_areas,
                "drug_density": self.meta.drug_density.value,
                "total_entities": self.meta.total_entities,
            },
        }

    @classmethod
    def from_llm_response(cls, data: dict[str, Any], model: str, tokens: int) -> Self:
        """Create ExtractionResult from LLM JSON response."""
        entities = [ExtractedEntity.from_dict(e) for e in data.get("entities", [])]

        quality_data = data.get("quality", {})
        counts_data = quality_data.get("counts", {})
        ner_nel_data = quality_data.get("ner_nel_counts", {})

        quality = ExtractionQuality(
            completeness=quality_data.get("completeness", 0),
            avg_confidence=quality_data.get("avg_confidence", 0),
            counts=QualityCounts(
                total=counts_data.get("total", len(entities)),
                high=counts_data.get("high", 0),
                med=counts_data.get("med", 0),
                low=counts_data.get("low", 0),
            ),
            ner_nel_counts=NERNELCounts(
                ner_only=ner_nel_data.get("ner_only", 0),
                nel=ner_nel_data.get("nel", 0),
            ),
            ambiguous=[
                AmbiguousEntity(text=a["text"], reason=a["reason"])
                for a in quality_data.get("ambiguous", [])
            ],
            maybe_missed=quality_data.get("maybe_missed", []),
            notes=quality_data.get("notes"),
        )

        validation_data = data.get("validation", {})
        validation = ExtractionValidation(
            passed=validation_data.get("passed", False),
            issues=validation_data.get("issues", []),
            checks_performed=validation_data.get("checks_performed", {}),
        )

        personal_info_data = data.get("personal_info", {})
        location_data = personal_info_data.get("location", {})
        personal_info = PersonalInfo(
            full_name=personal_info_data.get("full_name"),
            credentials=personal_info_data.get("credentials", []),
            email=personal_info_data.get("email"),
            phone=personal_info_data.get("phone"),
            linkedin=personal_info_data.get("linkedin"),
            location=Location(
                city=location_data.get("city"),
                state=location_data.get("state"),
                country=location_data.get("country"),
            ) if location_data else None,
        )

        meta_data = data.get("meta", {})
        meta = ExtractionMeta(
            doc_type=meta_data.get("doc_type"),
            therapeutic_areas=meta_data.get("therapeutic_areas", []),
            drug_density=DrugDensity(meta_data.get("drug_density", "LOW")),
            total_entities=meta_data.get("total_entities", len(entities)),
        )

        return cls(
            entities=entities,
            quality=quality,
            validation=validation,
            meta=meta,
            model_used=model,
            tokens_used=tokens,
            personal_info=personal_info,
        )

    @classmethod
    def from_cached(cls, data: dict[str, Any]) -> Self:
        """Reconstruct ExtractionResult from cached database document."""
        entities = [ExtractedEntity.from_dict(e) for e in data.get("entities", [])]

        quality_data = data.get("quality", {})
        counts_data = quality_data.get("counts", {})
        ner_nel_data = quality_data.get("ner_nel_counts", {})

        quality = ExtractionQuality(
            completeness=quality_data.get("completeness", 0),
            avg_confidence=quality_data.get("avg_confidence", 0),
            counts=QualityCounts(
                total=counts_data.get("total", len(entities)),
                high=counts_data.get("high", 0),
                med=counts_data.get("med", 0),
                low=counts_data.get("low", 0),
            ),
            ner_nel_counts=NERNELCounts(
                ner_only=ner_nel_data.get("ner_only", 0),
                nel=ner_nel_data.get("nel", 0),
            ),
            ambiguous=[
                AmbiguousEntity(text=a["text"], reason=a["reason"])
                for a in quality_data.get("ambiguous", [])
            ],
            maybe_missed=quality_data.get("maybe_missed", []),
            notes=quality_data.get("notes"),
        )

        validation_data = data.get("validation", {})
        validation = ExtractionValidation(
            passed=validation_data.get("passed", False),
            issues=validation_data.get("issues", []),
            checks_performed=validation_data.get("checks_performed", {}),
        )

        meta_data = data.get("meta", {})
        meta = ExtractionMeta(
            doc_type=meta_data.get("doc_type"),
            therapeutic_areas=meta_data.get("therapeutic_areas", []),
            drug_density=DrugDensity(meta_data.get("drug_density", "LOW")),
            total_entities=meta_data.get("total_entities", len(entities)),
        )

        personal_info_data = data.get("personal_info", {})
        location_data = personal_info_data.get("location", {}) if personal_info_data else {}
        personal_info = PersonalInfo(
            full_name=personal_info_data.get("full_name"),
            credentials=personal_info_data.get("credentials", []),
            email=personal_info_data.get("email"),
            phone=personal_info_data.get("phone"),
            linkedin=personal_info_data.get("linkedin"),
            location=Location(
                city=location_data.get("city"),
                state=location_data.get("state"),
                country=location_data.get("country"),
            ) if location_data else None,
        )

        return cls(
            entities=entities,
            quality=quality,
            validation=validation,
            meta=meta,
            personal_info=personal_info,
            model_used=data.get("model_used"),
            tokens_used=data.get("tokens_used", 0),
        )
