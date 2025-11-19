#!/usr/bin/env python3
"""
Update VCTK speaker metadata from speaker-info.txt file.
This script parses the official VCTK speaker-info.txt file and updates
the JSON metadata file with accurate speaker information.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Final, Optional

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/update_speaker_metadata.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/update_speaker_metadata.py [options]\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
SPEAKER_METADATA_FILE: Final[str] = "scripts/data/vctk_speakers.json"


def parse_speaker_info_txt(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Parse VCTK speaker-info.txt file.
    Expected format (tab-separated):
    ID  AGE GENDER ACCENTS REGION
    """
    speakers = {}

    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        return speakers

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Skip header if present
        start_idx = 0
        if lines and ("ID" in lines[0] or "AGE" in lines[0]):
            start_idx = 1

        for line in lines[start_idx:]:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try tab-separated first, then space-separated
            parts = line.split("\t") if "\t" in line else line.split()
            if len(parts) < 3:
                continue

            speaker_id = parts[0].strip()
            age_str = parts[1].strip() if len(parts) > 1 else ""
            gender = parts[2].strip().lower() if len(parts) > 2 else ""
            accent = parts[3].strip() if len(parts) > 3 else "English"
            region = parts[4].strip() if len(parts) > 4 else None

            # Parse age
            age = None
            try:
                if age_str:
                    age = int(age_str)
            except ValueError:
                pass

            # Build description
            desc_parts = []
            if gender:
                desc_parts.append(gender.capitalize())
            if age:
                desc_parts.append(f"age {age}")
            if accent:
                desc_parts.append(f"{accent} accent")
            if region:
                desc_parts.append(f"({region})")

            description = ", ".join(desc_parts) if desc_parts else "Unknown"

            speakers[speaker_id] = {
                "name": f"Speaker {speaker_id[1:]}" if speaker_id.startswith("p") else speaker_id,
                "age": age,
                "gender": gender if gender else None,
                "accent": accent,
                "region": region,
                "description": description,
            }

    except Exception as e:
        console.print(f"[red]Error parsing file: {e}[/red]")

    return speakers


@click.command()
@click.option(
    "--speaker-info-file",
    type=click.Path(path_type=Path),
    help="Path to VCTK speaker-info.txt file",
)
@click.option(
    "--output",
    default=SPEAKER_METADATA_FILE,
    type=click.Path(path_type=Path),
    help="Output JSON file path",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without writing",
)
def main(speaker_info_file: Optional[Path], output: Path, dry_run: bool):
    """Update VCTK speaker metadata from speaker-info.txt file."""

    console.print(
        Panel.fit(
            "[bold cyan]VCTK Speaker Metadata Updater[/bold cyan]\n"
            "Updates speaker metadata from VCTK speaker-info.txt file",
            border_style="cyan",
        )
    )

    if not speaker_info_file:
        console.print(
            "\n[yellow]Usage:[/yellow]\n"
            "  ./scripts/update_speaker_metadata.py --speaker-info-file <path>\n\n"
            "[cyan]To get speaker-info.txt:[/cyan]\n"
            "  1. Download VCTK corpus from: https://datashare.ed.ac.uk/handle/10283/3443\n"
            "  2. Extract speaker-info.txt from the dataset\n"
            "  3. Run this script with --speaker-info-file pointing to that file\n"
        )
        sys.exit(1)

    # Parse speaker-info.txt
    console.print(f"\n[cyan]Parsing {speaker_info_file}...[/cyan]")
    new_speakers = parse_speaker_info_txt(speaker_info_file)

    if not new_speakers:
        console.print("[red]No speaker data found in file[/red]")
        sys.exit(1)

    console.print(f"[green]Found {len(new_speakers)} speakers[/green]")

    # Load existing metadata
    existing_metadata = {}
    if output.exists():
        try:
            with open(output, encoding="utf-8") as f:
                data = json.load(f)
                # Remove comment key
                existing_metadata = {k: v for k, v in data.items() if not k.startswith("_")}
            console.print(f"[cyan]Loaded {len(existing_metadata)} existing entries[/cyan]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load existing file: {e}[/yellow]")

    # Merge: new data takes precedence
    updated_count = 0
    new_count = 0

    for speaker_id, speaker_data in new_speakers.items():
        if speaker_id in existing_metadata:
            updated_count += 1
        else:
            new_count += 1
        existing_metadata[speaker_id] = speaker_data

    console.print(f"\n[green]Would update:[/green] {updated_count} speakers")
    console.print(f"[green]Would add:[/green] {new_count} speakers")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    # Write updated metadata
    output_data = {
        "_comment": "VCTK Speaker Metadata - This file contains speaker information for the VCTK TTS model. Updated from official VCTK speaker-info.txt file. Note: VCTK dataset does NOT include American accents - it focuses on British Isles accents (English, Scottish, Irish, Northern Irish).",
        **existing_metadata,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    console.print(f"\n[green]✓ Updated {output}[/green]")
    console.print(f"[green]Total speakers: {len(existing_metadata)}[/green]")


if __name__ == "__main__":
    main()

