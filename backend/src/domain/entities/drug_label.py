"""
DrugLabel Domain Entity.

Drug labeling/package insert information.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class DrugLabel:
    """Drug label/package insert."""

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
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "spl_id": self.spl_id,
            "set_id": self.set_id,
            "version": self.version,
            "effective_time": self.effective_time,
            "description": self.description,
            "clinical_pharmacology": self.clinical_pharmacology,
            "mechanism_of_action": self.mechanism_of_action,
            "indications_and_usage": self.indications_and_usage,
            "dosage_and_administration": self.dosage_and_administration,
            "contraindications": self.contraindications,
            "warnings_and_cautions": self.warnings_and_cautions,
            "boxed_warning": self.boxed_warning,
            "adverse_reactions": self.adverse_reactions,
            "drug_interactions": self.drug_interactions,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            spl_id=data.get("spl_id"),
            set_id=data.get("set_id"),
            version=data.get("version"),
            effective_time=data.get("effective_time"),
            description=data.get("description"),
            clinical_pharmacology=data.get("clinical_pharmacology"),
            mechanism_of_action=data.get("mechanism_of_action"),
            indications_and_usage=data.get("indications_and_usage"),
            dosage_and_administration=data.get("dosage_and_administration"),
            contraindications=data.get("contraindications"),
            warnings_and_cautions=data.get("warnings_and_cautions"),
            boxed_warning=data.get("boxed_warning"),
            adverse_reactions=data.get("adverse_reactions"),
            drug_interactions=data.get("drug_interactions"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
