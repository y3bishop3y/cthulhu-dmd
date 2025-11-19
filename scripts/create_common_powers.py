#!/usr/bin/env python3
"""
Create common_powers.json file with all common powers and their 4 levels.
Then update all character.json files to reference power names instead of full definitions.
"""

import json
import sys
from pathlib import Path
from typing import Final, List, Dict, Any

try:
    import click
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/create_common_powers.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/create_common_powers.py [options]\n\n"
        "Recommended: uv run ./scripts/create_common_powers.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"
DATA_DIR: Final[str] = "data"

# Common powers with their 4 levels
# Note: These are placeholder descriptions - you'll need to fill in the actual game text
COMMON_POWERS_DATA: Final[Dict[str, Dict[str, Any]]] = {
    "Arcane Mastery": {
        "name": "Arcane Mastery",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
    "Brawling": {
        "name": "Brawling",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
    "Marksman": {
        "name": "Marksman",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
    "Stealth": {
        "name": "Stealth",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
    "Swiftness": {
        "name": "Swiftness",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
    "Toughness": {
        "name": "Toughness",
        "is_special": False,
        "levels": [
            {"level": 1, "description": "Level 1 description - TODO: Fill in from game rules"},
            {"level": 2, "description": "Level 2 description - TODO: Fill in from game rules"},
            {"level": 3, "description": "Level 3 description - TODO: Fill in from game rules"},
            {"level": 4, "description": "Level 4 description - TODO: Fill in from game rules"},
        ],
    },
}


def create_common_powers_file(data_dir: Path) -> Path:
    """Create common_powers.json file."""
    common_powers_path = data_dir / FILENAME_COMMON_POWERS
    
    # Convert to list format
    common_powers_list = list(COMMON_POWERS_DATA.values())
    
    with open(common_powers_path, "w", encoding="utf-8") as f:
        json.dump(common_powers_list, f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]✓ Created {common_powers_path}[/green]")
    return common_powers_path


def extract_power_names_from_character(char_data: Dict[str, Any]) -> List[str]:
    """Extract common power names from character data."""
    power_names: List[str] = []
    
    if "common_powers" in char_data:
        common_powers = char_data["common_powers"]
        
        # Handle both list of dicts and list of strings
        if isinstance(common_powers, list):
            for power in common_powers:
                if isinstance(power, dict) and "name" in power:
                    power_names.append(power["name"])
                elif isinstance(power, str):
                    # Already a string reference
                    power_names.append(power)
        elif isinstance(common_powers, dict):
            # Single power as dict (shouldn't happen, but handle it)
            if "name" in common_powers:
                power_names.append(common_powers["name"])
    
    return power_names


def update_character_file(char_json_path: Path) -> bool:
    """Update character.json to use power name references."""
    try:
        with open(char_json_path, "r", encoding="utf-8") as f:
            char_data = json.load(f)
        
        # Extract power names
        power_names = extract_power_names_from_character(char_data)
        
        # Update common_powers to just be a list of names
        char_data["common_powers"] = power_names
        
        # Write back
        with open(char_json_path, "w", encoding="utf-8") as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        console.print(f"[red]Error updating {char_json_path}:[/red] {e}")
        return False


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without actually changing files",
)
def main(data_dir: Path, dry_run: bool):
    """Create common_powers.json and update character files to reference power names."""
    console.print("[bold cyan]Common Powers Refactoring[/bold cyan]\n")
    
    # Create common_powers.json
    if not dry_run:
        create_common_powers_file(data_dir)
    else:
        console.print(f"[yellow]Would create {data_dir / FILENAME_COMMON_POWERS}[/yellow]")
    
    # Find all character.json files
    character_files = list(data_dir.rglob(FILENAME_CHARACTER_JSON))
    
    if not character_files:
        console.print(f"[yellow]No character.json files found in {data_dir}[/yellow]")
        return
    
    console.print(f"\n[cyan]Found {len(character_files)} character files[/cyan]")
    
    if dry_run:
        console.print("\n[bold yellow]DRY RUN - No files will be modified[/bold yellow]\n")
        for char_file in character_files[:10]:
            with open(char_file, "r", encoding="utf-8") as f:
                char_data = json.load(f)
            power_names = extract_power_names_from_character(char_data)
            if power_names:
                console.print(f"{char_file.relative_to(data_dir)}: {power_names}")
        if len(character_files) > 10:
            console.print(f"... and {len(character_files) - 10} more")
        return
    
    # Update character files
    updated = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Updating character files...", total=len(character_files))
        
        for char_file in character_files:
            if update_character_file(char_file):
                updated += 1
            else:
                failed += 1
            progress.update(task, advance=1)
    
    console.print(f"\n[green]✓ Updated:[/green] {updated} files")
    if failed > 0:
        console.print(f"[red]✗ Failed:[/red] {failed} files")
    console.print(f"\n[cyan]Common powers file:[/cyan] {data_dir / FILENAME_COMMON_POWERS}")


if __name__ == "__main__":
    main()

