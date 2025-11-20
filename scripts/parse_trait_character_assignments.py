#!/usr/bin/env python3
"""
Parse pages 3-4 of traits_booklet.pdf to extract which characters have which common traits.

This helps us understand trait distribution and can be used to:
- Verify character data
- Find characters for OCR extraction
- Understand trait combinations
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Final, List, Set

try:
    import click
    import pdfplumber
    from rich.console import Console
    from rich.table import Table
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
FILENAME_TRAITS_BOOKLET: Final[str] = "traits_booklet.pdf"
DATA_DIR: Final[str] = "data"

# Common trait names
COMMON_TRAITS: Final[List[str]] = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


def extract_character_name(line: str) -> tuple[str, int] | None:
    """Extract character name and number from a line like 'Al Capone (20)' or 'Lord Adam Benchley (7)'.
    
    Returns:
        Tuple of (character_name, character_number) or None if not found
    """
    # Pattern: "Name (Number)" or "Name, Name (Number)"
    # Handle names with quotes, apostrophes, titles, etc.
    pattern = r"([A-Z][a-zA-Z\s'\-\.]+?)\s*\((\d+)\)"
    match = re.search(pattern, line)
    if match:
        name = match.group(1).strip()
        number = int(match.group(2))
        return (name, number)
    return None


def parse_trait_section(text: str, trait_name: str) -> List[tuple[str, int]]:
    """Parse a trait section to extract character names and numbers.
    
    Args:
        text: Full text from pages 3-4
        trait_name: Name of the trait (e.g., "Swiftness", "Toughness")
        
    Returns:
        List of (character_name, character_number) tuples
    """
    characters: List[tuple[str, int]] = []
    
    # Find the trait section
    lines = text.split("\n")
    in_section = False
    
    for i, line in enumerate(lines):
        # Look for trait name as heading
        # Handle both "Trait Appendix" and "Trait Common Trait Quick" patterns
        trait_upper = trait_name.upper()
        line_upper = line.upper()
        if trait_upper in line_upper and ("Appendix" in line or "Common Trait" in line or "trait" in line.lower()):
            in_section = True
            continue
        
        # Stop if we hit another trait section
        if in_section:
            for other_trait in COMMON_TRAITS:
                if other_trait != trait_name and other_trait.upper() in line.upper() and "Appendix" in line:
                    return characters
            
            # Extract character names from this line
            # Handle multiple characters per line: "Name1 (1), Name2 (2), Name3 (3)"
            # Split by comma first, then extract each
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                char_info = extract_character_name(part)
                if char_info:
                    characters.append(char_info)
    
    return characters


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
def main(data_dir: Path, output_json: Path | None):
    """Parse pages 3-4 of traits booklet to extract character-trait assignments."""
    console.print("[bold cyan]Parsing Trait Character Assignments[/bold cyan]\n")

    pdf_path = data_dir / FILENAME_TRAITS_BOOKLET
    if not pdf_path.exists():
        console.print(f"[red]Error: {pdf_path} not found![/red]")
        sys.exit(1)

    # Extract pages 3, 4, and 5 (0-indexed: 2, 3, 4)
    # Page 3-4: Swiftness, Toughness, Marksman, Stealth
    # Page 5: Arcane Mastery, Brawling
    console.print(f"[cyan]Extracting pages 3-5 from {pdf_path.name}...[/cyan]")
    text_parts: List[str] = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [2, 3, 4]:  # Pages 3, 4, and 5
            if page_num < len(pdf.pages):
                text = pdf.pages[page_num].extract_text() or ""
                text_parts.append(text)
    
    full_text = "\n".join(text_parts)
    console.print(f"[green]✓ Extracted {len(full_text)} characters of text[/green]\n")

    # Parse each trait section
    trait_characters: Dict[str, List[tuple[str, int]]] = {}
    
    for trait_name in COMMON_TRAITS:
        characters = parse_trait_section(full_text, trait_name)
        trait_characters[trait_name] = characters
        console.print(
            f"[green]✓ {trait_name}:[/green] Found {len(characters)} characters"
        )

    console.print()

    # Create summary tables
    # Table 1: Characters per trait
    table1 = Table(title="Characters per Trait")
    table1.add_column("Trait", style="cyan")
    table1.add_column("Character Count", justify="right")
    table1.add_column("Characters", style="green")

    for trait_name in COMMON_TRAITS:
        characters = trait_characters[trait_name]
        char_names = [f"{name} ({num})" for name, num in characters[:5]]
        if len(characters) > 5:
            char_names.append(f"... and {len(characters) - 5} more")
        table1.add_row(
            trait_name,
            str(len(characters)),
            ", ".join(char_names),
        )

    console.print(table1)
    console.print()

    # Table 2: Trait combinations (which characters have which trait pairs)
    console.print("[cyan]Analyzing trait combinations...[/cyan]\n")
    
    # Build character -> traits mapping
    char_to_traits: Dict[str, Set[str]] = defaultdict(set)
    for trait_name, characters in trait_characters.items():
        for char_name, char_num in characters:
            char_key = f"{char_name} ({char_num})"
            char_to_traits[char_key].add(trait_name)

    # Find characters with multiple traits
    multi_trait_chars = {
        char: traits for char, traits in char_to_traits.items() if len(traits) > 1
    }

    if multi_trait_chars:
        table2 = Table(title="Characters with Multiple Traits")
        table2.add_column("Character", style="cyan")
        table2.add_column("Traits", style="green")
        table2.add_column("Count", justify="right")

        for char, traits in sorted(multi_trait_chars.items(), key=lambda x: len(x[1]), reverse=True):
            table2.add_row(char, ", ".join(sorted(traits)), str(len(traits)))

        console.print(table2)
        console.print()

    # Save to JSON if requested
    if output_json:
        output_data = {
            "trait_characters": {
                trait: [{"name": name, "number": num} for name, num in chars]
                for trait, chars in trait_characters.items()
            },
            "character_traits": {
                char: list(traits) for char, traits in char_to_traits.items()
            },
        }
        
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓ Saved to {output_json}[/green]")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()

