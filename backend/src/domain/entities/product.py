"""
Product Domain Entity.

Drug product with NDC packaging info.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self


@dataclass(slots=True)
class Product:
    """Drug product (specific packaging/formulation)."""

    key: str
    product_number: str | None = None
    package_ndc: str | None = None
    brand_name: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    marketing_status: str | None = None
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        return {
            "_key": self.key,
            "product_number": self.product_number,
            "package_ndc": self.package_ndc,
            "brand_name": self.brand_name,
            "dosage_form": self.dosage_form,
            "route": self.route,
            "marketing_status": self.marketing_status,
            "description": self.description,
            "created_at": self.created_at or now,
            "updated_at": now,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            key=data.get("_key", data.get("key", "")),
            product_number=data.get("product_number"),
            package_ndc=data.get("package_ndc"),
            brand_name=data.get("brand_name"),
            dosage_form=data.get("dosage_form"),
            route=data.get("route"),
            marketing_status=data.get("marketing_status"),
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
