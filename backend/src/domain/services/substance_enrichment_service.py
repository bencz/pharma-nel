"""
Substance Enrichment Service.

Orchestrates FDA, RxNorm, and UNII clients to fetch comprehensive substance data
and structure it for the ArangoDB knowledge graph.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.domain.entities.application import FDAApplication
from src.domain.entities.dosage_form import DosageForm
from src.domain.entities.drug import Drug
from src.domain.entities.drug_label import DrugLabel
from src.domain.entities.interaction import Interaction
from src.domain.entities.manufacturer import Manufacturer
from src.domain.entities.pharm_class import PharmClass
from src.domain.entities.pharma_graph import Edge, SubstanceGraphData, generate_key
from src.domain.entities.product import Product
from src.domain.entities.reaction import Reaction
from src.domain.entities.route import Route
from src.domain.entities.substance import Substance
from src.infrastructure.clients.fda_client import FDAClient
from src.infrastructure.clients.rxnorm_client import RxNormClient
from src.infrastructure.clients.unii_client import UNIIClient
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SubstanceEnrichmentService:
    """
    Service to enrich substance data from multiple APIs.

    Combines data from:
    - FDA OpenFDA API (drugsfda, label, ndc, event, enforcement)
    - NIH RxNorm API (rxcui, ingredients, brands, interactions)
    - FDA UNII/GSRS API (chemical data: SMILES, formula, CAS, etc)
    """

    def __init__(
        self,
        fda_client: FDAClient,
        rxnorm_client: RxNormClient,
        unii_client: UNIIClient,
    ) -> None:
        self._fda = fda_client
        self._rxnorm = rxnorm_client
        self._unii = unii_client

    async def get_substance_data(
        self,
        substance_name: str,
        include_events: bool = True,
        events_limit: int = 100,
        include_interactions: bool = True,
    ) -> SubstanceGraphData:
        """
        Fetch all data for a substance and structure for the graph.

        Args:
            substance_name: Substance name (brand, generic, or active ingredient)
            include_events: Whether to fetch adverse events
            events_limit: Limit for adverse events
            include_interactions: Whether to fetch drug interactions

        Returns:
            SubstanceGraphData with all structured data
        """
        logger.info("substance_enrichment_started", substance_name=substance_name)

        fda_data = await self._fda.get_all_drug_data(
            substance_name,
            include_events=include_events,
            events_limit=events_limit,
        )

        rxcui_hint = self._extract_rxcui_hint(fda_data)

        rxnorm_data = await self._rxnorm.get_all_drug_data(substance_name, rxcui_hint=rxcui_hint)

        result = SubstanceGraphData(
            search_term=substance_name,
            raw_fda_data=fda_data,
            raw_rxnorm_data=rxnorm_data,
        )

        drug_spl_map = self._process_ndc_data(fda_data.get("ndc", []), result, substance_name)
        self._process_drugsfda_data(fda_data.get("drugsfda", []), result, substance_name)
        self._process_enforcement_data(fda_data.get("enforcement", []), result)

        if include_events:
            self._process_event_data(fda_data.get("events", []), result)

        self._process_rxnorm_data(rxnorm_data, result, include_interactions)

        await self._fetch_labels_by_spl_id(drug_spl_map, result)

        await self._enrich_substances_with_chemical_data(result)

        result.found = len(result.drugs) > 0 or len(result.substances) > 0

        if result.found:
            self._ensure_main_substance(substance_name, result)

        logger.info(
            "substance_enrichment_completed",
            substance_name=substance_name,
            found=result.found,
            summary=result.summary(),
        )

        return result

    def _ensure_main_substance(self, search_term: str, result: SubstanceGraphData) -> None:
        """
        Ensure a main substance document exists for the search term.

        This creates the central node that represents the searched substance
        (e.g., "ibuprofen", "aspirin"). All related drugs/products link to this
        substance via drug_has_substance edge.
        """
        substance_key = search_term.lower().replace(" ", "_").replace("-", "_")

        if substance_key in result.substances:
            return

        existing_substance = None
        for sub in result.substances.values():
            if sub.name.lower() == search_term.lower():
                existing_substance = sub
                break

        if existing_substance:
            return

        now = datetime.now(UTC).isoformat()

        main_substance = Substance(
            key=substance_key,
            name=search_term.upper(),
            is_enriched=True,
            enriched_at=now,
        )
        result.substances[substance_key] = main_substance

        for drug_key in result.drugs:
            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="substances",
                    to_key=substance_key,
                    edge_collection="drug_has_substance",
                )
            )

        logger.info(
            "main_substance_created",
            substance=search_term,
            substance_key=substance_key,
            linked_drugs=len(result.drugs),
        )

    def _extract_rxcui_hint(self, fda_data: dict[str, Any]) -> str | None:
        """Extract RxCUI from FDA data to optimize RxNorm lookup."""
        for record in fda_data.get("drugsfda", []):
            openfda = record.get("openfda", {})
            rxcuis = openfda.get("rxcui", [])
            if rxcuis:
                return rxcuis[0]
        return None

    async def _fetch_labels_by_spl_id(
        self,
        drug_spl_map: dict[str, str],
        result: SubstanceGraphData,
    ) -> None:
        """
        Fetch drug labels by SPL ID for correct 1:1 drug->label linking.

        Args:
            drug_spl_map: Dict mapping drug_key -> spl_id
            result: SubstanceGraphData to populate with labels
        """
        if not drug_spl_map:
            return

        tasks = [
            self._fda.get_label_by_spl_id(spl_id)
            for spl_id in drug_spl_map.values()
        ]

        labels = await asyncio.gather(*tasks, return_exceptions=True)

        for (drug_key, spl_id), label_data in zip(drug_spl_map.items(), labels, strict=False):
            if isinstance(label_data, Exception) or not label_data:
                continue

            label_key = generate_key(spl_id)
            if not label_key or label_key in result.drug_labels:
                continue

            def get_text(field: str, data: dict = label_data) -> str | None:
                val = data.get(field, [])
                return val[0] if val else None

            result.drug_labels[label_key] = DrugLabel(
                key=label_key,
                spl_id=spl_id,
                set_id=label_data.get("set_id", ""),
                version=label_data.get("version", ""),
                effective_time=label_data.get("effective_time", ""),
                description=get_text("description"),
                clinical_pharmacology=get_text("clinical_pharmacology"),
                mechanism_of_action=get_text("mechanism_of_action"),
                indications_and_usage=get_text("indications_and_usage"),
                dosage_and_administration=get_text("dosage_and_administration"),
                contraindications=get_text("contraindications"),
                warnings_and_cautions=get_text("warnings_and_cautions") or get_text("warnings"),
                boxed_warning=get_text("boxed_warning"),
                adverse_reactions=get_text("adverse_reactions"),
                drug_interactions=get_text("drug_interactions"),
            )

            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="drug_labels",
                    to_key=label_key,
                    edge_collection="drug_has_label",
                )
            )

        logger.info(
            "labels_fetched_by_spl_id",
            total_drugs=len(drug_spl_map),
            labels_found=len(result.drug_labels),
        )

    def _find_existing_drug_key(
        self,
        application_number: str,
        brand_names: list[str],
        generic_names: list[str],
        result: SubstanceGraphData,
    ) -> str | None:
        """
        Find existing drug key in result by application_number or name match.

        Priority:
        1. Exact application_number match
        2. Brand name match (case insensitive)
        3. Generic name match (case insensitive)
        """
        if application_number:
            app_key = generate_key(application_number)
            if app_key and app_key in result.drugs:
                return app_key

        brand_lower = {n.lower() for n in brand_names}
        generic_lower = {n.lower() for n in generic_names}

        for key, drug in result.drugs.items():
            drug_brands = {n.lower() for n in (drug.brand_names or [])}
            drug_generics = {n.lower() for n in (drug.generic_names or [])}

            if brand_lower & drug_brands or generic_lower & drug_generics:
                return key

        return None

    def _process_drugsfda_data(
        self,
        records: list[dict],
        result: SubstanceGraphData,
        _search_term: str,
    ) -> None:
        """Process drugsfda endpoint data."""
        now = datetime.now(UTC).isoformat()

        for record in records:
            openfda = record.get("openfda", {})
            application_number = record.get("application_number", "")
            sponsor_name = record.get("sponsor_name", "")

            brand_names = openfda.get("brand_name", [])
            generic_names = openfda.get("generic_name", [])
            manufacturer_names = openfda.get("manufacturer_name", [])
            substances = openfda.get("substance_name", [])
            routes = openfda.get("route", [])
            dosage_forms = openfda.get("dosage_form", [])

            pharm_classes_epc = openfda.get("pharm_class_epc", [])
            pharm_classes_moa = openfda.get("pharm_class_moa", [])

            ndc_codes = openfda.get("product_ndc", [])
            rxcui = openfda.get("rxcui", [])
            unii = openfda.get("unii", [])
            spl_id = openfda.get("spl_id", [])

            drug_key = generate_key(application_number or (brand_names[0] if brand_names else ""))
            if drug_key and drug_key not in result.drugs:
                result.drugs[drug_key] = Drug(
                    key=drug_key,
                    application_number=application_number,
                    brand_names=brand_names,
                    generic_names=generic_names,
                    ndc_codes=ndc_codes,
                    rxcui=rxcui,
                    spl_id=spl_id,
                    sponsor_name=sponsor_name,
                    drug_type=application_number[:3] if application_number else "UNKNOWN",
                    source="drugsfda",
                    is_enriched=True,
                    enriched_at=now,
                )

            for submission in record.get("submissions", []):
                self._process_submission(submission, application_number, drug_key, result)

            for mfr in manufacturer_names:
                self._add_manufacturer(mfr, drug_key, result)

            for idx, sub in enumerate(substances):
                sub_unii = unii[idx] if idx < len(unii) else None
                self._add_substance(sub, sub_unii, None, drug_key, result)

            for route in routes:
                self._add_route(route, drug_key, result)

            for form in dosage_forms:
                self._add_dosage_form(form, drug_key, result)

            for pc in pharm_classes_epc:
                self._add_pharm_class(pc, "EPC", drug_key, result)
            for pc in pharm_classes_moa:
                self._add_pharm_class(pc, "MOA", drug_key, result)

            for product in record.get("products", []):
                self._process_product(product, application_number, drug_key, result)

    def _process_submission(
        self,
        submission: dict,
        app_num: str,
        drug_key: str | None,
        result: SubstanceGraphData,
    ) -> None:
        """Process FDA submission."""
        sub_type = submission.get("submission_type", "")
        sub_number = submission.get("submission_number", "")

        app_key = generate_key(app_num, sub_type, sub_number)
        if app_key and app_key not in result.applications:
            result.applications[app_key] = FDAApplication(
                key=app_key,
                application_number=app_num,
                submission_type=sub_type,
                submission_number=sub_number,
                submission_status=submission.get("submission_status", ""),
                submission_status_date=submission.get("submission_status_date", ""),
                review_priority=submission.get("review_priority", ""),
            )

            if drug_key:
                result.add_edge(
                    Edge(
                        from_collection="applications",
                        from_key=app_key,
                        to_collection="drugs",
                        to_key=drug_key,
                        edge_collection="application_for_drug",
                        properties={"type": sub_type, "status": submission.get("submission_status", "")},
                    )
                )

    def _process_product(
        self,
        product: dict,
        app_num: str,
        drug_key: str | None,
        result: SubstanceGraphData,
    ) -> None:
        """Process product."""
        prod_number = product.get("product_number", "")
        prod_key = generate_key(app_num, prod_number)

        if prod_key and prod_key not in result.products:
            result.products[prod_key] = Product(
                key=prod_key,
                product_number=prod_number,
                brand_name=product.get("brand_name", ""),
                dosage_form=product.get("dosage_form", ""),
                route=product.get("route", ""),
                marketing_status=product.get("marketing_status", ""),
            )

            if drug_key:
                result.add_edge(
                    Edge(
                        from_collection="products",
                        from_key=prod_key,
                        to_collection="drugs",
                        to_key=drug_key,
                        edge_collection="product_of_drug",
                    )
                )

    def _add_manufacturer(self, name: str, drug_key: str | None, result: SubstanceGraphData) -> None:
        mfr_key = generate_key(name)
        if mfr_key and mfr_key not in result.manufacturers:
            result.manufacturers[mfr_key] = Manufacturer(key=mfr_key, name=name)

        if drug_key and mfr_key:
            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="manufacturers",
                    to_key=mfr_key,
                    edge_collection="drug_by_manufacturer",
                )
            )

    def _add_substance(
        self,
        name: str,
        unii: str | None,
        rxcui: str | None,
        drug_key: str | None,
        result: SubstanceGraphData,
    ) -> None:
        sub_key = generate_key(name)
        if sub_key:
            if sub_key not in result.substances:
                result.substances[sub_key] = Substance(key=sub_key, name=name, unii=unii, rxcui=rxcui)
            else:
                existing = result.substances[sub_key]
                if unii and not existing.unii:
                    existing.unii = unii
                if rxcui and not existing.rxcui:
                    existing.rxcui = rxcui

            if drug_key:
                result.add_edge(
                    Edge(
                        from_collection="drugs",
                        from_key=drug_key,
                        to_collection="substances",
                        to_key=sub_key,
                        edge_collection="drug_has_substance",
                    )
                )

    def _add_route(self, name: str, drug_key: str | None, result: SubstanceGraphData) -> None:
        route_key = generate_key(name)
        if route_key and route_key not in result.routes:
            result.routes[route_key] = Route(key=route_key, name=name)

        if drug_key and route_key:
            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="routes",
                    to_key=route_key,
                    edge_collection="drug_has_route",
                )
            )

    def _add_dosage_form(self, name: str, drug_key: str | None, result: SubstanceGraphData) -> None:
        form_key = generate_key(name)
        if form_key and form_key not in result.dosage_forms:
            result.dosage_forms[form_key] = DosageForm(key=form_key, name=name)

        if drug_key and form_key:
            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="dosage_forms",
                    to_key=form_key,
                    edge_collection="drug_has_form",
                )
            )

    def _add_pharm_class(
        self,
        name: str,
        class_type: str,
        drug_key: str | None,
        result: SubstanceGraphData,
    ) -> None:
        class_key = generate_key(name)
        if class_key and class_key not in result.pharm_classes:
            result.pharm_classes[class_key] = PharmClass(key=class_key, name=name, class_type=class_type)

        if drug_key and class_key:
            result.add_edge(
                Edge(
                    from_collection="drugs",
                    from_key=drug_key,
                    to_collection="pharm_classes",
                    to_key=class_key,
                    edge_collection="drug_in_class",
                )
            )

    def _process_ndc_data(
        self,
        records: list[dict],
        result: SubstanceGraphData,
        search_term: str,
    ) -> dict[str, str]:
        """
        Process NDC data. Mark as enriched if exact match with search term.

        Returns:
            Dict mapping drug_key -> spl_id for label fetching.
        """
        search_lower = search_term.lower()
        now = datetime.now(UTC).isoformat()
        drug_spl_map: dict[str, str] = {}

        for record in records:
            product_ndc = record.get("product_ndc", "")
            if not product_ndc:
                continue

            brand_name = record.get("brand_name", "")
            generic_name = record.get("generic_name", "")
            spl_id = record.get("spl_id", "")

            is_exact_match = (
                brand_name.lower() == search_lower or
                generic_name.lower() == search_lower
            )

            drug_key = generate_key(product_ndc)

            if drug_key and drug_key not in result.drugs:
                result.drugs[drug_key] = Drug(
                    key=drug_key,
                    brand_names=[brand_name] if brand_name else [],
                    generic_names=[generic_name] if generic_name else [],
                    ndc_codes=[product_ndc],
                    spl_id=[spl_id] if spl_id else [],
                    source="ndc",
                    is_enriched=is_exact_match,
                    enriched_at=now if is_exact_match else None,
                )

                if spl_id and is_exact_match:
                    drug_spl_map[drug_key] = spl_id

            for pkg in record.get("packaging", []):
                pkg_ndc = pkg.get("package_ndc", "")
                pkg_key = generate_key(pkg_ndc)

                if pkg_key and pkg_key not in result.products:
                    result.products[pkg_key] = Product(
                        key=pkg_key,
                        package_ndc=pkg_ndc,
                        description=pkg.get("description", ""),
                    )

                    if drug_key:
                        result.add_edge(
                            Edge(
                                from_collection="products",
                                from_key=pkg_key,
                                to_collection="drugs",
                                to_key=drug_key,
                                edge_collection="product_of_drug",
                            )
                        )

        return drug_spl_map

    def _process_event_data(self, records: list[dict], result: SubstanceGraphData) -> None:
        """Process adverse event data."""
        for record in records:
            patient = record.get("patient", {})

            for drug in patient.get("drug", []):
                openfda = drug.get("openfda", {})
                brand_names = openfda.get("brand_name", [])
                generic_names = openfda.get("generic_name", [])
                substances = openfda.get("substance_name", [])
                routes = openfda.get("route", [])
                rxcui = openfda.get("rxcui", [])
                unii = openfda.get("unii", [])

                drug_name = brand_names[0] if brand_names else (generic_names[0] if generic_names else drug.get("medicinalproduct", ""))

                if not drug_name:
                    continue

                drug_key = generate_key(drug_name)

                if drug_key and drug_key not in result.drugs:
                    result.drugs[drug_key] = Drug(
                        key=drug_key,
                        brand_names=brand_names,
                        generic_names=generic_names,
                        rxcui=rxcui,
                        source="adverse_event",
                    )

                for idx, sub in enumerate(substances):
                    sub_unii = unii[idx] if idx < len(unii) else None
                    self._add_substance(sub, sub_unii, None, drug_key, result)

                for route in routes:
                    self._add_route(route, drug_key, result)

                for reaction in patient.get("reaction", []):
                    reaction_term = reaction.get("reactionmeddrapt", "")
                    if not reaction_term:
                        continue

                    reaction_key = generate_key(reaction_term)

                    if reaction_key and reaction_key not in result.reactions:
                        result.reactions[reaction_key] = Reaction(
                            key=reaction_key,
                            name=reaction_term,
                            meddra_version=reaction.get("reactionmeddraversionpt", ""),
                        )

                    if drug_key and reaction_key:
                        result.add_edge(
                            Edge(
                                from_collection="drugs",
                                from_key=drug_key,
                                to_collection="reactions",
                                to_key=reaction_key,
                                edge_collection="drug_causes_reaction",
                                properties={
                                    "outcome": reaction.get("reactionoutcome", ""),
                                    "drug_characterization": drug.get("drugcharacterization", ""),
                                },
                            )
                        )

    def _process_enforcement_data(self, records: list[dict], result: SubstanceGraphData) -> None:
        """Process enforcement/recall data."""
        for record in records:
            openfda = record.get("openfda", {})
            brand_names = openfda.get("brand_name", [])
            generic_names = openfda.get("generic_name", [])
            substances = openfda.get("substance_name", [])
            routes = openfda.get("route", [])
            unii = openfda.get("unii", [])
            rxcui = openfda.get("rxcui", [])

            drug_name = brand_names[0] if brand_names else (generic_names[0] if generic_names else "")

            if not drug_name:
                continue

            drug_key = generate_key(drug_name)

            if drug_key and drug_key not in result.drugs:
                result.drugs[drug_key] = Drug(
                    key=drug_key,
                    brand_names=brand_names,
                    generic_names=generic_names,
                    rxcui=rxcui,
                    source="enforcement",
                )

            for mfr in openfda.get("manufacturer_name", []):
                self._add_manufacturer(mfr, drug_key, result)

            for idx, sub in enumerate(substances):
                sub_unii = unii[idx] if idx < len(unii) else None
                self._add_substance(sub, sub_unii, None, drug_key, result)

            for route in routes:
                self._add_route(route, drug_key, result)

    def _process_rxnorm_data(
        self,
        rxnorm_data: dict[str, Any],
        result: SubstanceGraphData,
        include_interactions: bool,
    ) -> None:
        """Process RxNorm data."""
        if not rxnorm_data.get("found"):
            return

        source_rxcui = rxnorm_data.get("rxcui")
        source_name = rxnorm_data.get("name", "")

        main_drug_key = self._find_main_drug_key(rxnorm_data, result)

        for ingredient in rxnorm_data.get("ingredients", []):
            ing_name = ingredient.get("name", "")
            if ing_name:
                self._add_substance(ing_name, None, ingredient.get("rxcui"), main_drug_key, result)

        for brand in rxnorm_data.get("brands", []):
            brand_name = brand.get("name", "")
            if not brand_name:
                continue

            drug_key = generate_key(brand_name)
            if drug_key and drug_key not in result.drugs:
                result.drugs[drug_key] = Drug(
                    key=drug_key,
                    brand_names=[brand_name],
                    rxcui=[brand.get("rxcui", "")],
                    source="rxnorm",
                )

        if include_interactions:
            self._process_interactions(
                rxnorm_data.get("interactions", []),
                main_drug_key,
                source_rxcui,
                source_name,
                result,
            )

        ndc_codes = rxnorm_data.get("ndc_codes", [])
        if ndc_codes and main_drug_key and main_drug_key in result.drugs:
            drug = result.drugs[main_drug_key]
            drug.ndc_codes = list(set(drug.ndc_codes + ndc_codes))

    def _find_main_drug_key(self, rxnorm_data: dict[str, Any], result: SubstanceGraphData) -> str | None:
        """Find or create main drug based on RxNorm data."""
        rxcui = rxnorm_data.get("rxcui")
        name = rxnorm_data.get("name", "")

        if rxcui:
            for key, drug in result.drugs.items():
                if rxcui in drug.rxcui:
                    return key

        if name:
            drug_key = generate_key(name)
            if drug_key and drug_key not in result.drugs:
                result.drugs[drug_key] = Drug(
                    key=drug_key,
                    rxcui=[rxcui] if rxcui else [],
                    source="rxnorm",
                )
            return drug_key

        return next(iter(result.drugs.keys()), None) if result.drugs else None

    def _process_interactions(
        self,
        interactions: list[dict],
        source_drug_key: str | None,
        source_rxcui: str | None,
        source_name: str,
        result: SubstanceGraphData,
    ) -> None:
        """Process drug interactions from RxNorm."""
        for interaction in interactions:
            desc = interaction.get("description", "")
            if not desc:
                continue

            severity = interaction.get("severity", "N/A")

            target_info = interaction.get("minConceptItem", {})
            target_rxcui = target_info.get("rxcui", "")
            target_name = target_info.get("name", "")

            int_key = generate_key(source_rxcui or source_name, target_rxcui or target_name, "interaction")

            if not int_key:
                continue

            if int_key not in result.interactions:
                result.interactions[int_key] = Interaction(
                    key=int_key,
                    severity=severity,
                    description=desc,
                    source_drug_rxcui=source_rxcui,
                    source_drug_name=source_name,
                    target_drug_rxcui=target_rxcui,
                    target_drug_name=target_name,
                    source_api="rxnorm",
                )

            if source_drug_key:
                result.add_edge(
                    Edge(
                        from_collection="drugs",
                        from_key=source_drug_key,
                        to_collection="interactions",
                        to_key=int_key,
                        edge_collection="drug_interacts_with",
                        properties={"severity": severity, "role": "source"},
                    )
                )

            if target_name:
                target_drug_key = generate_key(target_name)

                if target_drug_key and target_drug_key not in result.drugs:
                    result.drugs[target_drug_key] = Drug(
                        key=target_drug_key,
                        rxcui=[target_rxcui] if target_rxcui else [],
                        source="rxnorm_interaction",
                    )

                if target_drug_key:
                    result.add_edge(
                        Edge(
                            from_collection="drugs",
                            from_key=target_drug_key,
                            to_collection="interactions",
                            to_key=int_key,
                            edge_collection="drug_interacts_with",
                            properties={"severity": severity, "role": "target"},
                        )
                    )

    async def _enrich_substances_with_chemical_data(self, result: SubstanceGraphData) -> None:
        """Enrich substances with chemical data from UNII/GSRS."""
        if not result.substances:
            return

        logger.info("enriching_substances", count=len(result.substances))

        substances_to_fetch = [{"unii": sub.unii, "name": sub.name} for sub in result.substances.values()]

        chemical_data = await self._unii.get_multiple_substances(substances_to_fetch)

        enriched_count = 0
        for sub in result.substances.values():
            chem = chemical_data.get(sub.unii) or chemical_data.get(sub.name)

            if chem:
                enriched_count += 1
                now = datetime.now(UTC).isoformat()

                if chem.unii and not sub.unii:
                    sub.unii = chem.unii

                sub.formula = chem.formula
                sub.molecular_weight = chem.molecular_weight
                sub.smiles = chem.smiles
                sub.inchi = chem.inchi
                sub.inchi_key = chem.inchi_key
                sub.cas_number = chem.cas_number
                sub.pubchem_id = chem.pubchem_id
                sub.substance_class = chem.substance_class
                sub.stereochemistry = chem.stereochemistry
                sub.is_enriched = True
                sub.enriched_at = now

        logger.info("substances_enriched", enriched=enriched_count, total=len(result.substances))
