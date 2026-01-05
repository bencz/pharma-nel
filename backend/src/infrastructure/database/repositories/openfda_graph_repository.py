"""
OpenFDA Drug Graph Repository (Async).

Handles persistence of the OpenFDA drug knowledge graph to ArangoDB.
Contains the graph schema definition and graph-level operations.
"""

from typing import Any, ClassVar

from arangoasync.database import Database
from arangoasync.exceptions import DocumentInsertError
from arangoasync.typings import CollectionType

from src.domain.entities.pharma_graph import Edge, SubstanceGraphData
from src.infrastructure.database.repositories.base import (
    BaseRepository,
    EdgeDefinition,
    IndexDefinition,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


OPENFDA_DRUG_GRAPH_SCHEMA: dict[str, Any] = {
    "graph_name": "openfda_drug_graph",
    "vertex_collections": [
        "drugs",
        "substances",
        "manufacturers",
        "routes",
        "dosage_forms",
        "pharm_classes",
        "reactions",
        "applications",
        "products",
        "interactions",
        "drug_labels",
        "profiles",
        "extractions",
    ],
    "edge_definitions": [
        {
            "edge_collection": "drug_has_substance",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["substances"],
        },
        {
            "edge_collection": "drug_has_route",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["routes"],
        },
        {
            "edge_collection": "drug_has_form",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["dosage_forms"],
        },
        {
            "edge_collection": "drug_in_class",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["pharm_classes"],
        },
        {
            "edge_collection": "drug_by_manufacturer",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["manufacturers"],
        },
        {
            "edge_collection": "application_for_drug",
            "from_vertex_collections": ["applications"],
            "to_vertex_collections": ["drugs"],
        },
        {
            "edge_collection": "product_of_drug",
            "from_vertex_collections": ["products"],
            "to_vertex_collections": ["drugs"],
        },
        {
            "edge_collection": "drug_causes_reaction",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["reactions"],
        },
        {
            "edge_collection": "drug_interacts_with",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["interactions"],
        },
        {
            "edge_collection": "drug_has_label",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["drug_labels"],
        },
        {
            "edge_collection": "drug_alias_of",
            "from_vertex_collections": ["drugs"],
            "to_vertex_collections": ["drugs"],
        },
        {
            "edge_collection": "profile_has_extraction",
            "from_vertex_collections": ["profiles"],
            "to_vertex_collections": ["extractions"],
        },
        {
            "edge_collection": "profile_interested_in_substance",
            "from_vertex_collections": ["profiles"],
            "to_vertex_collections": ["substances"],
        },
    ],
}


class OpenFDAGraphRepository(BaseRepository[SubstanceGraphData]):
    """
    Repository for the OpenFDA drug knowledge graph.

    Manages the graph structure and provides methods for
    persisting enrichment results and querying relationships.
    """

    collection_name: ClassVar[str] = "drugs"
    graph_name: ClassVar[str] = OPENFDA_DRUG_GRAPH_SCHEMA["graph_name"]

    indices: ClassVar[list[IndexDefinition]] = []

    edge_definitions: ClassVar[list[EdgeDefinition]] = [
        EdgeDefinition(
            collection="drug_has_substance",
            from_collections=["drugs"],
            to_collections=["substances"],
        ),
        EdgeDefinition(
            collection="drug_has_route",
            from_collections=["drugs"],
            to_collections=["routes"],
        ),
        EdgeDefinition(
            collection="drug_has_form",
            from_collections=["drugs"],
            to_collections=["dosage_forms"],
        ),
        EdgeDefinition(
            collection="drug_in_class",
            from_collections=["drugs"],
            to_collections=["pharm_classes"],
        ),
        EdgeDefinition(
            collection="drug_by_manufacturer",
            from_collections=["drugs"],
            to_collections=["manufacturers"],
        ),
        EdgeDefinition(
            collection="application_for_drug",
            from_collections=["applications"],
            to_collections=["drugs"],
        ),
        EdgeDefinition(
            collection="product_of_drug",
            from_collections=["products"],
            to_collections=["drugs"],
        ),
        EdgeDefinition(
            collection="drug_causes_reaction",
            from_collections=["drugs"],
            to_collections=["reactions"],
        ),
        EdgeDefinition(
            collection="drug_interacts_with",
            from_collections=["drugs"],
            to_collections=["interactions"],
        ),
        EdgeDefinition(
            collection="drug_has_label",
            from_collections=["drugs"],
            to_collections=["drug_labels"],
        ),
        EdgeDefinition(
            collection="drug_alias_of",
            from_collections=["drugs"],
            to_collections=["drugs"],
        ),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self._graph = None

    async def ensure_graph(self) -> None:
        """Ensure the graph and all vertex/edge collections exist."""
        graphs = await self._db.graphs()
        graph_names = [g["name"] for g in graphs]

        if self.graph_name not in graph_names:
            edge_definitions = []
            for edge_def in OPENFDA_DRUG_GRAPH_SCHEMA["edge_definitions"]:
                edge_definitions.append({
                    "collection": edge_def["edge_collection"],
                    "from": edge_def["from_vertex_collections"],
                    "to": edge_def["to_vertex_collections"],
                })

            await self._db.create_graph(
                self.graph_name,
                edge_definitions=edge_definitions,
            )
            logger.info("graph_created", graph_name=self.graph_name)

        self._graph = self._db.graph(self.graph_name)

    async def _ensure_vertex_collection(self, name: str) -> None:
        """Ensure a vertex collection exists."""
        collections = await self._db.collections()
        collection_names = [c["name"] for c in collections]

        if name not in collection_names:
            await self._db.create_collection(name)
            logger.debug("vertex_collection_created", collection=name)

    async def _ensure_edge_collection(self, name: str) -> None:
        """Ensure an edge collection exists."""
        collections = await self._db.collections()
        collection_names = [c["name"] for c in collections]

        if name not in collection_names:
            await self._db.create_collection(name, col_type=CollectionType.EDGE)
            logger.debug("edge_collection_created", collection=name)

    async def persist_graph_data(self, data: SubstanceGraphData) -> dict[str, int]:
        """
        Persist all graph data from enrichment result.

        Returns counts of persisted entities.
        """
        await self.ensure_graph()

        counts: dict[str, int] = {}

        counts["drugs"] = await self._persist_vertices("drugs", data.drugs)
        counts["substances"] = await self._persist_vertices("substances", data.substances)
        counts["manufacturers"] = await self._persist_vertices("manufacturers", data.manufacturers)
        counts["routes"] = await self._persist_vertices("routes", data.routes)
        counts["dosage_forms"] = await self._persist_vertices("dosage_forms", data.dosage_forms)
        counts["pharm_classes"] = await self._persist_vertices("pharm_classes", data.pharm_classes)
        counts["reactions"] = await self._persist_vertices("reactions", data.reactions)
        counts["applications"] = await self._persist_vertices("applications", data.applications)
        counts["products"] = await self._persist_vertices("products", data.products)
        counts["interactions"] = await self._persist_vertices("interactions", data.interactions)
        counts["drug_labels"] = await self._persist_vertices("drug_labels", data.drug_labels)

        counts["edges"] = await self._persist_edges(data.edges)

        logger.info("graph_data_persisted", search_term=data.search_term, counts=counts)
        return counts

    async def _persist_vertices(
        self,
        collection_name: str,
        vertices: dict[str, Any],
    ) -> int:
        """Persist vertices to a collection using upsert logic."""
        if not vertices:
            return 0

        await self._ensure_vertex_collection(collection_name)
        collection = self._db.collection(collection_name)

        count = 0
        for entity in vertices.values():
            doc = entity.to_dict() if hasattr(entity, "to_dict") else entity
            key = doc.get("_key")

            if key:
                exists = await collection.has(key)
                if exists:
                    await collection.update(doc)
                    count += 1
                else:
                    await self._safe_insert(collection, doc)
                    count += 1

        return count

    async def _safe_insert(self, collection, doc: dict) -> bool:
        """Insert document, handling unique constraint violations gracefully."""
        try:
            await collection.insert(doc)
            return True
        except DocumentInsertError as e:
            if "unique constraint violated" in str(e):
                logger.debug(
                    "duplicate_skipped",
                    collection=collection.name,
                    key=doc.get("_key"),
                )
                return False
            raise

    async def _persist_edges(self, edges: list[Edge]) -> int:
        """Persist edges to their respective collections."""
        if not edges:
            return 0

        edges_by_collection: dict[str, list[dict]] = {}
        for edge in edges:
            if edge.edge_collection not in edges_by_collection:
                edges_by_collection[edge.edge_collection] = []
            edges_by_collection[edge.edge_collection].append(edge.to_dict())

        count = 0
        for collection_name, edge_docs in edges_by_collection.items():
            await self._ensure_edge_collection(collection_name)
            collection = self._db.collection(collection_name)

            for doc in edge_docs:
                key = doc.get("_key")
                if key:
                    exists = await collection.has(key)
                    if not exists and await self._safe_insert(collection, doc):
                        count += 1

        return count

    async def get_drug_with_relations(self, drug_key: str) -> dict[str, Any] | None:
        """Get a drug with all its related entities via graph traversal."""
        query = """
        FOR drug IN drugs
            FILTER drug._key == @drug_key
            LET substances = (
                FOR v, e IN 1..1 OUTBOUND drug drug_has_substance
                    RETURN v
            )
            LET routes = (
                FOR v, e IN 1..1 OUTBOUND drug drug_has_route
                    RETURN v
            )
            LET forms = (
                FOR v, e IN 1..1 OUTBOUND drug drug_has_form
                    RETURN v
            )
            LET classes = (
                FOR v, e IN 1..1 OUTBOUND drug drug_in_class
                    RETURN v
            )
            LET manufacturers = (
                FOR v, e IN 1..1 OUTBOUND drug drug_by_manufacturer
                    RETURN v
            )
            LET labels = (
                FOR v, e IN 1..1 OUTBOUND drug drug_has_label
                    RETURN v
            )
            LET interactions = (
                FOR v, e IN 1..1 OUTBOUND drug drug_interacts_with
                    RETURN v
            )
            LET reactions = (
                FOR v, e IN 1..1 OUTBOUND drug drug_causes_reaction
                    RETURN v
            )
            RETURN {
                drug: drug,
                substances: substances,
                routes: routes,
                dosage_forms: forms,
                pharm_classes: classes,
                manufacturers: manufacturers,
                labels: labels,
                interactions: interactions,
                reactions: reactions
            }
        """
        results = await self.execute_query(query, {"drug_key": drug_key})
        return results[0] if results else None

    async def get_substance_relations(self, substance_key: str) -> dict[str, Any]:
        """
        Get ALL related entities for a substance via graph traversal.

        Returns complete data for:
        - drugs: Commercial drug products containing this substance
        - pharm_classes: Pharmacological classes
        - manufacturers: Drug manufacturers
        - routes: Administration routes
        - dosage_forms: Dosage forms
        - products: NDC products/packages
        - applications: FDA applications
        - labels: Drug labels/package inserts
        - interactions: Drug-drug interactions
        - reactions: Adverse reactions
        """
        query = """
        LET substance = DOCUMENT(CONCAT("substances/", @substance_key))

        LET drugs = (
            FOR drug IN 1..1 INBOUND substance drug_has_substance
                RETURN {
                    key: drug._key,
                    application_number: drug.application_number,
                    brand_names: drug.brand_names,
                    generic_names: drug.generic_names,
                    ndc_codes: drug.ndc_codes,
                    rxcui: drug.rxcui,
                    spl_id: drug.spl_id,
                    sponsor_name: drug.sponsor_name,
                    drug_type: drug.type,
                    source: drug.source,
                    is_enriched: drug.is_enriched
                }
        )

        LET drug_docs = (
            FOR drug IN 1..1 INBOUND substance drug_has_substance
                RETURN drug
        )

        LET pharm_classes = (
            FOR drug IN drug_docs
                FOR pc IN 1..1 OUTBOUND drug drug_in_class
                    COLLECT key = pc._key, name = pc.name, class_type = pc.class_type
                    RETURN { key: key, name: name, class_type: class_type }
        )

        LET manufacturers = (
            FOR drug IN drug_docs
                FOR m IN 1..1 OUTBOUND drug drug_by_manufacturer
                    COLLECT key = m._key, name = m.name
                    RETURN { key: key, name: name }
        )

        LET routes = (
            FOR drug IN drug_docs
                FOR r IN 1..1 OUTBOUND drug drug_has_route
                    COLLECT key = r._key, name = r.name
                    RETURN { key: key, name: name }
        )

        LET dosage_forms = (
            FOR drug IN drug_docs
                FOR df IN 1..1 OUTBOUND drug drug_has_form
                    COLLECT key = df._key, name = df.name
                    RETURN { key: key, name: name }
        )

        LET products = (
            FOR drug IN drug_docs
                FOR p IN 1..1 OUTBOUND drug product_of_drug
                    RETURN {
                        key: p._key,
                        product_number: p.product_number,
                        package_ndc: p.package_ndc,
                        brand_name: p.brand_name,
                        dosage_form: p.dosage_form,
                        route: p.route,
                        marketing_status: p.marketing_status,
                        description: p.description
                    }
        )

        LET applications = (
            FOR drug IN drug_docs
                FOR app IN 1..1 OUTBOUND drug application_for_drug
                    RETURN {
                        key: app._key,
                        application_number: app.application_number,
                        submission_type: app.submission_type,
                        submission_number: app.submission_number,
                        submission_status: app.submission_status,
                        submission_status_date: app.submission_status_date,
                        review_priority: app.review_priority
                    }
        )

        LET labels = (
            FOR drug IN drug_docs
                FOR lbl IN 1..1 OUTBOUND drug drug_has_label
                    RETURN {
                        key: lbl._key,
                        spl_id: lbl.spl_id,
                        set_id: lbl.set_id,
                        version: lbl.version,
                        effective_time: lbl.effective_time,
                        description: lbl.description,
                        clinical_pharmacology: lbl.clinical_pharmacology,
                        mechanism_of_action: lbl.mechanism_of_action,
                        indications_and_usage: lbl.indications_and_usage,
                        dosage_and_administration: lbl.dosage_and_administration,
                        contraindications: lbl.contraindications,
                        warnings_and_cautions: lbl.warnings_and_cautions,
                        boxed_warning: lbl.boxed_warning,
                        adverse_reactions: lbl.adverse_reactions,
                        drug_interactions: lbl.drug_interactions
                    }
        )

        LET interactions = (
            FOR drug IN drug_docs
                FOR inter IN 1..1 OUTBOUND drug drug_interacts_with
                    RETURN {
                        key: inter._key,
                        severity: inter.severity,
                        description: inter.description,
                        source_drug_rxcui: inter.source_drug_rxcui,
                        source_drug_name: inter.source_drug_name,
                        target_drug_rxcui: inter.target_drug_rxcui,
                        target_drug_name: inter.target_drug_name
                    }
        )

        LET reactions = (
            FOR drug IN drug_docs
                FOR rxn IN 1..1 OUTBOUND drug drug_causes_reaction
                    COLLECT key = rxn._key, name = rxn.name, meddra_version = rxn.meddra_version
                    RETURN { key: key, name: name, meddra_version: meddra_version }
        )

        RETURN {
            drugs: drugs,
            pharm_classes: pharm_classes,
            manufacturers: manufacturers,
            routes: routes,
            dosage_forms: dosage_forms,
            products: products,
            applications: applications,
            labels: labels,
            interactions: interactions,
            reactions: reactions
        }
        """
        results = await self.execute_query(query, {"substance_key": substance_key})
        return results[0] if results else {}

    async def find_substances_by_names(
        self,
        names: list[str],
    ) -> dict[str, Any]:
        """
        Find enriched substances by name.

        Args:
            names: List of substance names to search for

        Returns:
            Dict mapping lowercase name -> Substance object
        """
        if not names:
            return {}

        from src.domain.entities.substance import Substance

        names_lower = [n.lower() for n in names]
        keys = [n.lower().replace(" ", "_").replace("-", "_") for n in names]

        query = """
            FOR s IN substances
                FILTER s._key IN @keys
                    OR LOWER(s.name) IN @names_lower
                FILTER s.is_enriched == true
                RETURN s
        """

        results = await self.execute_query(query, {"keys": keys, "names_lower": names_lower})

        found: dict[str, Any] = {}
        for doc in results:
            substance = Substance.from_dict(doc)
            found[substance.name.lower()] = substance
            key_as_name = substance.key.replace("_", " ")
            if key_as_name not in found:
                found[key_as_name] = substance

        return found

    async def get_graph_stats(self) -> dict[str, int]:
        """Get statistics for all collections in the graph."""
        stats: dict[str, int] = {}

        for coll_name in OPENFDA_DRUG_GRAPH_SCHEMA["vertex_collections"]:
            collections = await self._db.collections()
            collection_names = [c["name"] for c in collections]
            if coll_name in collection_names:
                collection = self._db.collection(coll_name)
                stats[coll_name] = await collection.count()
            else:
                stats[coll_name] = 0

        for edge_def in OPENFDA_DRUG_GRAPH_SCHEMA["edge_definitions"]:
            coll_name = edge_def["edge_collection"]
            collections = await self._db.collections()
            collection_names = [c["name"] for c in collections]
            if coll_name in collection_names:
                collection = self._db.collection(coll_name)
                stats[coll_name] = await collection.count()
            else:
                stats[coll_name] = 0

        return stats

    async def get_profiles_interested_in_substance(
        self,
        substance_key: str,
    ) -> list[dict[str, Any]]:
        """Get all profiles interested in a substance via graph traversal."""
        query = """
        FOR p IN 1..1 INBOUND DOCUMENT(CONCAT("substances/", @substance_key)) profile_interested_in_substance
            RETURN {
                key: p._key,
                full_name: p.full_name,
                email: p.email,
                credentials: p.credentials
            }
        """
        return await self.execute_query(query, {"substance_key": substance_key})

    async def get_substance_with_profiles(
        self,
        substance_key: str,
    ) -> dict[str, Any] | None:
        """Get substance with all interested profiles."""
        query = """
        LET substance = DOCUMENT(CONCAT("substances/", @substance_key))

        LET profiles = (
            FOR p IN 1..1 INBOUND substance profile_interested_in_substance
                RETURN {
                    key: p._key,
                    full_name: p.full_name,
                    email: p.email,
                    credentials: p.credentials,
                    linkedin: p.linkedin
                }
        )

        RETURN {
            substance: {
                key: substance._key,
                name: substance.name,
                unii: substance.unii,
                formula: substance.formula,
                molecular_weight: substance.molecular_weight
            },
            interested_profiles: profiles
        }
        """
        results = await self.execute_query(query, {"substance_key": substance_key})
        return results[0] if results else None
