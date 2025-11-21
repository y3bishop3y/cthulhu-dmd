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
        extract_common_powers_from_back_card,
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


def _extract_front_card_with_optimal_strategies(
    front_path: Path, quiet: bool = False
) -> Tuple[Optional[FrontCardFields], str]:
    """Extract front card using field-specific optimal strategies with fallback.

    Args:
        front_path: Path to front card image
        quiet: If True, suppress progress messages

    Returns:
        Tuple of (FrontCardFields or None, extracted text)
    """
    if not quiet:
        console.print(
            "  Extracting fields from front image (using field-specific optimal strategies)..."
        )

    try:
        front_fields = extract_front_card_fields_with_optimal_strategies(front_path)
        front_text = front_fields.to_text

        # If field extraction didn't work well, fall back to whole-card extraction
        # BUT preserve story if it was successfully extracted
        extracted_story = front_fields.story if front_fields.story else None
        if front_fields.is_empty or not front_fields.has_essential_fields:
            if not quiet:
                console.print(
                    "  Field-specific extraction incomplete, using whole-card extraction..."
                )
            front_text = extract_front_card_with_optimal_strategy(front_path)
            # Preserve story if it was extracted, even if name/location failed
            if extracted_story:
                front_fields = FrontCardFields(
                    name=None,
                    location=None,
                    motto=None,
                    story=extracted_story,
                )
            else:
                front_fields = None  # type: ignore[assignment]
        return front_fields, front_text
    except Exception as e:
        if not quiet:
            console.print(
                f"[yellow]Warning: Field-specific extraction failed ({e}), falling back to whole-card[/yellow]"
            )
        front_text = extract_front_card_with_optimal_strategy(front_path)
        return None, front_text


def _extract_back_card_with_optimal_strategies(back_path: Path, quiet: bool = False) -> str:
    """Extract back card using optimal strategy with fallback.

    Args:
        back_path: Path to back card image
        quiet: If True, suppress progress messages

    Returns:
        Extracted text from back card
    """
    if not quiet:
        console.print("  Extracting text from back image (using optimal strategy)...")

    try:
        return extract_back_card_with_optimal_strategy(back_path)
    except Exception as e:
        if not quiet:
            console.print(
                f"[yellow]Warning: Optimal strategy failed ({e}), falling back to default[/yellow]"
            )
        return extract_text_from_image(back_path)


def _extract_front_card_basic(front_path: Path, quiet: bool = False) -> str:
    """Extract front card using basic OCR (no optimal strategies).

    Args:
        front_path: Path to front card image
        quiet: If True, suppress progress messages

    Returns:
        Extracted text from front card
    """
    if not quiet:
        console.print("  Extracting text from front image...")
    return extract_text_from_image(front_path)


def _extract_back_card_basic(back_path: Path, quiet: bool = False) -> str:
    """Extract back card using basic OCR (no optimal strategies).

    Args:
        back_path: Path to back card image
        quiet: If True, suppress progress messages

    Returns:
        Extracted text from back card
    """
    if not quiet:
        console.print("  Extracting text from back image...")
    return extract_text_from_image(back_path)


def _load_story_from_file(story_file: Optional[Path], quiet: bool = False) -> Optional[str]:
    """Load HTML-extracted story from file if available.

    Args:
        story_file: Optional path to story file
        quiet: If True, suppress progress messages

    Returns:
        Story text or None
    """
    if story_file and story_file.exists():
        story_text = story_file.read_text(encoding="utf-8").strip()
        if not quiet:
            console.print(f"  Using HTML-extracted story (length: {len(story_text)} chars)")
        return story_text
    return None


def _parse_character_data(
    front_fields: Optional[FrontCardFields],
    front_text: str,
    back_text: str,
    back_path: Optional[Path],
    story_text: Optional[str],
    use_optimal_strategies: bool = True,
    quiet: bool = False,
) -> CharacterData:
    """Parse extracted text into CharacterData model.

    Args:
        front_fields: Optional FrontCardFields from field-specific extraction
        front_text: Extracted text from front card
        back_text: Extracted text from back card
        back_path: Optional path to back card image (for region-specific common power extraction)
        story_text: Optional HTML-extracted story text
        use_optimal_strategies: If True, use region-specific common power extraction
        quiet: If True, suppress progress messages

    Returns:
        Parsed CharacterData
    """
    # Get story from field extraction if available
    extracted_story_from_fields = None
    if front_fields and front_fields.story:
        extracted_story_from_fields = front_fields.story

    if front_fields and front_fields.has_essential_fields:
        # Use field-specific extraction results
        story_to_use = story_text or extracted_story_from_fields
        front_data = front_fields.to_front_card_data(story_override=story_to_use)

        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)

        # Extract common powers from region-specific extraction if available
        common_power_names: List[str] = []
        if use_optimal_strategies and back_path and back_path.exists():
            try:
                region_powers = extract_common_powers_from_back_card(back_path)
                if region_powers:
                    common_power_names = region_powers
                    if not quiet:
                        console.print(
                            f"  Found {len(common_power_names)} common powers via region extraction: {', '.join(common_power_names)}"
                        )
            except Exception as e:
                if not quiet:
                    console.print(
                        f"[yellow]Warning: Region-specific common power extraction failed ({e}), using parsed powers[/yellow]"
                    )
                # Fall back to parsed powers
                common_power_names = [cp.name for cp in back_data.common_powers]
        else:
            # Use parsed powers from whole-card text
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
        # Fall back to standard parsing, but use field-extracted story if available
        story_to_use = story_text or extracted_story_from_fields
        parsed_data = CharacterData.from_images(front_text, back_text, story_to_use)

        # Try region-specific common power extraction even in fallback mode
        if use_optimal_strategies and back_path and back_path.exists():
            try:
                region_powers = extract_common_powers_from_back_card(back_path)
                if region_powers and len(region_powers) >= 2:
                    # Prefer region-extracted powers if we found at least 2
                    parsed_data.common_powers = region_powers
                    if not quiet:
                        console.print(
                            f"  Updated common powers via region extraction: {', '.join(region_powers)}"
                        )
            except Exception:
                # Silently fall back to parsed powers
                pass

    if not quiet:
        console.print(
            f"  Parsed: name={parsed_data.name}, location={parsed_data.location}, "
            f"special_power={parsed_data.special_power.name if parsed_data.special_power else None}, "
            f"common_powers={len(parsed_data.common_powers)}"
        )

    return parsed_data


def _merge_with_existing_data(
    parsed_data: CharacterData, existing_data: Optional[CharacterData]
) -> Tuple[CharacterData, List[str]]:
    """Merge parsed data with existing data if provided.

    Args:
        parsed_data: Newly parsed character data
        existing_data: Optional existing character data

    Returns:
        Tuple of (merged CharacterData, list of issues)
    """
    if existing_data:
        merged_data = existing_data.merge_with(parsed_data, prefer_html=True)
        merged_issues = merged_data.detect_issues()
        return merged_data, merged_issues

    issues = parsed_data.detect_issues()
    return parsed_data, issues


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

    Returns:
        Tuple of (CharacterData, list of issues)
    """
    if not quiet:
        console.print("[cyan]Parsing images for character...[/cyan]")

    # Extract text from images
    if use_optimal_strategies:
        front_fields, front_text = _extract_front_card_with_optimal_strategies(front_path, quiet)
        back_text = _extract_back_card_with_optimal_strategies(back_path, quiet)
    else:
        front_text = _extract_front_card_basic(front_path, quiet)
        front_fields = None
        back_text = _extract_back_card_basic(back_path, quiet)

    # Validate extraction results
    if not front_text:
        if not quiet:
            console.print("[yellow]Warning: No text extracted from front image[/yellow]")
    if not back_text:
        if not quiet:
            console.print("[yellow]Warning: No text extracted from back image[/yellow]")

    # Load HTML-extracted story if available
    story_text = _load_story_from_file(story_file, quiet)

    # Parse extracted text into CharacterData
    parsed_data = _parse_character_data(
        front_fields, front_text, back_text, back_path, story_text, use_optimal_strategies, quiet
    )

    # Merge with existing data if provided
    return _merge_with_existing_data(parsed_data, existing_data)


def _display_header(verify: bool) -> None:
    """Display the header banner.

    Args:
        verify: Whether in verification mode
    """
    mode_text = "Verification Mode" if verify else "Parsing Mode"
    console.print(
        Panel.fit(
            f"[bold cyan]Death May Die Character Parser[/bold cyan]\n"
            f"{mode_text}: Extracts character data from card images",
            border_style="cyan",
        )
    )


def _validate_season(data_dir: Path, season: Optional[str]) -> None:
    """Validate season directory if provided.

    Args:
        data_dir: Root data directory
        season: Optional season name to validate

    Raises:
        SystemExit: If season directory doesn't exist
    """
    if season:
        season_path = data_dir / season
        if not season_path.exists() or not season_path.is_dir():
            console.print(f"[red]Season directory '{season}' not found in {data_dir}[/red]")
            sys.exit(1)
        console.print(f"[cyan]Processing season: {season}[/cyan]\n")


def _find_image_files(char_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Find front and back image files for a character directory.

    Args:
        char_dir: Character directory to search

    Returns:
        Tuple of (front_path, back_path), either may be None
    """
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

    return front_path, back_path


def _find_characters_to_process(
    character_dir: Optional[Path],
    data_dir: Path,
    character: Optional[str],
    season: Optional[str],
) -> List[Path]:
    """Determine which characters to process based on arguments.

    Args:
        character_dir: Optional single character directory
        data_dir: Root data directory
        character: Optional character name to find
        season: Optional season to limit search

    Returns:
        List of character directories to process

    Raises:
        SystemExit: If character not found or no characters found
    """
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
                    front_path, _ = _find_image_files(char_dir)

                    # Include if has front image or zip (back may be missing for some seasons)
                    if zip_path.exists() or front_path:
                        characters_to_process.append(char_dir)

    if not characters_to_process:
        console.print(f"[red]No character directories found in {data_dir}[/red]")
        sys.exit(1)

    return characters_to_process


def _process_character_verify(
    char_dir: Path,
    front_path: Path,
    back_path: Optional[Path],
    use_optimal_strategies: bool,
) -> None:
    """Process a character in verification mode (show extracted fields without saving).

    Args:
        char_dir: Character directory
        front_path: Path to front card image
        back_path: Optional path to back card image
        use_optimal_strategies: Whether to use optimal OCR strategies
    """
    existing_data = load_existing_character_json(char_dir)
    story_file = char_dir / Filename.STORY_TXT
    story_path = story_file if story_file.exists() else None

    character_data, issues = parse_character_images(
        front_path,
        back_path or front_path,
        story_path,
        None,
        use_optimal_strategies,
        quiet=True,
    )
    _display_extraction_report(char_dir, character_data, existing_data, issues)


def _save_character_data(
    char_dir: Path, character_data: CharacterData, output_format: str
) -> None:
    """Save character data to file.

    Args:
        char_dir: Character directory
        character_data: Character data to save
        output_format: Output format (json or yaml)
    """
    output_file = char_dir / Filename.CHARACTER_JSON
    if output_format == OUTPUT_FORMAT_JSON:
        output_file.write_text(
            json.dumps(character_data.model_dump(), indent=2, ensure_ascii=False) + "\n",
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


def _process_character_normal(
    char_dir: Path,
    front_path: Path,
    back_path: Optional[Path],
    use_optimal_strategies: bool,
    output_format: str,
) -> None:
    """Process a character in normal mode (parse and save).

    Args:
        char_dir: Character directory
        front_path: Path to front card image
        back_path: Optional path to back card image
        use_optimal_strategies: Whether to use optimal OCR strategies
        output_format: Output format (json or yaml)
    """
    existing_data = load_existing_character_json(char_dir)
    if existing_data:
        console.print(f"  [cyan]Loaded existing {Filename.CHARACTER_JSON}[/cyan]")

    story_file = char_dir / Filename.STORY_TXT
    story_path = story_file if story_file.exists() else None

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
    _save_character_data(char_dir, character_data, output_format)


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
) -> None:
    """Parse character card images to extract character data."""
    _display_header(verify)
    _validate_season(data_dir, season)

    characters_to_process = _find_characters_to_process(
        character_dir, data_dir, character, season
    )

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

            front_path, back_path = _find_image_files(char_dir)

            if not front_path:
                console.print(f"[yellow]Skipping {char_dir.name}: missing front image[/yellow]")
                progress.update(task, advance=1)
                continue

            try:
                if verify:
                    _process_character_verify(
                        char_dir, front_path, back_path, use_optimal_strategies
                    )
                else:
                    _process_character_normal(
                        char_dir, front_path, back_path, use_optimal_strategies, output_format
                    )
                progress.update(task, advance=1)
            except Exception as e:
                import traceback
                console.print(f"[red]Error processing {char_dir.name}:[/red] {e}")
                console.print(f"[red]Traceback:[/red]\n{traceback.format_exc()}")
                progress.update(task, advance=1)

    console.print("\n[green]✓ Parsing complete![/green]")


if __name__ == "__main__":
    main()
