"""
Interaction Domain Entity.

Drug-drug interaction from RxNorm.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class Interaction:
    """Drug-drug interaction."""

    key: str
    severity: str | None = None
    description: str | None = None
    source_drug_rxcui: str | None = None
    source_drug_name: str | None = None
    target_drug_rxcui: str | None = None
    target_drug_name: str | None = None
    source_api: str = "rxnorm"
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "severity": self.severity,
            "description": self.description,
            "source_drug_rxcui": self.source_drug_rxcui,
            "source_drug_name": self.source_drug_name,
            "target_drug_rxcui": self.target_drug_rxcui,
            "target_drug_name": self.target_drug_name,
            "source_api": self.source_api,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            severity=data.get("severity"),
            description=data.get("description"),
            source_drug_rxcui=data.get("source_drug_rxcui"),
            source_drug_name=data.get("source_drug_name"),
            target_drug_rxcui=data.get("target_drug_rxcui"),
            target_drug_name=data.get("target_drug_name"),
            source_api=data.get("source_api", "rxnorm"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
