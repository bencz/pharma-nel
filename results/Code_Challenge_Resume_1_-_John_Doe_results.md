# Extraction Results: Code_Challenge_Resume_1_-_John_Doe.pdf

**Generated:** 2026-01-05 05:53:03
**Extraction ID:** `5ac6d23b2a20f9610fe3dbd609f4f79f`

---

## Profile Information

- **Name:** John Doe
- **Credentials:** MD, MPH, TM, MS
- **Email:** None
- **Phone:** None

---

## Extracted Entities

**Total Entities:** 15

### BRAND (4)

| Name | Linked To | Relationship | Confidence |
|------|-----------|--------------|------------|
| KADCYLA | trastuzumab emtansine | brand_of | - |
| TIBSOVO | ivosidenib | brand_of | - |
| IDHIFA | enasidenib | brand_of | - |
| PYRUKYND | None | None | - |

### CODE (6)

| Name | Linked To | Relationship | Confidence |
|------|-----------|--------------|------------|
| MM-302 | None | None | - |
| MM-111 | None | None | - |
| MM-141 | None | None | - |
| MM-DX-929 | None | None | - |
| IPI-549 | None | None | - |
| AG-120 | ivosidenib | same_as | - |

### GENERIC (5)

| Name | Linked To | Relationship | Confidence |
|------|-----------|--------------|------------|
| trastuzumab emtansine | KADCYLA | generic_of | - |
| ivosidenib | TIBSOVO | generic_of | - |
| enasidenib | IDHIFA | generic_of | - |
| Vorasidenib | None | None | - |
| sunitinib malate | None | None | - |

---

## Entity Details

---

## Raw API Response

<details>
<summary>Click to expand</summary>

```json
{
  "success": true,
  "data": {
    "extraction_id": "5ac6d23b2a20f9610fe3dbd609f4f79f",
    "profile": {
      "id": "4b1a1c31df30d33db7a0ca27",
      "full_name": "John Doe",
      "credentials": [
        "MD",
        "MPH",
        "TM",
        "MS"
      ],
      "email": null,
      "phone": null,
      "linkedin": null,
      "location": null
    },
    "entities": [
      {
        "name": "KADCYLA",
        "type": "BRAND",
        "linked_to": "trastuzumab emtansine",
        "relationship": "brand_of",
        "substance_id": "kadcyla",
        "url": "entity/kadcyla"
      },
      {
        "name": "trastuzumab emtansine",
        "type": "GENERIC",
        "linked_to": "KADCYLA",
        "relationship": "generic_of",
        "substance_id": "trastuzumab_emtansine",
        "url": "entity/trastuzumab_emtansine"
      },
      {
        "name": "MM-302",
        "type": "CODE",
        "linked_to": null,
        "relationship": null,
        "substance_id": null,
        "url": null
      },
      {
        "name": "MM-111",
        "type": "CODE",
        "linked_to": null,
        "relationship": null,
        "substance_id": null,
        "url": null
      },
      {
        "name": "MM-141",
        "type": "CODE",
        "linked_to": null,
        "relationship": null,
        "substance_id": null,
        "url": null
      },
      {
        "name": "MM-DX-929",
        "type": "CODE",
        "linked_to": null,
        "relationship": null,
        "substance_id": null,
        "url": null
      },
      {
        "name": "TIBSOVO",
        "type": "BRAND",
        "linked_to": "ivosidenib",
        "relationship": "brand_of",
        "substance_id": "tibsovo",
        "url": "entity/tibsovo"
      },
      {
        "name": "ivosidenib",
        "type": "GENERIC",
        "linked_to": "TIBSOVO",
        "relationship": "generic_of",
        "substance_id": "ivosidenib",
        "url": "entity/ivosidenib"
      },
      {
        "name": "IDHIFA",
        "type": "BRAND",
        "linked_to": "enasidenib",
        "relationship": "brand_of",
        "substance_id": "idhifa",
        "url": "entity/idhifa"
      },
      {
        "name": "enasidenib",
        "type": "GENERIC",
        "linked_to": "IDHIFA",
        "relationship": "generic_of",
        "substance_id": "enasidenib",
        "url": "entity/enasidenib"
      },
      {
        "name": "PYRUKYND",
        "type": "BRAND",
        "linked_to": null,
        "relationship": null,
        "substance_id": "pyrukynd",
        "url": "entity/pyrukynd"
      },
      {
        "name": "Vorasidenib",
        "type": "GENERIC",
        "linked_to": null,
        "relationship": null,
        "substance_id": "vorasidenib",
        "url": "entity/vorasidenib"
      },
      {
        "name": "IPI-549",
        "type": "CODE",
        "linked_to": null,
        "relationship": null,
        "substance_id": null,
        "url": null
      },
      {
        "name": "AG-120",
        "type": "CODE",
        "linked_to": "ivosidenib",
        "relationship": "same_as",
        "substance_id": null,
        "url": null
      },
      {
        "name": "sunitinib malate",
        "type": "GENERIC",
        "linked_to": null,
        "relationship": null,
        "substance_id": "sunitinib_malate",
        "url": "entity/sunitinib_malate"
      }
    ]
  },
  "error": null
}
```

</details>