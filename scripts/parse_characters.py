#!/usr/bin/env python3
"""
Parse character card images to extract character data.
Extracts name, location, motto, story from front.jpg
and powers/abilities from back.jpg.
"""

import json
import sys
from pathlib import Path
from typing import Final, List, Optional, Tuple

try:
    import click
    import yaml
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

    from scripts.models.character import CharacterData
    from scripts.models.constants import CommonPower, Filename
    from scripts.utils.ocr import extract_text_from_image
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_characters.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_characters.py [options]\n\n"
        "Note: You may also need to install Tesseract OCR:\n"
        "  macOS: brew install tesseract\n"
        "  Linux: sudo apt-get install tesseract-ocr\n"
        "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
OUTPUT_FORMAT_JSON: Final[str] = "json"
OUTPUT_FORMAT_YAML: Final[str] = "yaml"

# Get common power names as list for backward compatibility
COMMON_POWERS: Final[List[str]] = [power.value for power in CommonPower]


# OCR functions now imported from utils/ocr.py
# Preprocessing and extraction functions are available via:
# - preprocess_image_for_ocr(image_path)
# - extract_text_from_image(image_path)


# Normalization and cleaning functions now imported from utils/parsing.py
# Use:
# - normalize_dice_symbols(text)
# - normalize_red_swirl_symbols(text)
# - clean_ocr_text(text, preserve_newlines=True/False)


# Front card parsing is now encapsulated in FrontCardData.parse_from_text()


# Back card parsing is now encapsulated in BackCardData.parse_from_text()


# Issue detection is now encapsulated in CharacterData.detect_issues()


def load_existing_character_json(char_dir: Path) -> Optional[CharacterData]:
    """Load existing character.json if it exists."""
    json_path = char_dir / Filename.CHARACTER_JSON
    if not json_path.exists():
        return None

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        # Convert dict to CharacterData model
        return CharacterData(**data)
    except (json.JSONDecodeError, Exception) as e:
        console.print(
            f"[yellow]Warning: Could not load existing {Filename.CHARACTER_JSON}: {e}[/yellow]"
        )
        return None


# Merging is now encapsulated in CharacterData.merge_with()


def parse_character_images(
    front_path: Path,
    back_path: Path,
    story_file: Optional[Path] = None,
    existing_data: Optional[CharacterData] = None,
) -> Tuple[CharacterData, List[str]]:
    """Parse both front and back images for a character, returning data and issues."""
    console.print("[cyan]Parsing images for character...[/cyan]")

    # Extract text from images
    console.print("  Extracting text from front image...")
    front_text = extract_text_from_image(front_path)
    if not front_text:
        console.print("[yellow]Warning: No text extracted from front image[/yellow]")

    console.print("  Extracting text from back image...")
    back_text = extract_text_from_image(back_path)
    if not back_text:
        console.print("[yellow]Warning: No text extracted from back image[/yellow]")

    # Use HTML-extracted story if available
    story_text = None
    if story_file and story_file.exists():
        story_text = story_file.read_text(encoding="utf-8").strip()
        console.print(f"  Using HTML-extracted story (length: {len(story_text)} chars)")

    # Parse using Pydantic models
    parsed_data = CharacterData.from_images(front_text, back_text, story_text)
    console.print(
        f"  Parsed: name={parsed_data.name}, location={parsed_data.location}, "
        f"special_power={parsed_data.special_power.name if parsed_data.special_power else None}, "
        f"common_powers={len(parsed_data.common_powers)}"
    )

    # Detect parsing issues using model method
    issues = parsed_data.detect_issues()

    # Merge with existing data if provided
    if existing_data:
        merged_data = existing_data.merge_with(parsed_data, prefer_html=True)
        # Also check merged data for issues
        merged_issues = merged_data.detect_issues()
        return merged_data, merged_issues

    return parsed_data, issues


@click.command()
@click.option(
    "--character-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Directory containing front.jpg and back.jpg for a character",
)
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Root data directory to process all characters",
)
@click.option(
    "--output-format",
    type=click.Choice([OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_YAML], case_sensitive=False),
    default=OUTPUT_FORMAT_JSON,
    help="Output format for character data files",
)
@click.option(
    "--character",
    help="Specific character name to parse (e.g., 'adam')",
)
def main(
    character_dir: Optional[Path],
    data_dir: Path,
    output_format: str,
    character: Optional[str],
):
    """Parse character card images to extract character data."""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Character Parser[/bold cyan]\n"
            "Extracts character data from card images",
            border_style="cyan",
        )
    )

    # Determine which characters to process
    characters_to_process: List[Path] = []

    if character_dir:
        # Process single character directory
        characters_to_process.append(character_dir)
    elif character:
        # Find character in data directory
        char_path = None
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir():
                char_dir = season_dir / character.lower()
                if char_dir.exists():
                    char_path = char_dir
                    break
        if char_path:
            characters_to_process.append(char_path)
        else:
            console.print(f"[red]Character '{character}' not found in {data_dir}[/red]")
            sys.exit(1)
    else:
        # Process all characters in data directory
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir():
                for char_dir in season_dir.iterdir():
                    if char_dir.is_dir():
                        # Check if images exist (either as files or in zip)
                        char_name = char_dir.name
                        zip_path = char_dir / f"{char_name}.zip"
                        front_path = char_dir / Filename.FRONT
                        back_path = char_dir / Filename.BACK

                        if zip_path.exists() or (front_path.exists() and back_path.exists()):
                            characters_to_process.append(char_dir)

    if not characters_to_process:
        console.print(f"[red]No character directories found in {data_dir}[/red]")
        sys.exit(1)

    console.print(f"\n[green]Found {len(characters_to_process)} characters to process[/green]\n")

    # Process each character
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        for char_dir in characters_to_process:
            task = progress.add_task(f"Processing {char_dir.name}", total=1)

            # Prefer WebP for color, then JPG
            front_path = None
            for ext in [".webp", ".jpg", ".jpeg"]:
                candidate = char_dir / f"front{ext}"
                if candidate.exists():
                    front_path = candidate
                    break

            back_path = None
            for ext in [".webp", ".jpg", ".jpeg"]:
                candidate = char_dir / f"back{ext}"
                if candidate.exists():
                    back_path = candidate
                    break

            if not front_path or not back_path:
                console.print(f"[yellow]Skipping {char_dir.name}: missing images[/yellow]")
                progress.update(task, advance=1)
                continue

            try:
                # Load existing character.json if it exists
                existing_data = load_existing_character_json(char_dir)
                if existing_data:
                    console.print(f"  [cyan]Loaded existing {Filename.CHARACTER_JSON}[/cyan]")

                # Check for HTML-extracted story file
                story_file = char_dir / Filename.STORY_TXT
                story_path = story_file if story_file.exists() else None

                # Parse character data
                character_data, issues = parse_character_images(
                    front_path, back_path, story_path, existing_data
                )

                # Report issues
                if issues:
                    console.print("  [yellow]⚠ Parsing issues detected:[/yellow]")
                    for issue in issues:
                        console.print(f"    • {issue}")
                else:
                    console.print("  [green]✓ No parsing issues detected[/green]")

                # Save to file
                output_file = char_dir / Filename.CHARACTER_JSON
                if output_format == OUTPUT_FORMAT_JSON:
                    output_file.write_text(
                        json.dumps(character_data.model_dump(), indent=2, ensure_ascii=False)
                        + "\n",
                        encoding="utf-8",
                    )
                else:
                    output_file = char_dir / f"character.{output_format}"
                    with open(output_file, "w") as f:
                        yaml.dump(
                            character_data.model_dump(),
                            f,
                            default_flow_style=False,
                            sort_keys=False,
                        )

                console.print(f"[green]✓ Saved {output_file}[/green]")
                progress.update(task, advance=1)

            except Exception as e:
                console.print(f"[red]Error processing {char_dir.name}:[/red] {e}")
                progress.update(task, advance=1)

    console.print("\n[green]✓ Parsing complete![/green]")


if __name__ == "__main__":
    main()
