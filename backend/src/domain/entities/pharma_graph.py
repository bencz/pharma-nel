"""
OpenFDA Substance Graph Data Structures.

Contains Edge and SubstanceGraphData for aggregating enrichment results.
The graph schema is defined in OpenFDAGraphRepository.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from src.domain.entities.application import FDAApplication
from src.domain.entities.dosage_form import DosageForm
from src.domain.entities.drug import Drug
from src.domain.entities.drug_label import DrugLabel
from src.domain.entities.interaction import Interaction
from src.domain.entities.manufacturer import Manufacturer
from src.domain.entities.pharm_class import PharmClass
from src.domain.entities.product import Product
from src.domain.entities.reaction import Reaction
from src.domain.entities.route import Route
from src.domain.entities.substance import Substance


def generate_key(*args: Any) -> str | None:
    """Generate a unique key for ArangoDB document."""
    combined = "_".join(str(arg).lower().strip() for arg in args if arg)
    if not combined:
        return None

    clean = re.sub(r"[^a-z0-9_]", "_", combined)
    clean = re.sub(r"_+", "_", clean)
    clean = clean.strip("_")

    if not clean:
        return None

    if clean[0].isdigit():
        clean = "k_" + clean

    if len(clean) > 64:
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    return clean


@dataclass(slots=True)
class Edge:
    """Generic graph edge."""

    from_collection: str
    from_key: str
    to_collection: str
    to_key: str
    edge_collection: str
    properties: dict[str, Any] = field(default_factory=dict)

    def get_unique_id(self) -> str:
        return f"{self.from_collection}/{self.from_key}->{self.to_collection}/{self.to_key}@{self.edge_collection}"

    def to_dict(self) -> dict[str, Any]:
        edge_key = hashlib.md5(
            f"{self.from_collection}/{self.from_key}_{self.to_collection}/{self.to_key}_{self.edge_collection}".encode()
        ).hexdigest()[:16]

        return {
            "_key": edge_key,
            "_from": f"{self.from_collection}/{self.from_key}",
            "_to": f"{self.to_collection}/{self.to_key}",
            **self.properties,
        }


@dataclass(slots=True)
class SubstanceGraphData:
    """Complete graph data structure for a substance search."""

    search_term: str
    found: bool = False

    drugs: dict[str, Drug] = field(default_factory=dict)
    substances: dict[str, Substance] = field(default_factory=dict)
    manufacturers: dict[str, Manufacturer] = field(default_factory=dict)
    routes: dict[str, Route] = field(default_factory=dict)
    dosage_forms: dict[str, DosageForm] = field(default_factory=dict)
    pharm_classes: dict[str, PharmClass] = field(default_factory=dict)
    reactions: dict[str, Reaction] = field(default_factory=dict)
    applications: dict[str, FDAApplication] = field(default_factory=dict)
    products: dict[str, Product] = field(default_factory=dict)
    interactions: dict[str, Interaction] = field(default_factory=dict)
    drug_labels: dict[str, DrugLabel] = field(default_factory=dict)

    edges: list[Edge] = field(default_factory=list)
    _edge_ids: set[str] = field(default_factory=set)

    raw_fda_data: dict[str, Any] = field(default_factory=dict)
    raw_rxnorm_data: dict[str, Any] = field(default_factory=dict)

    def add_edge(self, edge: Edge) -> bool:
        """Add edge avoiding duplicates."""
        edge_id = edge.get_unique_id()
        if edge_id in self._edge_ids:
            return False

        self._edge_ids.add(edge_id)
        self.edges.append(edge)
        return True

    def to_graph_model(self) -> dict[str, Any]:
        """Convert to ArangoDB-compatible format."""
        edges_by_collection: dict[str, list[dict]] = {}
        for edge in self.edges:
            if edge.edge_collection not in edges_by_collection:
                edges_by_collection[edge.edge_collection] = []
            edges_by_collection[edge.edge_collection].append(edge.to_dict())

        return {
            "vertices": {
                "drugs": [v.to_dict() if hasattr(v, "to_dict") else v for v in self.drugs.values()],
                "substances": [v.to_dict() for v in self.substances.values()],
                "manufacturers": [v.to_dict() for v in self.manufacturers.values()],
                "routes": [v.to_dict() for v in self.routes.values()],
                "dosage_forms": [v.to_dict() for v in self.dosage_forms.values()],
                "pharm_classes": [v.to_dict() for v in self.pharm_classes.values()],
                "reactions": [v.to_dict() for v in self.reactions.values()],
                "applications": [v.to_dict() for v in self.applications.values()],
                "products": [v.to_dict() for v in self.products.values()],
                "interactions": [v.to_dict() for v in self.interactions.values()],
                "drug_labels": [v.to_dict() for v in self.drug_labels.values()],
            },
            "edges": edges_by_collection,
            "metadata": {
                "search_term": self.search_term,
                "found": self.found,
                "drug_count": len(self.drugs),
                "substance_count": len(self.substances),
                "total_edges": len(self.edges),
            },
        }

    def summary(self) -> dict[str, int]:
        return {
            "drugs": len(self.drugs),
            "substances": len(self.substances),
            "manufacturers": len(self.manufacturers),
            "routes": len(self.routes),
            "dosage_forms": len(self.dosage_forms),
            "pharm_classes": len(self.pharm_classes),
            "reactions": len(self.reactions),
            "applications": len(self.applications),
            "products": len(self.products),
            "interactions": len(self.interactions),
            "drug_labels": len(self.drug_labels),
            "edges": len(self.edges),
        }
