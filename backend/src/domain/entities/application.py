"""
FDA Application Domain Entity.

FDA drug application submissions (NDA, ANDA, BLA).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class FDAApplication:
    """FDA drug application submission (NDA, ANDA, BLA)."""

    key: str
    application_number: str
    submission_type: str | None = None
    submission_number: str | None = None
    submission_status: str | None = None
    submission_status_date: str | None = None
    review_priority: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "application_number": self.application_number,
            "submission_type": self.submission_type,
            "submission_number": self.submission_number,
            "submission_status": self.submission_status,
            "submission_status_date": self.submission_status_date,
            "review_priority": self.review_priority,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            application_number=data.get("application_number", ""),
            submission_type=data.get("submission_type"),
            submission_number=data.get("submission_number"),
            submission_status=data.get("submission_status"),
            submission_status_date=data.get("submission_status_date"),
            review_priority=data.get("review_priority"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
