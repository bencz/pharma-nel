"""
Substance Domain Entity.

Active pharmaceutical ingredient with chemical data.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class Substance:
    """Active pharmaceutical ingredient with chemical data."""

    key: str
    name: str
    unii: str | None = None
    rxcui: str | None = None
    formula: str | None = None
    molecular_weight: float | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchi_key: str | None = None
    cas_number: str | None = None
    pubchem_id: str | None = None
    substance_class: str | None = None
    stereochemistry: str | None = None
    is_enriched: bool = False
    enriched_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "name": self.name,
            "unii": self.unii,
            "rxcui": self.rxcui,
            "formula": self.formula,
            "molecular_weight": self.molecular_weight,
            "smiles": self.smiles,
            "inchi": self.inchi,
            "inchi_key": self.inchi_key,
            "cas_number": self.cas_number,
            "pubchem_id": self.pubchem_id,
            "substance_class": self.substance_class,
            "stereochemistry": self.stereochemistry,
            "is_enriched": self.is_enriched,
            "enriched_at": self.enriched_at,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            name=data.get("name", ""),
            unii=data.get("unii"),
            rxcui=data.get("rxcui"),
            formula=data.get("formula"),
            molecular_weight=data.get("molecular_weight"),
            smiles=data.get("smiles"),
            inchi=data.get("inchi"),
            inchi_key=data.get("inchi_key"),
            cas_number=data.get("cas_number"),
            pubchem_id=data.get("pubchem_id"),
            substance_class=data.get("substance_class"),
            stereochemistry=data.get("stereochemistry"),
            is_enriched=data.get("is_enriched", False),
            enriched_at=data.get("enriched_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
