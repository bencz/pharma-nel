"""
Drug Domain Entity.

Main drug entity for the pharmaceutical knowledge graph.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class Drug:
    """
    Drug domain entity.

    Used for business logic AND persisted to ArangoDB.
    """

    key: str
    application_number: str | None = None
    brand_names: list[str] = field(default_factory=list)
    generic_names: list[str] = field(default_factory=list)
    ndc_codes: list[str] = field(default_factory=list)
    rxcui: list[str] = field(default_factory=list)
    spl_id: list[str] = field(default_factory=list)
    sponsor_name: str | None = None
    drug_type: str | None = None
    source: str = "api"
    is_enriched: bool = False
    is_alias: bool = False
    enriched_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def has_substance(self, _substance_name: str) -> bool:
        """Check if drug contains a substance by name."""
        return False

    def is_generic(self) -> bool:
        """Check if drug is a generic (ANDA application)."""
        if self.application_number:
            return self.application_number.startswith("ANDA")
        return False

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "application_number": self.application_number,
            "brand_names": self.brand_names,
            "generic_names": self.generic_names,
            "ndc_codes": self.ndc_codes,
            "rxcui": self.rxcui,
            "spl_id": self.spl_id,
            "sponsor_name": self.sponsor_name,
            "type": self.drug_type,
            "source": self.source,
            "is_enriched": self.is_enriched,
            "is_alias": self.is_alias,
            "enriched_at": self.enriched_at,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Drug":
        return cls(
            key=data.get("_key", data.get("key", "")),
            application_number=data.get("application_number"),
            brand_names=data.get("brand_names", []),
            generic_names=data.get("generic_names", []),
            ndc_codes=data.get("ndc_codes", []),
            rxcui=data.get("rxcui", []),
            spl_id=data.get("spl_id", []),
            sponsor_name=data.get("sponsor_name"),
            drug_type=data.get("type"),
            source=data.get("source", "api"),
            is_enriched=data.get("is_enriched", False),
            is_alias=data.get("is_alias", False),
            enriched_at=data.get("enriched_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
