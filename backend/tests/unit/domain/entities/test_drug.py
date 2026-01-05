"""
Unit tests for Drug entity.
"""

import pytest

from src.domain.entities.drug import Drug


class TestDrug:
    """Unit tests for Drug entity."""

    def test_create_drug_minimal(self) -> None:
        drug = Drug(key="test_key")

        assert drug.key == "test_key"
        assert drug.brand_names == []
        assert drug.generic_names == []
        assert drug.is_enriched is False

    def test_create_drug_full(self) -> None:
        drug = Drug(
            key="full_drug",
            application_number="NDA123456",
            brand_names=["Brand1", "Brand2"],
            generic_names=["generic1"],
            ndc_codes=["12345-678-90"],
            rxcui=["123456"],
            spl_id=["spl-123"],
            sponsor_name="TestSponsor",
            drug_type="NDA",
            source="test",
            is_enriched=True,
        )

        assert drug.key == "full_drug"
        assert drug.application_number == "NDA123456"
        assert len(drug.brand_names) == 2
        assert drug.is_enriched is True

    def test_is_generic_anda(self) -> None:
        drug = Drug(
            key="generic_drug",
            application_number="ANDA123456",
        )

        assert drug.is_generic() is True

    def test_is_generic_nda(self) -> None:
        drug = Drug(
            key="brand_drug",
            application_number="NDA123456",
        )

        assert drug.is_generic() is False

    def test_is_generic_no_application(self) -> None:
        drug = Drug(key="no_app_drug")

        assert drug.is_generic() is False

    def test_to_dict(self) -> None:
        drug = Drug(
            key="dict_drug",
            brand_names=["TestBrand"],
            generic_names=["testgeneric"],
            is_enriched=True,
        )

        result = drug.to_dict()

        assert result["_key"] == "dict_drug"
        assert result["brand_names"] == ["TestBrand"]
        assert result["is_enriched"] is True
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self) -> None:
        data = {
            "_key": "from_dict_drug",
            "application_number": "NDA999",
            "brand_names": ["FromDict"],
            "generic_names": ["fromdict"],
            "is_enriched": True,
        }

        drug = Drug.from_dict(data)

        assert drug.key == "from_dict_drug"
        assert drug.application_number == "NDA999"
        assert drug.brand_names == ["FromDict"]
        assert drug.is_enriched is True

    def test_from_dict_with_key_field(self) -> None:
        data = {
            "key": "key_field_drug",
            "brand_names": ["KeyField"],
        }

        drug = Drug.from_dict(data)

        assert drug.key == "key_field_drug"

    def test_roundtrip_serialization(self) -> None:
        original = Drug(
            key="roundtrip",
            application_number="NDA111",
            brand_names=["Round", "Trip"],
            generic_names=["roundtrip"],
            ndc_codes=["111-222-33"],
            rxcui=["111222"],
            is_enriched=True,
        )

        serialized = original.to_dict()
        restored = Drug.from_dict(serialized)

        assert restored.key == original.key
        assert restored.application_number == original.application_number
        assert restored.brand_names == original.brand_names
        assert restored.is_enriched == original.is_enriched
