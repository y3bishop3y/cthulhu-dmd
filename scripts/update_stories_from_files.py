#!/usr/bin/env python3
"""
Update character.json files with stories from story.txt files.
This script finds all story.txt files and updates the corresponding character.json files.
"""

import json
import sys
from pathlib import Path
from typing import Final, Optional

try:
    import click
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/update_stories_from_files.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/update_stories_from_files.py [options]\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_STORY_TXT: Final[str] = "story.txt"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"


def update_character_json_with_story(char_dir: Path, story_text: str) -> bool:
    """Update character.json with story from story.txt file."""
    json_filepath = char_dir / FILENAME_CHARACTER_JSON

    # Load existing JSON if it exists, otherwise create new structure
    existing_data: dict = {}
    if json_filepath.exists():
        try:
            existing_data = json.loads(json_filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception) as e:
            console.print(
                f"[yellow]Warning: Could not parse {json_filepath}: {e}[/yellow]"
            )
            existing_data = {}

    # Check if story needs updating
    current_story = existing_data.get("story")
    if current_story == story_text:
        return False  # No update needed

    # Update story
    existing_data["story"] = story_text

    # Ensure structure matches CharacterData model
    if "name" not in existing_data:
        existing_data["name"] = char_dir.name.replace("-", " ").title()
    if "location" not in existing_data:
        existing_data["location"] = None
    if "motto" not in existing_data:
        existing_data["motto"] = None
    if "special_power" not in existing_data:
        existing_data["special_power"] = None
    if "common_powers" not in existing_data:
        existing_data["common_powers"] = []

    # Write updated JSON
    json_filepath.parent.mkdir(parents=True, exist_ok=True)
    json_filepath.write_text(
        json.dumps(existing_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


@click.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Directory containing character data",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def main(data_dir: Path, dry_run: bool):
    """Update character.json files with stories from story.txt files."""

    console.print(
        "[bold cyan]Updating character.json files with stories from story.txt[/bold cyan]\n"
    )

    # Find all story.txt files
    story_files = list(data_dir.rglob(FILENAME_STORY_TXT))
    console.print(f"Found {len(story_files)} story.txt files\n")

    if not story_files:
        console.print("[yellow]No story.txt files found[/yellow]")
        return

    updated_count = 0
    skipped_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing stories...", total=len(story_files))

        for story_file in story_files:
            char_dir = story_file.parent
            char_name = char_dir.name

            try:
                story_text = story_file.read_text(encoding="utf-8").strip()
                if not story_text:
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                if dry_run:
                    console.print(f"[cyan]Would update[/cyan] {char_dir / FILENAME_CHARACTER_JSON}")
                    console.print(f"  Story preview: {story_text[:100]}...")
                else:
                    if update_character_json_with_story(char_dir, story_text):
                        updated_count += 1
                        console.print(f"[green]✓ Updated[/green] {char_name}")
                    else:
                        skipped_count += 1

            except Exception as e:
                console.print(f"[red]Error processing {story_file}:[/red] {e}")

            progress.update(task, advance=1)

    console.print(f"\n[green]✓ Updated:[/green] {updated_count} characters")
    if skipped_count > 0:
        console.print(f"[yellow]Skipped:[/yellow] {skipped_count} characters (no changes needed)")
    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")


if __name__ == "__main__":
    main()

