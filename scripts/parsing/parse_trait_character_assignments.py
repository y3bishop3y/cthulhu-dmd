#!/usr/bin/env python3
"""
Parse pages 3-5 of traits_booklet.pdf to extract which characters have which common traits.

This helps us understand trait distribution and can be used to:
- Verify character data
- Find characters for OCR extraction
- Understand trait combinations

Parsing logic is encapsulated in Pydantic models for better organization.
"""

import json
import sys
from pathlib import Path
from typing import Final, Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table

    from scripts.models.constants import CommonPower, Filename
    from scripts.models.trait_assignments import TraitCharacterAssignments
    from scripts.utils.pdf import extract_text_from_pdf
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_trait_character_assignments.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_trait_character_assignments.py [options]\n\n"
        "Recommended: uv run ./scripts/parse_trait_character_assignments.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
DATA_DIR: Final[str] = "data"


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--output-json",
    type=click.Path(path_type=Path),
    help="Output JSON file with character-trait assignments (optional)",
)
def main(data_dir: Path, output_json: Optional[Path]):
    """Parse pages 3-5 of traits booklet to extract character-trait assignments."""
    console.print("[bold cyan]Parsing Trait Character Assignments[/bold cyan]\n")

    pdf_path = data_dir / Filename.TRAITS_BOOKLET
    if not pdf_path.exists():
        console.print(f"[red]Error: {pdf_path} not found![/red]")
        sys.exit(1)

    # Extract pages 3, 4, and 5
    # Page 3-4: Swiftness, Toughness, Marksman, Stealth
    # Page 5: Arcane Mastery, Brawling
    console.print(f"[cyan]Extracting pages 3-5 from {pdf_path.name}...[/cyan]")
    # Note: start_page/end_page are 0-indexed in extract_text_from_pdf, so pages 3-5 are indices 2-4
    full_text = extract_text_from_pdf(pdf_path, start_page=2, end_page=5)
    console.print(f"[green]✓ Extracted {len(full_text)} characters of text[/green]\n")

    # Parse using Pydantic model
    assignments = TraitCharacterAssignments.parse_from_text(full_text)

    # Display parsed results
    for trait_name in [cp.value for cp in CommonPower]:
        section = assignments.get_trait_section(trait_name)
        if section:
            console.print(
                f"[green]✓ {trait_name}:[/green] Found {section.character_count} characters"
            )

    console.print()

    # Create summary tables
    # Table 1: Characters per trait
    table1 = Table(title="Characters per Trait")
    table1.add_column("Trait", style="cyan")
    table1.add_column("Character Count", justify="right")
    table1.add_column("Characters", style="green")

    for trait_name in [cp.value for cp in CommonPower]:
        section = assignments.get_trait_section(trait_name)
        if section:
            char_names = section.character_names[:5]
            if len(section.characters) > 5:
                char_names.append(f"... and {len(section.characters) - 5} more")
            table1.add_row(
                trait_name,
                str(section.character_count),
                ", ".join(char_names),
            )

    console.print(table1)
    console.print()

    # Table 2: Trait combinations (which characters have which trait pairs)
    console.print("[cyan]Analyzing trait combinations...[/cyan]\n")

    multi_trait_chars = assignments.characters_with_multiple_traits

    if multi_trait_chars:
        table2 = Table(title="Characters with Multiple Traits")
        table2.add_column("Character", style="cyan")
        table2.add_column("Traits", style="green")
        table2.add_column("Count", justify="right")

        for char, traits in sorted(multi_trait_chars.items(), key=lambda x: len(x[1]), reverse=True):
            table2.add_row(char, ", ".join(sorted(traits)), str(len(traits)))

        console.print(table2)
        console.print()

    # Display summary statistics
    stats = assignments.get_summary_stats()
    console.print(f"[cyan]Summary:[/cyan] {stats['total_traits']} traits, "
                  f"{stats['total_characters']} characters, "
                  f"{stats['characters_with_multiple_traits']} with multiple traits\n")

    # Save to JSON if requested
    if output_json:
        output_data = {
            "trait_characters": {
                trait_name: [
                    {"name": char.name, "number": char.number}
                    for char in section.characters
                ]
                for trait_name, section in assignments.trait_sections.items()
            },
            "character_traits": {
                char: list(traits) for char, traits in assignments.character_to_traits.items()
            },
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Saved to {output_json}[/green]")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()

