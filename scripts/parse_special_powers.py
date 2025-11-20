#!/usr/bin/env python3
"""
Parse and update special powers for all characters.

This script:
1. Parses special powers from character back card images using OCR
2. Extracts power level descriptions
3. Updates character.json files with complete special power data
4. Validates and cleans OCR text
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

try:
    import click
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_special_powers.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_special_powers.py [options]\n\n"
        "Recommended: uv run ./scripts/parse_special_powers.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.character import BackCardData, Power
from scripts.models.constants import Filename
from scripts.utils.ocr import extract_text_from_image
from scripts.parsing.text_parsing import clean_ocr_text

console = Console()


def parse_special_power_from_back_card(back_text: str, character_name: str) -> Optional[Power]:
    """Parse special power from back card text.

    Args:
        back_text: OCR text from back card
        character_name: Character name for context

    Returns:
        Power object with special power data, or None if not found
    """
    # Clean the text
    cleaned_text = clean_ocr_text(back_text, preserve_newlines=True)

    # Try to parse using BackCardData model
    try:
        back_data = BackCardData.parse_from_text(cleaned_text)
        if back_data.special_power:
            return back_data.special_power
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not parse special power for {character_name}: {e}[/yellow]"
        )

    return None


def update_character_special_power(
    char_dir: Path, special_power: Power, dry_run: bool = False
) -> bool:
    """Update character.json with special power data.

    Args:
        char_dir: Character directory
        special_power: Parsed special power
        dry_run: If True, don't write files

    Returns:
        True if updated, False otherwise
    """
    json_path = char_dir / Filename.CHARACTER_JSON

    # Load existing data
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading {json_path}: {e}[/red]")
            return False
    else:
        data = {}

    # Check if update is needed
    current_special = data.get("special_power")
    needs_update = False

    if not current_special:
        needs_update = True
    elif current_special.get("description") != special_power.levels[0].description:
        needs_update = True
    elif len(current_special.get("levels", [])) != len(special_power.levels):
        needs_update = True

    if not needs_update:
        return False

    # Update data
    # Convert Power model to dict format
    levels_list = []
    if hasattr(special_power, "levels") and special_power.levels:
        # Handle both list and single level cases
        levels_to_process = (
            special_power.levels
            if isinstance(special_power.levels, list)
            else [special_power.levels]
        )
        for level in levels_to_process:
            if hasattr(level, "level") and hasattr(level, "description"):
                levels_list.append({"level": level.level, "description": level.description})

    data["special_power"] = {
        "name": special_power.name,
        "is_special": True,
        "levels": levels_list,
    }

    # Write updated file
    if not dry_run:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return True


@click.command()
@click.option(
    "--character-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Specific character directory to parse",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default="data",
    help="Root data directory to process all characters",
)
@click.option(
    "--season",
    type=str,
    help="Specific season to process (e.g., 'season1', 'unknowable-box')",
)
@click.option(
    "--character",
    type=str,
    help="Specific character name to parse (e.g., 'adam')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without writing files",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force re-parsing even if special power already exists",
)
def main(
    character_dir: Optional[Path],
    data_dir: Path,
    season: Optional[str],
    character: Optional[str],
    dry_run: bool,
    force: bool,
):
    """Parse and update special powers for characters."""
    console.print(
        "[bold cyan]Special Power Parser[/bold cyan]\n"
        "Parsing special powers from character back cards\n"
    )

    # Determine which characters to process
    characters_to_process: List[Path] = []

    if character_dir:
        characters_to_process = [character_dir]
    elif character and season:
        char_path = data_dir / season / character
        if char_path.exists():
            characters_to_process = [char_path]
        else:
            console.print(f"[red]Error: Character directory not found: {char_path}[/red]")
            sys.exit(1)
    elif season:
        season_dir = data_dir / season
        if season_dir.exists():
            characters_to_process = [
                d for d in season_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
            ]
        else:
            console.print(f"[red]Error: Season directory not found: {season_dir}[/red]")
            sys.exit(1)
    else:
        # Process all characters
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir() and not season_dir.name.startswith("."):
                characters_to_process.extend(
                    [d for d in season_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
                )

    if not characters_to_process:
        console.print("[yellow]No characters found to process[/yellow]")
        return

    console.print(f"[green]Found {len(characters_to_process)} characters to process[/green]\n")

    # Process each character
    updated_count = 0
    skipped_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing characters...", total=len(characters_to_process))

        for char_dir in characters_to_process:
            char_name = char_dir.name
            progress.update(task, description=f"Processing {char_name}...")

            # Check if back card exists
            # Prefer preprocessed OCR version, then WebP for color, then JPG
            back_path = None
            for candidate_name in [
                "back_ocr_preprocessed.png",
                "back_ocr_preprocessed.tiff",
                "back.webp",
                "back.jpg",
                "back.jpeg",
            ]:
                candidate = char_dir / candidate_name
                if candidate.exists():
                    back_path = candidate
                    break

            if not back_path:
                console.print(f"[yellow]Skipping {char_name}: no back card image[/yellow]")
                skipped_count += 1
                progress.update(task, advance=1)
                continue

            # Check if already has special power (unless force)
            if not force:
                json_path = char_dir / Filename.CHARACTER_JSON
                if json_path.exists():
                    try:
                        with open(json_path, encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("special_power") and data["special_power"].get("name"):
                            # Check if description looks complete (not just OCR garbage)
                            desc = (
                                data["special_power"].get("levels", [{}])[0].get("description", "")
                            )
                            if desc and len(desc) > 10 and not desc.startswith("Goin"):
                                console.print(
                                    f"[cyan]Skipping {char_name}: already has special power[/cyan]"
                                )
                                skipped_count += 1
                                progress.update(task, advance=1)
                                continue
                    except Exception:
                        pass

            try:
                # Extract text from back card
                back_text = extract_text_from_image(back_path)
                if not back_text:
                    console.print(
                        f"[yellow]Warning: No text extracted from {char_name} back card[/yellow]"
                    )
                    error_count += 1
                    progress.update(task, advance=1)
                    continue

                # Parse special power
                special_power = parse_special_power_from_back_card(back_text, char_name)

                if not special_power:
                    console.print(
                        f"[yellow]Warning: Could not parse special power for {char_name}[/yellow]"
                    )
                    error_count += 1
                    progress.update(task, advance=1)
                    continue

                # Update character.json
                if update_character_special_power(char_dir, special_power, dry_run):
                    updated_count += 1
                    if dry_run:
                        console.print(
                            f"[green]Would update {char_name}: {special_power.name}[/green]"
                        )
                    else:
                        console.print(f"[green]Updated {char_name}: {special_power.name}[/green]")

            except Exception as e:
                console.print(f"[red]Error processing {char_name}: {e}[/red]")
                error_count += 1

            progress.update(task, advance=1)

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Updated: {updated_count}")
    console.print(f"  Skipped: {skipped_count}")
    console.print(f"  Errors: {error_count}")
    console.print(f"  Total: {len(characters_to_process)}")

    if dry_run:
        console.print("\n[yellow]Dry run mode - no files were modified[/yellow]")


if __name__ == "__main__":
    main()
