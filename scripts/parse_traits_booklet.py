#!/usr/bin/env python3
"""
Parse the Death May Die traits booklet PDF to extract trait information.
This will help us understand the structure of traits and their levels.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Final, List, Optional

try:
    import click
    import pdfplumber
    from pydantic import BaseModel, Field
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_traits_booklet.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_traits_booklet.py [options]\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
TRAITS_BOOKLET_FILENAME: Final[str] = "traits_booklet.pdf"
OUTPUT_JSON: Final[str] = "traits_data.json"

# Common trait names
COMMON_TRAITS: Final[List[str]] = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


# Pydantic Models
class TraitLevel(BaseModel):
    """Represents a single level of a trait."""

    level: int
    description: str


class Trait(BaseModel):
    """Represents a common trait with its levels."""

    name: str
    levels: List[TraitLevel] = Field(default_factory=list)


def extract_trait_descriptions(pdf_path: Path) -> Dict[str, Trait]:
    """Extract trait descriptions from the PDF."""
    traits: Dict[str, Trait] = {name: Trait(name=name) for name in COMMON_TRAITS}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        # Split into lines for processing
        lines = full_text.split("\n")

        current_trait: Optional[str] = None
        current_level: Optional[int] = None
        current_description: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this is a trait name
            for trait_name in COMMON_TRAITS:
                if trait_name.upper() in line.upper() and len(line) < 50:
                    # Save previous trait if exists
                    if current_trait and current_level and current_description:
                        traits[current_trait].levels.append(
                            TraitLevel(level=current_level, description=" ".join(current_description))
                        )

                    # Start new trait
                    current_trait = trait_name
                    current_level = None
                    current_description = []
                    break

            # Check for level indicators (Level 1, Level 2, etc.)
            level_match = re.search(r"(?:^|\s)(?:Level\s*)?(\d+)[:\-]?\s*", line, re.I)
            if level_match:
                # Save previous level if exists
                if current_trait and current_level and current_description:
                    traits[current_trait].levels.append(
                        TraitLevel(level=current_level, description=" ".join(current_description))
                    )

                # Start new level
                current_level = int(level_match.group(1))
                # Extract description (everything after the level number)
                description = re.sub(r"(?:^|\s)(?:Level\s*)?\d+[:\-]?\s*", "", line, flags=re.I).strip()
                current_description = [description] if description else []
            elif current_trait and current_level:
                # This might be a continuation of the current level description
                if line and len(line) > 5:
                    current_description.append(line)

            i += 1

        # Don't forget the last level
        if current_trait and current_level and current_description:
            traits[current_trait].levels.append(
                TraitLevel(level=current_level, description=" ".join(current_description))
            )

    except Exception as e:
        console.print(f"[red]Error extracting traits from PDF:[/red] {e}")
        import traceback

        traceback.print_exc()

    return traits


@click.command()
@click.option(
    "--pdf-path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the traits booklet PDF",
)
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Data directory containing the PDF",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory (defaults to same as PDF)",
)
def main(pdf_path: Optional[Path], data_dir: Path, output_dir: Optional[Path]):
    """Parse the Death May Die traits booklet PDF."""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Traits Booklet Parser[/bold cyan]\n"
            "Extracts trait information from the PDF booklet",
            border_style="cyan",
        )
    )

    # Determine PDF path
    if pdf_path:
        pdf_file = pdf_path
    else:
        pdf_file = data_dir / TRAITS_BOOKLET_FILENAME

    if not pdf_file.exists():
        console.print(f"[red]PDF not found at {pdf_file}[/red]")
        console.print("Download it from: https://makecraftgame.com/wp-content/uploads/2023/09/Booklet.pdf")
        sys.exit(1)

    # Determine output directory
    if output_dir:
        out_dir = output_dir
    else:
        out_dir = pdf_file.parent

    console.print(f"\n[cyan]Parsing PDF: {pdf_file}[/cyan]")

    # Extract trait descriptions
    traits = extract_trait_descriptions(pdf_file)

    # Output results
    console.print("\n[green]Extracted traits:[/green]")
    for trait_name, trait in traits.items():
        console.print(f"  {trait_name}: {len(trait.levels)} levels")

    # Save to JSON
    output_file = out_dir / OUTPUT_JSON
    traits_dict = {name: trait.model_dump() for name, trait in traits.items()}
    with open(output_file, "w") as f:
        json.dump(traits_dict, f, indent=2)

    console.print(f"\n[green]✓ Saved trait data to {output_file}[/green]")
    console.print("\n[green]✓ Parsing complete![/green]")


if __name__ == "__main__":
    main()

