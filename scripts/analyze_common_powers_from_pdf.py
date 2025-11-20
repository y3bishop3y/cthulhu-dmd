#!/usr/bin/env python3
"""
Analyze common_powers.json against the traits_booklet.pdf to verify parsing accuracy.

This script:
1. Extracts power descriptions from the PDF
2. Compares with JSON descriptions
3. Identifies OCR errors and parsing issues
4. Checks if statistics are correctly calculated
5. Suggests improvements to effects and statistics
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/analyze_common_powers_from_pdf.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/analyze_power_statistics.py [options]\n\n"
        "Recommended: uv run ./scripts/analyze_common_powers_from_pdf.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.utils.parsing import OCR_CORRECTIONS
from scripts.utils.pdf import (
    extract_text_from_pdf_pages,
    get_pdf_page_count,
)

console = Console()

# Common power names
COMMON_POWERS = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


def find_power_section_in_pdf(text: str, power_name: str) -> Optional[str]:
    """Find the section for a specific power in the PDF text."""
    # Look for power name followed by level descriptions
    # Pattern: Power name, then Level 1, Level 2, etc.
    patterns = [
        rf"{re.escape(power_name)}.*?(?=\n\n[A-Z][A-Z\s]{{3,}}|\n[A-Z][a-z]+\s+[A-Z]|$)",
        rf"{re.escape(power_name.upper())}.*?(?=\n\n[A-Z][A-Z\s]{{3,}}|\n[A-Z][a-z]+\s+[A-Z]|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)

    return None


def extract_level_descriptions_from_text(text: str, power_name: str) -> Dict[int, str]:
    """Extract level descriptions from PDF text."""
    levels: Dict[int, str] = {}

    # Look for "Level 1:", "Level 2:", etc. patterns
    # Also handle patterns like "1:", "2:", etc. that might appear
    level_pattern = re.compile(
        r"(?:Level|LEVEL|^)\s*([1234])[:\-\.]?\s*(.*?)(?=(?:Level|LEVEL|^)\s*[1234]|$)",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )

    matches = level_pattern.findall(text)
    for level_num_str, description in matches:
        level_num = int(level_num_str)
        desc_clean = re.sub(r"\s+", " ", description.strip())
        # Filter out very short or invalid descriptions
        if desc_clean and len(desc_clean) > 10 and not desc_clean.startswith("Appendix"):
            # Remove page numbers and other artifacts
            desc_clean = re.sub(r"\d+\s*$", "", desc_clean).strip()
            if desc_clean and len(desc_clean) > 10:
                levels[level_num] = desc_clean

    return levels


def compare_descriptions(
    pdf_desc: Optional[str], json_desc: str, power_name: str, level: int
) -> Dict[str, any]:
    """Compare PDF and JSON descriptions, identifying issues."""
    issues = []
    suggestions = []

    if not pdf_desc:
        issues.append("Power level not found in PDF")
        return {"issues": issues, "suggestions": suggestions, "pdf_text": None}

    # Use centralized OCR corrections from TOML config
    ocr_errors = OCR_CORRECTIONS

    json_lower = json_desc.lower()

    # Check for OCR errors in JSON
    for error, correction in ocr_errors.items():
        if error in json_lower and correction not in json_lower:
            issues.append(f"OCR error: '{error}' should be '{correction}'")

    # Compare lengths (PDF should be more complete)
    if len(pdf_desc) > len(json_desc) * 1.5:
        issues.append(
            f"JSON description is significantly shorter ({len(json_desc)} vs {len(pdf_desc)} chars)"
        )
        suggestions.append("Consider using PDF description as it appears more complete")

    # Check for garbled text in JSON
    if re.search(r"[A-Z]{5,}", json_desc):
        issues.append("Contains garbled uppercase text (likely OCR error)")

    if re.search(r"\s{3,}", json_desc):
        issues.append("Contains excessive whitespace (likely OCR error)")

    return {
        "issues": issues,
        "suggestions": suggestions,
        "pdf_text": pdf_desc,
        "json_text": json_desc,
    }


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data",
    help="Data directory",
)
@click.option(
    "--power",
    type=str,
    help="Analyze specific power only",
)
def main(data_dir: Path, power: Optional[str]):
    """Analyze common_powers.json against traits_booklet.pdf."""
    console.print(
        Panel.fit(
            "[bold cyan]Common Powers Analysis[/bold cyan]\n"
            "Comparing JSON descriptions with PDF source",
            border_style="cyan",
        )
    )

    # Load JSON
    json_path = data_dir / "common_powers.json"
    if not json_path.exists():
        console.print(f"[red]Error: {json_path} not found![/red]")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    # Load PDF
    pdf_path = data_dir / "traits_booklet.pdf"
    if not pdf_path.exists():
        console.print(f"[red]Error: {pdf_path} not found![/red]")
        sys.exit(1)

    console.print("[cyan]Extracting text from PDF...[/cyan]")
    # Extract appendix pages (34-37) where power descriptions are located
    pages_data = extract_text_from_pdf_pages(pdf_path, start_page=34, end_page=38)
    pdf_text = "\n\n".join([page["text"] for page in pages_data])
    page_count = get_pdf_page_count(pdf_path)
    console.print(
        f"[green]✓ Extracted {len(pdf_text)} characters from appendix pages (34-37)[/green]\n"
    )

    # Analyze each power
    powers_to_analyze = [p for p in powers_data if not power or p["name"] == power]

    for power_data in powers_to_analyze:
        power_name = power_data["name"]
        console.print(f"\n[bold cyan]{power_name}[/bold cyan]")
        console.print("=" * 80)

        # Find power section in PDF
        pdf_section = find_power_section_in_pdf(pdf_text, power_name)
        if pdf_section:
            pdf_levels = extract_level_descriptions_from_text(pdf_section, power_name)
            console.print(f"[green]✓ Found power section in PDF ({len(pdf_levels)} levels)[/green]")
        else:
            console.print("[yellow]⚠ Power section not found in PDF[/yellow]")
            pdf_levels = {}

        # Compare each level
        for level_data in power_data["levels"]:
            level = level_data["level"]
            json_desc = level_data["description"]
            stats = level_data.get("statistics", {})
            effect = level_data.get("effect", "")

            console.print(f"\n[bold]Level {level}:[/bold]")

            # Get PDF description if available
            pdf_desc = pdf_levels.get(level)

            # Compare descriptions
            comparison = compare_descriptions(pdf_desc, json_desc, power_name, level)

            # Show JSON description
            console.print(
                f"[yellow]JSON:[/yellow] {json_desc[:150]}{'...' if len(json_desc) > 150 else ''}"
            )

            # Show PDF description if available
            if pdf_desc:
                console.print(
                    f"[green]PDF:[/green] {pdf_desc[:150]}{'...' if len(pdf_desc) > 150 else ''}"
                )

            # Show issues
            if comparison["issues"]:
                console.print("[red]Issues:[/red]")
                for issue in comparison["issues"]:
                    console.print(f"  • {issue}")

            # Show statistics
            if stats:
                console.print("[cyan]Statistics:[/cyan]")
                console.print(
                    f"  Green dice: {stats.get('green_dice_added', 0)}, "
                    f"Black dice: {stats.get('black_dice_added', 0)}"
                )
                console.print(
                    f"  Expected successes: {stats.get('base_expected_successes', 0):.2f} → "
                    f"{stats.get('enhanced_expected_successes', 0):.2f} "
                    f"(+{stats.get('expected_successes_increase', 0):.2f}, "
                    f"{stats.get('expected_successes_percent_increase', 0):.1f}%)"
                )
                console.print(f"  Effect: {effect}")

            # Suggestions
            if comparison["suggestions"]:
                console.print("[magenta]Suggestions:[/magenta]")
                for suggestion in comparison["suggestions"]:
                    console.print(f"  • {suggestion}")

    console.print("\n[green]✓ Analysis complete![/green]")


if __name__ == "__main__":
    main()
