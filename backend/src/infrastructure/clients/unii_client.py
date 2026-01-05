"""
FDA Substance/UNII API Client.

Provides chemical data including:
- UNII (Unique Ingredient Identifier)
- SMILES (chemical structure)
- Molecular formula and weight
- InChI/InChIKey
- CAS numbers
- PubChem IDs

Documentation: https://open.fda.gov/apis/other/substance/
"""

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import Any

from src.infrastructure.clients.base import BaseHTTPClient
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class UNIIClientConfig:
    """UNII/Substance API client configuration."""

    base_url: str = "https://api.fda.gov/other/substance.json"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True


@dataclass
class ChemicalData:
    """Chemical data for a substance."""

    unii: str | None = None
    name: str | None = None
    substance_class: str | None = None
    formula: str | None = None
    molecular_weight: float | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchi_key: str | None = None
    cas_number: str | None = None
    pubchem_id: str | None = None
    molfile: str | None = None
    stereochemistry: str | None = None
    optical_activity: str | None = None
    definition_type: str | None = None
    names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unii": self.unii,
            "name": self.name,
            "substance_class": self.substance_class,
            "formula": self.formula,
            "molecular_weight": self.molecular_weight,
            "smiles": self.smiles,
            "inchi": self.inchi,
            "inchi_key": self.inchi_key,
            "cas_number": self.cas_number,
            "pubchem_id": self.pubchem_id,
            "molfile": self.molfile,
            "stereochemistry": self.stereochemistry,
            "optical_activity": self.optical_activity,
            "definition_type": self.definition_type,
            "names": self.names,
        }


class UNIIClient(BaseHTTPClient):
    """Async client for FDA Substance/UNII API."""

    def __init__(self, config: UNIIClientConfig | None = None) -> None:
        config = config or UNIIClientConfig()
        super().__init__(
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            verify_ssl=config.verify_ssl,
        )

    async def _unii_request(self, params: dict[str, Any]) -> dict[str, Any] | None:
        response = await self.get("", params=params)

        if response.status_code == 404:
            return None
        if response.status_code == 200:
            data = response.json()
            if "error" in data and "NOT_FOUND" in str(data.get("error", {}).get("code", "")):
                return None
            return data

        text = response.text
        if "NOT_FOUND" in text or "No matches found" in text:
            return None

        logger.warning(
            "unii_api_error",
            status_code=response.status_code,
        )
        return None

    def _extract_chemical_data(self, record: dict[str, Any]) -> ChemicalData:
        data = ChemicalData()

        data.unii = record.get("unii")
        data.substance_class = record.get("substance_class")
        data.definition_type = record.get("definition_type")

        names = record.get("names", [])
        data.names = [n.get("name", "") for n in names if n.get("name")]

        for name_entry in names:
            if name_entry.get("display_name"):
                data.name = name_entry.get("name")
                break
        if not data.name and data.names:
            data.name = data.names[0]

        structure = record.get("structure", {})
        if structure:
            data.smiles = structure.get("smiles")
            data.formula = structure.get("formula")
            data.molfile = structure.get("molfile")
            data.stereochemistry = structure.get("stereochemistry")
            data.optical_activity = structure.get("optical_activity")

            mw = structure.get("mwt")
            if mw:
                with contextlib.suppress(ValueError, TypeError):
                    data.molecular_weight = float(mw)

        if not data.smiles:
            moieties = record.get("moieties", [])
            for moiety in moieties:
                if moiety.get("smiles"):
                    data.smiles = moiety.get("smiles")
                    data.formula = data.formula or moiety.get("formula")
                    data.molfile = data.molfile or moiety.get("molfile")
                    data.stereochemistry = data.stereochemistry or moiety.get("stereochemistry")
                    break

        codes = record.get("codes", [])
        for code in codes:
            code_system = code.get("code_system", "").upper()
            code_value = code.get("code", "")

            if "CAS" in code_system and not data.cas_number:
                data.cas_number = code_value
            elif "PUBCHEM" in code_system and not data.pubchem_id:
                data.pubchem_id = code_value
            elif "INCHI" in code_system.upper():
                if "KEY" in code_system.upper():
                    data.inchi_key = code_value
                else:
                    data.inchi = code_value

        return data

    async def search_by_unii(self, unii: str) -> ChemicalData | None:
        params = {"search": f'unii:"{unii}"', "limit": 1}
        result = await self._unii_request(params)

        if result and "results" in result and result["results"]:
            return self._extract_chemical_data(result["results"][0])
        return None

    async def search_by_name(self, name: str, limit: int = 5) -> list[ChemicalData]:
        escaped_name = name.replace('"', '\\"').upper()
        params = {"search": f'names.name:"{escaped_name}"', "limit": min(limit, 100)}

        result = await self._unii_request(params)

        chemicals: list[ChemicalData] = []
        if result and "results" in result:
            for record in result["results"]:
                chemicals.append(self._extract_chemical_data(record))
        return chemicals

    async def search_by_cas(self, cas_number: str) -> ChemicalData | None:
        params = {
            "search": f'codes.code:"{cas_number}" AND codes.code_system:"CAS"',
            "limit": 1,
        }
        result = await self._unii_request(params)

        if result and "results" in result and result["results"]:
            return self._extract_chemical_data(result["results"][0])
        return None

    async def get_substance_data(
        self,
        unii: str | None = None,
        name: str | None = None,
    ) -> ChemicalData | None:
        if unii:
            result = await self.search_by_unii(unii)
            if result:
                return result

        if name:
            results = await self.search_by_name(name, limit=1)
            if results:
                return results[0]

        return None

    async def get_multiple_substances(
        self,
        substances: list[dict[str, str]],
    ) -> dict[str, ChemicalData]:
        results: dict[str, ChemicalData] = {}

        tasks: list = []
        keys: list[str] = []

        for sub in substances:
            unii = sub.get("unii")
            name = sub.get("name")
            key = unii or name

            if key and key not in results:
                keys.append(key)
                tasks.append(self.get_substance_data(unii=unii, name=name))

        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for key, result in zip(keys, task_results, strict=False):
                if isinstance(result, ChemicalData):
                    results[key] = result
                elif isinstance(result, Exception):
                    logger.warning("substance_fetch_error", key=key, error=str(result))

        return results
