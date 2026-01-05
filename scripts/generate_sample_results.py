#!/usr/bin/env python3
"""
Sample Results Generator

This script processes PDF files from the samples/ directory using the Pharma NER API
and generates Markdown reports with the extraction results.

Usage:
    python scripts/generate_sample_results.py [--api-url URL] [--output-dir DIR]

Requirements:
    - Backend API running (default: http://localhost:8000)
    - PDF files in samples/ directory
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import httpx


# Configuration
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_SAMPLES_DIR = Path(__file__).parent.parent / "samples"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "results"


async def check_api_health(client: httpx.AsyncClient, api_url: str) -> bool:
    """Check if the API is healthy and ready."""
    try:
        response = await client.get(f"{api_url}/health/live", timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] API health check failed: {e}")
        return False


async def extract_from_pdf(
    client: httpx.AsyncClient, api_url: str, pdf_path: Path
) -> dict | None:
    """Send PDF to extraction API and return results."""
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = await client.post(
                f"{api_url}/extract",
                files=files,
                timeout=120.0,  # NER extraction can take time
            )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Extraction failed for {pdf_path.name}: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"[ERROR] Error extracting {pdf_path.name}: {e}")
        return None


async def get_entity_details(
    client: httpx.AsyncClient, api_url: str, entity_id: str
) -> dict | None:
    """Get detailed information about an entity."""
    try:
        response = await client.get(
            f"{api_url}/entity/{entity_id}",
            timeout=30.0,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def generate_markdown_report(
    pdf_name: str,
    extraction_result: dict,
    entity_details: dict[str, dict],
) -> str:
    """Generate a Markdown report from extraction results."""
    data = extraction_result.get("data", {})
    profile = data.get("profile", {})
    entities = data.get("entities", [])
    extraction_id = data.get("extraction_id", "N/A")

    # Build Markdown
    lines = [
        f"# Extraction Results: {pdf_name}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Extraction ID:** `{extraction_id}`",
        "",
        "---",
        "",
        "## Profile Information",
        "",
    ]

    if profile:
        lines.extend([
            f"- **Name:** {profile.get('full_name', 'N/A')}",
            f"- **Credentials:** {', '.join(profile.get('credentials', [])) or 'N/A'}",
            f"- **Email:** {profile.get('email', 'N/A')}",
            f"- **Phone:** {profile.get('phone', 'N/A')}",
        ])
        if profile.get("therapeutic_areas"):
            lines.append(f"- **Therapeutic Areas:** {', '.join(profile.get('therapeutic_areas', []))}")
    else:
        lines.append("*No profile information extracted*")

    lines.extend([
        "",
        "---",
        "",
        "## Extracted Entities",
        "",
        f"**Total Entities:** {len(entities)}",
        "",
    ])

    if entities:
        # Group entities by type
        entities_by_type: dict[str, list] = {}
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        for entity_type, type_entities in sorted(entities_by_type.items()):
            lines.extend([
                f"### {entity_type} ({len(type_entities)})",
                "",
                "| Name | Linked To | Relationship | Confidence |",
                "|------|-----------|--------------|------------|",
            ])

            for entity in type_entities:
                name = entity.get("name", "N/A")
                linked_to = entity.get("linked_to", "-")
                relationship = entity.get("relationship", "-")
                confidence = entity.get("confidence", "-")
                if isinstance(confidence, (int, float)):
                    confidence = f"{confidence}%"

                lines.append(f"| {name} | {linked_to} | {relationship} | {confidence} |")

            lines.append("")

        # Entity Details Section
        if entity_details:
            lines.extend([
                "---",
                "",
                "## Entity Details",
                "",
            ])

            for entity_id, details in entity_details.items():
                if not details or not details.get("success"):
                    continue

                entity_data = details.get("data", {})
                substance = entity_data.get("substance", {})

                if substance:
                    lines.extend([
                        f"### {substance.get('name', entity_id)}",
                        "",
                    ])

                    if substance.get("unii"):
                        lines.append(f"- **UNII:** `{substance.get('unii')}`")
                    if substance.get("cas"):
                        lines.append(f"- **CAS:** `{substance.get('cas')}`")
                    if substance.get("inchikey"):
                        lines.append(f"- **InChIKey:** `{substance.get('inchikey')}`")
                    if substance.get("molecular_formula"):
                        lines.append(f"- **Molecular Formula:** {substance.get('molecular_formula')}")

                    # FDA data
                    fda_data = entity_data.get("fda", {})
                    if fda_data:
                        lines.extend([
                            "",
                            "**FDA Information:**",
                        ])
                        if fda_data.get("products"):
                            lines.append(f"- Products: {len(fda_data.get('products', []))} found")
                        if fda_data.get("applications"):
                            lines.append(f"- Applications: {len(fda_data.get('applications', []))} found")

                    lines.append("")

    else:
        lines.append("*No entities extracted*")

    lines.extend([
        "---",
        "",
        "## Raw API Response",
        "",
        "<details>",
        "<summary>Click to expand</summary>",
        "",
        "```json",
    ])

    import json
    lines.append(json.dumps(extraction_result, indent=2, default=str))

    lines.extend([
        "```",
        "",
        "</details>",
    ])

    return "\n".join(lines)


async def process_samples(
    api_url: str,
    samples_dir: Path,
    output_dir: Path,
) -> None:
    """Process all PDF samples and generate reports."""
    # Find PDF files
    pdf_files = list(samples_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"[ERROR] No PDF files found in {samples_dir}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in {samples_dir}")
    print(f"API URL: {api_url}")
    print(f"Output directory: {output_dir}")
    print()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        # Check API health
        print("Checking API health...")
        if not await check_api_health(client, api_url):
            print("[ERROR] API is not available. Please start the backend first.")
            print(f"   Expected API at: {api_url}")
            sys.exit(1)
        print("[OK] API is healthy")
        print()

        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

            # Extract entities
            print("   Sending to extraction API...")
            result = await extract_from_pdf(client, api_url, pdf_path)

            if not result or not result.get("success"):
                print(f"   [ERROR] Extraction failed")
                continue

            print("   [OK] Extraction complete")

            # Get entity details for each extracted entity
            entities = result.get("data", {}).get("entities", [])
            entity_details = {}

            if entities:
                print(f"   Fetching details for {len(entities)} entities...")
                for entity in entities:
                    entity_id = entity.get("substance_id")
                    if entity_id and entity_id not in entity_details:
                        details = await get_entity_details(client, api_url, entity_id)
                        if details:
                            entity_details[entity_id] = details

            # Generate Markdown report
            print("   Generating Markdown report...")
            report = generate_markdown_report(pdf_path.name, result, entity_details)

            # Save report
            output_file = output_dir / f"{pdf_path.stem}_results.md"
            output_file.write_text(report, encoding="utf-8")
            print(f"   Saved: {output_file}")
            print()

    # Generate summary
    print("=" * 60)
    print("[OK] Processing complete!")
    print(f"   Reports saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Markdown reports from sample PDF extractions"
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Backend API URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=DEFAULT_SAMPLES_DIR,
        help=f"Directory containing PDF samples (default: {DEFAULT_SAMPLES_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for reports (default: {DEFAULT_OUTPUT_DIR})",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  Pharma NER - Sample Results Generator")
    print("=" * 60)
    print()

    asyncio.run(process_samples(args.api_url, args.samples_dir, args.output_dir))


if __name__ == "__main__":
    main()
