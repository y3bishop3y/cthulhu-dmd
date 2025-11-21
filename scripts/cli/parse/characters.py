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

# Add project root to path (go up 3 levels from scripts/cli/parse/)
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import click
    import yaml
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run python scripts/cli/parse/characters.py [options]\n"
        "  2. source .venv/bin/activate && python scripts/cli/parse/characters.py [options]\n\n"
        "Note: You may also need to install Tesseract OCR:\n"
        "  macOS: brew install tesseract\n"
        "  Linux: sudo apt-get install tesseract-ocr\n"
        "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from scripts.cli.parse.parsing_models import FrontCardFields
    from scripts.models.character import CharacterData
    from scripts.models.constants import CommonPower, Filename
    from scripts.utils.ocr import extract_text_from_image
    from scripts.utils.optimal_ocr import (
        extract_back_card_with_optimal_strategy,
        extract_front_card_fields_with_optimal_strategies,
        extract_front_card_with_optimal_strategy,
    )
except ImportError as e:
    print(
        f"Error: Missing required import: {e}\n\n"
        "Make sure you're running from the project root directory.\n"
        "The project root should contain the 'scripts' directory.\n",
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


# Normalization and cleaning functions now imported from parsing/text_parsing.py
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


def _display_extraction_report(
    char_dir: Path,
    extracted_data: CharacterData,
    existing_data: Optional[CharacterData],
    issues: List[str],
) -> None:
    """Display a formatted report of extracted fields for verification."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]Character: {char_dir.name}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

    # Create a table to show extracted vs existing data
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=15)
    table.add_column("Extracted", style="green", width=40)
    table.add_column("Current JSON", style="yellow", width=40)

    # Name
    extracted_name = extracted_data.name or "[not extracted]"
    existing_name = existing_data.name if existing_data else "[no JSON]"
    name_match = "✓" if extracted_name == existing_name else "⚠"
    table.add_row("Name", f"{name_match} {extracted_name}", existing_name)

    # Location
    extracted_location = extracted_data.location or "[not extracted]"
    existing_location = existing_data.location if existing_data else "[no JSON]"
    location_match = "✓" if extracted_location == existing_location else "⚠"
    table.add_row("Location", f"{location_match} {extracted_location}", existing_location)

    # Motto
    extracted_motto = extracted_data.motto or "[not extracted]"
    existing_motto = existing_data.motto if existing_data else "[no JSON]"
    motto_match = "✓" if extracted_motto == existing_motto else "⚠"
    table.add_row("Motto", f"{motto_match} {extracted_motto}", existing_motto)

    # Story (truncated)
    extracted_story = extracted_data.story or "[not extracted]"
    existing_story = (existing_data.story if existing_data else None) or "[no JSON]"
    if (
        extracted_story != "[not extracted]"
        and isinstance(extracted_story, str)
        and len(extracted_story) > 50
    ):
        extracted_story = extracted_story[:47] + "..."
    if (
        existing_story != "[no JSON]"
        and isinstance(existing_story, str)
        and len(existing_story) > 50
    ):
        existing_story = existing_story[:47] + "..."
    story_match = "✓" if extracted_story == existing_story else "⚠"
    table.add_row("Story", f"{story_match} {extracted_story}", existing_story)

    # Special Power
    extracted_sp = (
        extracted_data.special_power.name if extracted_data.special_power else "[not extracted]"
    )
    existing_sp = (
        existing_data.special_power.name
        if existing_data and existing_data.special_power
        else "[no JSON]"
    )
    sp_match = "✓" if extracted_sp == existing_sp else "⚠"
    table.add_row("Special Power", f"{sp_match} {extracted_sp}", existing_sp)

    # Common Powers
    extracted_cp = (
        ", ".join(extracted_data.common_powers)
        if extracted_data.common_powers and len(extracted_data.common_powers) > 0
        else "[not extracted]"
    )
    existing_cp = (
        ", ".join(existing_data.common_powers)
        if existing_data and existing_data.common_powers and len(existing_data.common_powers) > 0
        else "[no JSON]"
    )
    cp_match = "✓" if extracted_cp == existing_cp else "⚠"
    table.add_row("Common Powers", f"{cp_match} {extracted_cp}", existing_cp)

    console.print(table)

    # Show issues if any
    if issues:
        console.print("\n[yellow]⚠ Parsing Issues:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("\n[green]✓ No parsing issues detected[/green]")

    console.print()


def parse_character_images(
    front_path: Path,
    back_path: Path,
    story_file: Optional[Path] = None,
    existing_data: Optional[CharacterData] = None,
    use_optimal_strategies: bool = True,
    quiet: bool = False,
) -> Tuple[CharacterData, List[str]]:
    """Parse both front and back images for a character, returning data and issues.

    Args:
        front_path: Path to front card image
        back_path: Path to back card image
        story_file: Optional path to HTML-extracted story file
        existing_data: Optional existing character data to merge with
        use_optimal_strategies: If True, use optimal OCR strategies from benchmark results
        quiet: If True, suppress progress messages
    """
    if not quiet:
        console.print("[cyan]Parsing images for character...[/cyan]")

    # Extract text from images
    front_fields: Optional[FrontCardFields] = None
    if use_optimal_strategies:
        if not quiet:
            console.print(
                "  Extracting fields from front image (using field-specific optimal strategies)..."
            )
        try:
            # Use field-specific extraction with optimal strategies
            fields_dict = extract_front_card_fields_with_optimal_strategies(front_path)
            front_fields = FrontCardFields.from_dict(fields_dict)

            # Use computed property to get combined text
            front_text = front_fields.to_text

            # If field extraction didn't work well, fall back to whole-card extraction
            if front_fields.is_empty or not front_fields.has_essential_fields:
                if not quiet:
                    console.print(
                        "  Field-specific extraction incomplete, using whole-card extraction..."
                    )
                front_text = extract_front_card_with_optimal_strategy(front_path)
                front_fields = None  # Clear fields to use parsed text instead
        except Exception as e:
            if not quiet:
                console.print(
                    f"[yellow]Warning: Field-specific extraction failed ({e}), falling back to whole-card[/yellow]"
                )
            front_text = extract_front_card_with_optimal_strategy(front_path)
            front_fields = None

        if not quiet:
            console.print("  Extracting text from back image (using optimal strategy)...")
        try:
            back_text = extract_back_card_with_optimal_strategy(back_path)
        except Exception as e:
            if not quiet:
                console.print(
                    f"[yellow]Warning: Optimal strategy failed ({e}), falling back to default[/yellow]"
                )
            back_text = extract_text_from_image(back_path)
    else:
        if not quiet:
            console.print("  Extracting text from front image...")
        front_text = extract_text_from_image(front_path)
        front_fields = None
        if not quiet:
            console.print("  Extracting text from back image...")
        back_text = extract_text_from_image(back_path)

    if not front_text:
        if not quiet:
            console.print("[yellow]Warning: No text extracted from front image[/yellow]")
    if not back_text:
        if not quiet:
            console.print("[yellow]Warning: No text extracted from back image[/yellow]")

    # Use HTML-extracted story if available
    story_text = None
    if story_file and story_file.exists():
        story_text = story_file.read_text(encoding="utf-8").strip()
        if not quiet:
            console.print(f"  Using HTML-extracted story (length: {len(story_text)} chars)")

    # Parse using Pydantic models
    # If we have field-specific extraction results, use them to enhance parsing
    if front_fields and front_fields.has_essential_fields:
        # Convert FrontCardFields to FrontCardData using model method
        front_data = front_fields.to_front_card_data(story_override=story_text)

        # Parse back card
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)

        # Combine into CharacterData
        common_power_names = [cp.name for cp in back_data.common_powers]
        parsed_data = CharacterData(
            name=front_data.name or "Unknown",
            location=front_data.location,
            motto=front_data.motto,
            story=front_data.story,
            special_power=back_data.special_power,
            common_powers=common_power_names,
        )
    else:
        # Fall back to standard parsing
        parsed_data = CharacterData.from_images(front_text, back_text, story_text)
    if not quiet:
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
@click.option(
    "--use-optimal-strategies/--no-optimal-strategies",
    default=True,
    help="Use optimal OCR strategies from benchmark results (default: --use-optimal-strategies)",
)
@click.option(
    "--season",
    type=str,
    help="Specific season directory to process (e.g., 'season1', 'season2', 'unknowable-box')",
)
@click.option(
    "--verify/--no-verify",
    default=False,
    help="Verification mode: show extracted fields without saving files (default: --no-verify)",
)
def main(
    character_dir: Optional[Path],
    data_dir: Path,
    output_format: str,
    character: Optional[str],
    use_optimal_strategies: bool,
    season: Optional[str],
    verify: bool,
):
    """Parse character card images to extract character data."""

    mode_text = "Verification Mode" if verify else "Parsing Mode"
    console.print(
        Panel.fit(
            f"[bold cyan]Death May Die Character Parser[/bold cyan]\n"
            f"{mode_text}: Extracts character data from card images",
            border_style="cyan",
        )
    )

    # Validate season directory if provided
    if season:
        season_path = data_dir / season
        if not season_path.exists() or not season_path.is_dir():
            console.print(f"[red]Season directory '{season}' not found in {data_dir}[/red]")
            sys.exit(1)
        console.print(f"[cyan]Processing season: {season}[/cyan]\n")

    # Determine which characters to process
    characters_to_process: List[Path] = []

    if character_dir:
        # Process single character directory
        characters_to_process.append(character_dir)
    elif character:
        # Find character in data directory
        char_path = None
        search_dirs = (
            [data_dir / season] if season else [s for s in data_dir.iterdir() if s.is_dir()]
        )
        for season_dir in search_dirs:
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
        # Process characters in specified season or all seasons
        season_dirs = (
            [data_dir / season] if season else [s for s in data_dir.iterdir() if s.is_dir()]
        )

        for season_dir in season_dirs:
            if not season_dir.is_dir():
                continue
            for char_dir in season_dir.iterdir():
                if char_dir.is_dir():
                    # Check if images exist (either as files or in zip)
                    char_name = char_dir.name
                    zip_path = char_dir / f"{char_name}.zip"
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

                    # Include if has front image (back may be missing for some seasons)
                    if zip_path.exists() or front_path:
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

            if not front_path:
                console.print(f"[yellow]Skipping {char_dir.name}: missing front image[/yellow]")
                progress.update(task, advance=1)
                continue

            try:
                # Load existing character.json if it exists
                existing_data = load_existing_character_json(char_dir)

                # Check for HTML-extracted story file
                story_file = char_dir / Filename.STORY_TXT
                story_path = story_file if story_file.exists() else None

                # Parse character data (only need back_path if it exists)
                if verify:
                    # In verify mode, show what was extracted
                    character_data, issues = parse_character_images(
                        front_path,
                        back_path or front_path,
                        story_path,
                        None,
                        use_optimal_strategies,
                        quiet=True,
                    )
                    _display_extraction_report(char_dir, character_data, existing_data, issues)
                else:
                    # In normal mode, merge with existing and save
                    if existing_data:
                        console.print(f"  [cyan]Loaded existing {Filename.CHARACTER_JSON}[/cyan]")

                    character_data, issues = parse_character_images(
                        front_path,
                        back_path or front_path,
                        story_path,
                        existing_data,
                        use_optimal_strategies,
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
