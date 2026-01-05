"""
Reaction Domain Entity.

Adverse reaction from drug events.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class Reaction:
    """Adverse reaction (MedDRA term)."""

    key: str
    name: str
    meddra_version: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "name": self.name,
            "meddra_version": self.meddra_version,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            name=data.get("name", ""),
            meddra_version=data.get("meddra_version"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
