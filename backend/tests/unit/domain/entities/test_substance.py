"""
Unit tests for Substance entity.
"""

import pytest

from src.domain.entities.substance import Substance


class TestSubstance:
    """Unit tests for Substance entity."""

    def test_create_substance_minimal(self) -> None:
        substance = Substance(key="test_sub", name="Test Substance")

        assert substance.key == "test_sub"
        assert substance.name == "Test Substance"
        assert substance.unii is None
        assert substance.is_enriched is False

    def test_create_substance_full(self) -> None:
        substance = Substance(
            key="full_sub",
            name="Full Substance",
            unii="ABC123DEF",
            rxcui="123456",
            formula="C10H15N",
            molecular_weight=165.23,
            smiles="CC(C)NCC(O)c1ccc(O)c(O)c1",
            inchi="InChI=1S/C10H15NO3/...",
            inchi_key="UCTWMZQNUQWSLP-UHFFFAOYSA-N",
            cas_number="51-43-4",
            pubchem_id="5816",
            substance_class="Chemical",
            stereochemistry="ACHIRAL",
            is_enriched=True,
        )

        assert substance.key == "full_sub"
        assert substance.unii == "ABC123DEF"
        assert substance.molecular_weight == 165.23
        assert substance.is_enriched is True

    def test_to_dict(self) -> None:
        substance = Substance(
            key="dict_sub",
            name="Dict Substance",
            unii="XYZ789",
            formula="H2O",
        )

        result = substance.to_dict()

        assert result["_key"] == "dict_sub"
        assert result["name"] == "Dict Substance"
        assert result["unii"] == "XYZ789"
        assert result["formula"] == "H2O"
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self) -> None:
        data = {
            "_key": "from_dict_sub",
            "name": "From Dict",
            "unii": "FROMDICT",
            "molecular_weight": 100.5,
            "is_enriched": True,
        }

        substance = Substance.from_dict(data)

        assert substance.key == "from_dict_sub"
        assert substance.name == "From Dict"
        assert substance.unii == "FROMDICT"
        assert substance.molecular_weight == 100.5
        assert substance.is_enriched is True

    def test_from_dict_with_key_field(self) -> None:
        data = {
            "key": "key_field_sub",
            "name": "Key Field",
        }

        substance = Substance.from_dict(data)

        assert substance.key == "key_field_sub"

    def test_roundtrip_serialization(self) -> None:
        original = Substance(
            key="roundtrip_sub",
            name="Roundtrip Substance",
            unii="ROUND123",
            formula="C6H12O6",
            molecular_weight=180.16,
            is_enriched=True,
        )

        serialized = original.to_dict()
        restored = Substance.from_dict(serialized)

        assert restored.key == original.key
        assert restored.name == original.name
        assert restored.unii == original.unii
        assert restored.molecular_weight == original.molecular_weight
        assert restored.is_enriched == original.is_enriched
