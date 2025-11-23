#!/usr/bin/env python3
"""
Reorganize data directory structure according to Phase 1 plan.

This script:
1. Moves season1/characters/* to season1/* (flatten structure)
2. Moves character-book.pdf from season1/characters/ to season1/
3. Optionally archives or removes *_annotated.png files
4. Optionally removes *_ocr_preprocessed.png files
5. Verifies consistent structure across all seasons
"""

import shutil
import sys
from pathlib import Path
from typing import List

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.prompt import Confirm
except ImportError:
    print("Error: Missing rich library. Install with: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARCHIVE_DIR = DATA_DIR / ".archive"


def find_annotated_files(data_dir: Path) -> List[Path]:
    """Find all *_annotated.png files."""
    return list(data_dir.rglob("*_annotated.png"))


def find_ocr_preprocessed_files(data_dir: Path) -> List[Path]:
    """Find all *_ocr_preprocessed.png files."""
    return list(data_dir.rglob("*_ocr_preprocessed.png"))


def move_season1_characters():
    """Move season1/characters/* to season1/*."""
    season1_dir = DATA_DIR / "season1"
    characters_dir = season1_dir / "characters"

    if not characters_dir.exists():
        console.print("[yellow]season1/characters/ directory not found. Skipping.[/yellow]")
        return False

    console.print("[cyan]Moving season1/characters/* to season1/...[/cyan]")

    # Get all items in characters directory
    items = list(characters_dir.iterdir())

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Moving files...", total=len(items))

        for item in items:
            if item.is_dir():
                # Move character directory
                dest = season1_dir / item.name
                if dest.exists():
                    console.print(
                        f"[yellow]Warning: {dest} already exists. Skipping {item.name}[/yellow]"
                    )
                else:
                    shutil.move(str(item), str(dest))
                    progress.update(task, description=f"Moved {item.name}")
            elif item.name == "character-book.pdf":
                # Move PDF to season1 root
                dest = season1_dir / item.name
                if dest.exists():
                    console.print(f"[yellow]Warning: {dest} already exists. Skipping[/yellow]")
                else:
                    shutil.move(str(item), str(dest))
                    progress.update(task, description="Moved character-book.pdf")
            else:
                console.print(f"[yellow]Skipping unexpected file: {item.name}[/yellow]")

            progress.update(task, advance=1)

    # Remove empty characters directory
    try:
        characters_dir.rmdir()
        console.print("[green]✓ Removed empty characters/ directory[/green]")
    except OSError:
        console.print(
            "[yellow]Warning: characters/ directory not empty or cannot be removed[/yellow]"
        )

    return True


def archive_files(files: List[Path], archive_name: str = "annotated"):
    """Archive files to .archive directory."""
    if not files:
        return

    archive_subdir = ARCHIVE_DIR / archive_name
    archive_subdir.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]Archiving {len(files)} files to {archive_subdir}...[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Archiving...", total=len(files))

        for file_path in files:
            # Preserve relative path structure in archive
            rel_path = file_path.relative_to(DATA_DIR)
            dest = archive_subdir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(file_path), str(dest))
            progress.update(task, advance=1)

    console.print(f"[green]✓ Archived {len(files)} files[/green]")


def delete_files(files: List[Path], file_type: str = "files"):
    """Delete files."""
    if not files:
        return

    console.print(f"[cyan]Deleting {len(files)} {file_type}...[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting...", total=len(files))

        for file_path in files:
            try:
                file_path.unlink()
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]Error deleting {file_path}: {e}[/red]")

    console.print(f"[green]✓ Deleted {len(files)} {file_type}[/green]")


def verify_structure():
    """Verify all seasons follow consistent structure."""
    console.print("[cyan]Verifying directory structure...[/cyan]")

    seasons = [
        "season1",
        "season2",
        "season3",
        "season4",
        "comic-book-extras",
        "comic-book-v2",
        "extra-promos",
        "unknowable-box",
        "unspeakable-box",
    ]

    issues = []

    for season_name in seasons:
        season_dir = DATA_DIR / season_name
        if not season_dir.exists():
            continue

        # Check if characters are directly in season directory
        character_dirs = [
            d
            for d in season_dir.iterdir()
            if d.is_dir() and d.name not in ["enemies", "missions", "animation"]
        ]

        # Check for nested characters/ directory (shouldn't exist after reorganization)
        characters_subdir = season_dir / "characters"
        if characters_subdir.exists():
            issues.append(f"{season_name}: Still has characters/ subdirectory")

        # Check for character.json files
        for char_dir in character_dirs:
            char_json = char_dir / "character.json"
            if not char_json.exists():
                issues.append(f"{season_name}/{char_dir.name}: Missing character.json")

    if issues:
        console.print("[yellow]Found structure issues:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")
        return False
    else:
        console.print("[green]✓ Directory structure is consistent[/green]")
        return True


def main():
    """Main reorganization function."""
    console.print("[bold cyan]Data Directory Reorganization[/bold cyan]")
    console.print(f"Data directory: {DATA_DIR}\n")

    # Step 1: Move season1/characters/* to season1/*
    console.print("\n[bold]Step 1: Flattening season1 structure[/bold]")
    moved = move_season1_characters()
    if moved:
        console.print("[green]✓ Season1 structure flattened[/green]")
    else:
        console.print("[yellow]⚠ Season1 structure already flat or not found[/yellow]")

    # Step 2: Find annotated and OCR preprocessed files
    console.print("\n[bold]Step 2: Finding cleanup files[/bold]")
    annotated_files = find_annotated_files(DATA_DIR)
    ocr_files = find_ocr_preprocessed_files(DATA_DIR)

    console.print(f"Found {len(annotated_files)} *_annotated.png files")
    console.print(f"Found {len(ocr_files)} *_ocr_preprocessed.png files")

    # Step 3: Handle annotated files
    if annotated_files:
        console.print("\n[bold]Step 3: Handling annotated files[/bold]")
        action = Confirm.ask(
            f"Found {len(annotated_files)} *_annotated.png files. Archive or delete?", default=True
        )
        if action:
            archive_files(annotated_files, "annotated")
        else:
            if Confirm.ask("Are you sure you want to delete them?", default=False):
                delete_files(annotated_files, "*_annotated.png files")

    # Step 4: Handle OCR preprocessed files
    if ocr_files:
        console.print("\n[bold]Step 4: Handling OCR preprocessed files[/bold]")
        action = Confirm.ask(
            f"Found {len(ocr_files)} *_ocr_preprocessed.png files. Archive or delete?", default=True
        )
        if action:
            archive_files(ocr_files, "ocr_preprocessed")
        else:
            if Confirm.ask("Are you sure you want to delete them?", default=False):
                delete_files(ocr_files, "*_ocr_preprocessed.png files")

    # Step 5: Verify structure
    console.print("\n[bold]Step 5: Verifying structure[/bold]")
    verify_structure()

    console.print("\n[green]✓ Reorganization complete![/green]")


if __name__ == "__main__":
    main()
