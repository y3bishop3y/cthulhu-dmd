#!/usr/bin/env python3
"""
Update character.json files with statistical analysis for special power levels.

This script analyzes each special power level and adds statistical data including:
- Dice additions (green/black)
- Expected successes
- Tentacle risk
- Success increases
- Conditional effects
- Elder sign conversions
"""

import json
import sys
from pathlib import Path
from typing import Final, Optional

try:
    import click
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/update_special_powers_with_stats.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/update_special_powers_with_stats.py [options]\n\n"
        "Recommended: uv run ./scripts/update_special_powers_with_stats.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.analyze_power_statistics import analyze_power_level
from scripts.models.character import PowerLevelStatistics
from scripts.models.constants import Filename

console = Console()

# Constants
DATA_DIR: Final[str] = "data"


def update_character_special_power_stats(
    char_dir: Path, dry_run: bool = False, force: bool = False
) -> tuple[bool, Optional[str]]:
    """Update character.json with special power statistics.

    Args:
        char_dir: Character directory
        dry_run: If True, don't write files

    Returns:
        Tuple of (was_updated, error_message)
    """
    json_path = char_dir / Filename.CHARACTER_JSON

    if not json_path.exists():
        return False, f"No {Filename.CHARACTER_JSON} found"

    # Load existing data
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Error loading JSON: {e}"

    # Check if special power exists
    if "special_power" not in data or not data["special_power"]:
        return False, "No special power found"

    special_power = data["special_power"]
    power_name = special_power.get("name", "Unknown")

    # Check if levels exist
    if "levels" not in special_power or not special_power["levels"]:
        return False, "No power levels found"

    # Analyze each level
    updated = False
    for level_data in special_power["levels"]:
        level = level_data.get("level")
        description = level_data.get("description", "")

        if not level or not description:
            continue

        # Check if statistics already exist and are complete
        if not force:
            existing_stats = level_data.get("statistics")
            if existing_stats and all(
                key in existing_stats
                for key in [
                    "green_dice_added",
                    "black_dice_added",
                    "base_expected_successes",
                    "enhanced_expected_successes",
                ]
            ):
                # Statistics already exist, skip unless forced
                continue

        # Analyze this power level
        try:
            analysis = analyze_power_level(power_name, level, description)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not analyze {power_name} Level {level}: {e}[/yellow]"
            )
            continue

        # Create PowerLevelStatistics from analysis
        # Extract conditional/reroll/healing/defensive effects
        try:
            from scripts.cleanup_and_improve_common_powers import (
                extract_conditional_effects,
                extract_defensive_effects,
                extract_healing_effects,
                extract_reroll_effects,
            )

            # Extract effects from description using extraction functions
            conditional_effects = extract_conditional_effects(description)
            reroll_effects = extract_reroll_effects(description)
            healing_effects = extract_healing_effects(description)
            defensive_effects = extract_defensive_effects(description)
        except ImportError:
            # Fallback: create empty effect objects if import fails
            from pydantic import BaseModel, Field

            class EmptyEffects(BaseModel):
                is_conditional: bool = False
                conditions: list = Field(default_factory=list)
                rerolls_added: int = 0
                reroll_type: None = None
                has_reroll: bool = False
                wounds_healed: int = 0
                stress_healed: int = 0
                has_healing: bool = False
                wound_reduction: int = 0
                sanity_reduction: int = 0
                has_defensive: bool = False

            conditional_effects = EmptyEffects()
            reroll_effects = EmptyEffects()
            healing_effects = EmptyEffects()
            defensive_effects = EmptyEffects()

        # Create statistics using PowerLevelStatistics.from_analysis
        stats = PowerLevelStatistics.from_analysis(
            analysis=analysis,
            conditional_effects=conditional_effects,
            reroll_effects=reroll_effects,
            healing_effects=healing_effects,
            defensive_effects=defensive_effects,
        )

        # Update level data with statistics
        level_data["statistics"] = stats.model_dump()
        level_data["effect"] = analysis.effect
        updated = True

    if updated and not dry_run:
        # Write updated file
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return updated, None


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--character",
    type=str,
    help="Specific character name to update (e.g., 'adam')",
)
@click.option(
    "--season",
    type=str,
    help="Specific season to process (e.g., 'season1')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force update even if statistics already exist",
)
def main(
    data_dir: Path,
    character: Optional[str],
    season: Optional[str],
    dry_run: bool,
    force: bool,
):
    """Update character.json files with special power statistics."""
    console.print("[bold cyan]Updating Special Powers with Statistics[/bold cyan]\n")

    # Find characters to process
    characters_to_process: list[Path] = []

    if character and season:
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

    # Process characters
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

            was_updated, error_msg = update_character_special_power_stats(char_dir, dry_run, force)

            if error_msg:
                console.print(f"[yellow]Skipping {char_name}: {error_msg}[/yellow]")
                error_count += 1
            elif was_updated:
                updated_count += 1
                if dry_run:
                    console.print(f"[green]Would update {char_name}[/green]")
                else:
                    console.print(f"[green]Updated {char_name}[/green]")
            else:
                skipped_count += 1

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
