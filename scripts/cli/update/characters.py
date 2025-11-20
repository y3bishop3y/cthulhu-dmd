#!/usr/bin/env python3
"""
Update character.json files with correct common power assignments.

This script:
1. Loads trait assignments from trait_character_assignments.json
2. Updates all character.json files with correct common powers (2 per character)
3. Validates that all characters have exactly 2 common powers
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import click
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/update_character_common_powers.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/update_character_common_powers.py [options]\n\n"
        "Recommended: uv run ./scripts/update_character_common_powers.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.constants import Filename

console = Console()


def normalize_character_name(name: str) -> str:
    """Normalize character name for matching.

    Examples:
        "Lord Adam Benchley (7)" -> "adam"
        "Adam" -> "adam"
        "Lord Adam Benchley" -> "adam"
    """
    # Remove numbers and parentheses
    name = re.sub(r"\s*\(\d+\)", "", name)
    # Remove titles (Lord, Professor, etc.)
    name = re.sub(r"^(Lord|Professor|Sergeant|Dr\.|Dr)\s+", "", name, flags=re.I)
    # Get last name or first name if single word
    parts = name.split()
    if len(parts) > 1:
        # Use first name (most characters are stored by first name)
        return parts[0].lower()
    return name.lower()


def load_trait_assignments(data_dir: Path) -> Dict[str, List[str]]:
    """Load trait/character assignments from JSON file.

    Returns:
        Dictionary mapping normalized character names (lowercase) to list of common power names
    """
    json_path = data_dir / "trait_character_assignments.json"
    if not json_path.exists():
        console.print(f"[yellow]Warning: {json_path} not found[/yellow]")
        return {}

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Build mapping from character_traits section
        assignments = {}
        if "character_traits" in data:
            for char_key, powers in data["character_traits"].items():
                # Normalize character name (e.g., "Lord Adam Benchley (7)" -> "adam")
                normalized = normalize_character_name(char_key)
                if normalized:
                    assignments[normalized] = powers

        return assignments
    except Exception as e:
        console.print(f"[red]Error loading trait assignments: {e}[/red]")
        return {}


def update_character_common_powers(
    char_dir: Path, common_powers: List[str], dry_run: bool = False
) -> bool:
    """Update character.json with common powers.

    Args:
        char_dir: Character directory
        common_powers: List of common power names (should be 2)
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
    current_powers = data.get("common_powers", [])
    if isinstance(current_powers, list) and len(current_powers) == 2:
        # Check if they match (order doesn't matter)
        if set(current_powers) == set(common_powers):
            return False  # Already correct

    # Update data
    data["common_powers"] = common_powers

    # Write updated file
    if not dry_run:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return True


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default="data",
    help="Root data directory",
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
    help="Show what would be updated without writing files",
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Only validate, don't update",
)
def main(
    data_dir: Path,
    character: Optional[str],
    season: Optional[str],
    dry_run: bool,
    validate_only: bool,
):
    """Update character.json files with correct common power assignments."""
    console.print(
        "[bold cyan]Common Powers Updater[/bold cyan]\n"
        "Updating character.json files with correct common power assignments\n"
    )

    # Load trait assignments
    assignments = load_trait_assignments(data_dir)
    if not assignments:
        console.print("[red]Error: No trait assignments found[/red]")
        sys.exit(1)

    console.print(f"[green]Loaded {len(assignments)} character assignments[/green]\n")

    # Find characters to process
    characters_to_process: List[Path] = []

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

    # Process characters
    updated_count = 0
    skipped_count = 0
    error_count = 0
    missing_count = 0
    wrong_count = 0

    issues_table = Table(title="Issues Found")
    issues_table.add_column("Character", style="cyan")
    issues_table.add_column("Issue", style="yellow")

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

            # Find assignment
            char_key = char_name.lower()
            if char_key not in assignments:
                if not validate_only:
                    issues_table.add_row(char_name, "No assignment found")
                missing_count += 1
                error_count += 1
                progress.update(task, advance=1)
                continue

            common_powers = assignments[char_key]

            # Validate we have exactly 2 powers
            if len(common_powers) != 2:
                issues_table.add_row(
                    char_name, f"Expected 2 powers, found {len(common_powers)}: {common_powers}"
                )
                wrong_count += 1
                error_count += 1
                progress.update(task, advance=1)
                continue

            # Update character.json
            if not validate_only:
                if update_character_common_powers(char_dir, common_powers, dry_run):
                    updated_count += 1
                    if dry_run:
                        console.print(
                            f"[green]Would update {char_name}: {', '.join(common_powers)}[/green]"
                        )
                    else:
                        console.print(
                            f"[green]Updated {char_name}: {', '.join(common_powers)}[/green]"
                        )
                else:
                    skipped_count += 1
            else:
                # Validation mode - check current state
                json_path = char_dir / Filename.CHARACTER_JSON
                if json_path.exists():
                    try:
                        with open(json_path, encoding="utf-8") as f:
                            data = json.load(f)
                        current_powers = data.get("common_powers", [])
                        if set(current_powers) != set(common_powers):
                            issues_table.add_row(
                                char_name,
                                f"Wrong powers: {current_powers} (should be {common_powers})",
                            )
                            wrong_count += 1
                        elif len(current_powers) != 2:
                            issues_table.add_row(
                                char_name,
                                f"Wrong count: {len(current_powers)} powers (should be 2)",
                            )
                            wrong_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        issues_table.add_row(char_name, f"Error reading file: {e}")
                        error_count += 1
                else:
                    issues_table.add_row(char_name, "No character.json file")
                    missing_count += 1

            progress.update(task, advance=1)

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Updated: {updated_count}")
    console.print(f"  Skipped: {skipped_count}")
    console.print(f"  Missing assignments: {missing_count}")
    console.print(f"  Wrong powers: {wrong_count}")
    console.print(f"  Errors: {error_count}")
    console.print(f"  Total: {len(characters_to_process)}")

    if issues_table.rows:
        console.print("\n")
        console.print(issues_table)

    if dry_run:
        console.print("\n[yellow]Dry run mode - no files were modified[/yellow]")


if __name__ == "__main__":
    main()
