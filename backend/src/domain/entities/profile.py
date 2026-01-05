"""
Profile Domain Entity.

User profile extracted from resume documents.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self


def generate_profile_key(
    email: str | None = None,
    full_name: str | None = None,
    linkedin: str | None = None,
) -> str:
    """
    Generate a deterministic key for profile based on identifying data.

    Priority: email > linkedin > full_name
    Same person = same key (allows deduplication).
    """
    if email:
        data = f"email:{email.lower().strip()}"
    elif linkedin:
        data = f"linkedin:{linkedin.lower().strip()}"
    elif full_name:
        data = f"name:{full_name.lower().strip()}"
    else:
        data = f"unknown:{datetime.now(UTC).isoformat()}"

    return hashlib.md5(data.encode()).hexdigest()[:24]


@dataclass(slots=True)
class ProfileLocation:
    """Location information for a profile."""

    city: str | None = None
    state: str | None = None
    country: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "city": self.city,
            "state": self.state,
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Self | None:
        if not data:
            return None
        return cls(
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
        )


@dataclass(slots=True)
class Profile:
    """
    User profile extracted from resume.

    Stored as a vertex in the knowledge graph.
    Connected to extractions via profile_has_extraction edge.
    """

    key: str
    full_name: str | None = None
    credentials: list[str] = field(default_factory=list)
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    location: ProfileLocation | None = None
    source_extractions: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "full_name": self.full_name,
            "credentials": self.credentials,
            "email": self.email,
            "phone": self.phone,
            "linkedin": self.linkedin,
            "location": self.location.to_dict() if self.location else None,
            "source_extractions": self.source_extractions,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            full_name=data.get("full_name"),
            credentials=data.get("credentials", []),
            email=data.get("email"),
            phone=data.get("phone"),
            linkedin=data.get("linkedin"),
            location=ProfileLocation.from_dict(data.get("location")),
            source_extractions=data.get("source_extractions", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_personal_info(
        cls,
        personal_info: dict[str, Any],
        extraction_key: str | None = None,
    ) -> Self:
        """Create Profile from LLM-extracted personal_info."""
        email = personal_info.get("email")
        full_name = personal_info.get("full_name")
        linkedin = personal_info.get("linkedin")
        key = generate_profile_key(email=email, full_name=full_name, linkedin=linkedin)

        location_data = personal_info.get("location")
        location = ProfileLocation.from_dict(location_data) if location_data else None

        source_extractions = [extraction_key] if extraction_key else []

        return cls(
            key=key,
            full_name=full_name,
            credentials=personal_info.get("credentials", []),
            email=email,
            phone=personal_info.get("phone"),
            linkedin=linkedin,
            location=location,
            source_extractions=source_extractions,
        )

    def merge_with(self, other: "Profile") -> "Profile":
        """
        Merge another profile into this one, preserving existing data.

        Used when the same person appears in multiple extractions.
        """
        merged_credentials = list(set(self.credentials + other.credentials))
        merged_extractions = list(set(self.source_extractions + other.source_extractions))

        return Profile(
            key=self.key,
            full_name=self.full_name or other.full_name,
            credentials=merged_credentials,
            email=self.email or other.email,
            phone=self.phone or other.phone,
            linkedin=self.linkedin or other.linkedin,
            location=self.location or other.location,
            source_extractions=merged_extractions,
            created_at=self.created_at or other.created_at,
        )
