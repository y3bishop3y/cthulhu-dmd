#!/usr/bin/env python3
"""
Extract common power level descriptions from character cards using OCR.
Aggregate results and update common_powers.json and all character.json files.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Final, List

try:
    import click
    import cv2
    import numpy as np
    import pdfplumber
    import pytesseract
    from PIL import Image
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table

    from scripts.core.parsing.text import OCR_CORRECTIONS, clean_ocr_text
    from scripts.models.ocr_config import get_ocr_corrections
    from scripts.utils.ocr import extract_text_from_image, preprocess_image_for_ocr
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/extract_and_update_common_powers.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/extract_and_update_common_powers.py [options]\n\n"
        "Recommended: uv run ./scripts/extract_and_update_common_powers.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"
DATA_DIR: Final[str] = "data"
BACK_IMAGE_PATTERNS: Final[List[str]] = ["back.webp", "back.jpg"]

# Common power names
COMMON_POWERS: Final[List[str]] = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


# Use improved OCR utilities from utils/ocr.py
# (preprocess_image_for_ocr and extract_text_from_image are imported above)


def parse_power_levels_from_text(text: str, power_name: str) -> List[Dict[str, Any]]:
    """Parse level descriptions for a specific power from OCR text."""
    levels: List[Dict[str, Any]] = []

    # Clean text and split into lines
    # Apply additional cleanup for garbled text
    cleaned = text
    # Remove garbled uppercase patterns at start of lines
    cleaned = re.sub(r"^([A-Z]{8,})\s+", "", cleaned, flags=re.MULTILINE)
    # Fix common OCR artifacts
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    # Find the power section
    power_start_idx = None
    for i, line in enumerate(lines):
        if power_name.upper() in line.upper() and len(line) < 50:
            power_start_idx = i
            break

    if power_start_idx is None:
        return levels

    # Extract section until next power or end
    current_level = None
    current_description: List[str] = []

    for i in range(power_start_idx + 1, min(power_start_idx + 30, len(lines))):
        line = lines[i]
        line_lower = line.lower()

        # Check if we hit another power
        for other_power in COMMON_POWERS:
            if other_power != power_name and other_power.upper() in line.upper():
                if (
                    line.upper().startswith(other_power.upper())
                    or line.upper() == other_power.upper()
                ):
                    # Save current level if we have one
                    if current_level and current_description:
                        levels.append(
                            {
                                "level": current_level,
                                "description": " ".join(current_description).strip(),
                            }
                        )
                    return levels

        # Look for level indicators
        level_match = re.search(r"^(?:level\s*)?([1234])[:\-]?\s*(.*)", line_lower)
        if level_match:
            # Save previous level
            if current_level and current_description:
                levels.append(
                    {
                        "level": current_level,
                        "description": " ".join(current_description).strip(),
                    }
                )

            # Start new level
            current_level = int(level_match.group(1))
            desc_start = level_match.group(2).strip()
            current_description = [desc_start] if desc_start else []
        elif current_level:
            # Continuation of current level
            # Skip if it looks like a new power name or game rule
            if not any(
                keyword in line.upper()
                for keyword in ["YOUR TURN", "TAKE", "DRAW", "INVESTIGATE", "FIGHT", "RESOLVE"]
            ):
                current_description.append(line)

    # Save last level
    if current_level and current_description:
        levels.append(
            {
                "level": current_level,
                "description": " ".join(current_description).strip(),
            }
        )

    return levels


def extract_character_powers_from_card(back_image_path: Path) -> List[str]:
    """Extract which common powers a character has from their back card."""
    text = extract_text_from_image(back_image_path)
    if not text:
        return []

    powers_found: List[str] = []
    text_upper = text.upper()

    for power in COMMON_POWERS:
        if power.upper() in text_upper:
            # Check if it's mentioned as a power name (not just in description)
            lines = text.split("\n")
            for line in lines:
                line_upper = line.upper().strip()
                if power.upper() == line_upper or (
                    power.upper() in line_upper
                    and len(line.strip()) < 50
                    and not any(
                        keyword in line_upper
                        for keyword in ["LEVEL", "DESCRIPTION", "COMMON SKILL"]
                    )
                ):
                    if power not in powers_found:
                        powers_found.append(power)
                    break

    return powers_found


def aggregate_power_levels(
    all_extractions: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Aggregate level descriptions from multiple OCR extractions, picking best ones."""
    aggregated: Dict[str, List[Dict[str, Any]]] = {}

    for power_name in COMMON_POWERS:
        extractions = all_extractions.get(power_name, [])

        # Group by level number
        levels_by_num: Dict[int, List[str]] = defaultdict(list)

        for extraction in extractions:
            for level_data in extraction:
                level_num = level_data["level"]
                description = level_data["description"]

                # Filter out obviously bad OCR (too short, mostly symbols, etc.)
                # But be more lenient - accept shorter descriptions if they seem meaningful
                alpha_ratio = len([c for c in description if c.isalpha()]) / max(
                    len(description), 1
                )
                is_valid = (
                    len(description) > 5  # Reduced from 10
                    and alpha_ratio > 0.2  # Reduced from 0.3
                    and "TODO" not in description
                    and "Not found" not in description
                    and description.strip()  # Not just whitespace
                )
                if is_valid:
                    levels_by_num[level_num].append(description)

        # For each level, pick the longest/most complete description
        power_levels: List[Dict[str, Any]] = []
        for level_num in range(1, 5):
            descriptions = levels_by_num.get(level_num, [])
            if descriptions:
                # Pick the longest description (usually most complete)
                best_desc = max(descriptions, key=len)
                power_levels.append({"level": level_num, "description": best_desc})
            else:
                # Only use placeholder if we truly didn't find anything
                # Check if we have any levels at all - if so, use a shorter placeholder
                if any(levels_by_num.values()):
                    power_levels.append(
                        {
                            "level": level_num,
                            "description": f"Level {level_num} description - Not found in character cards",
                        }
                    )
                else:
                    # No levels found at all - use TODO placeholder
                    power_levels.append(
                        {
                            "level": level_num,
                            "description": f"Level {level_num} description - TODO: Fill in from game rules",
                        }
                    )

        aggregated[power_name] = power_levels

    return aggregated


def cleanup_ocr_errors(text: str) -> str:
    """Apply OCR corrections to clean up text."""
    cleaned = text

    # Apply corrections from OCR_CORRECTIONS dictionary
    for error, correction in OCR_CORRECTIONS.items():
        # Use word boundaries to avoid partial matches
        pattern = r"\b" + re.escape(error) + r"\b"
        cleaned = re.sub(pattern, correction, cleaned, flags=re.IGNORECASE)

    # All corrections are now loaded from TOML file via OCR_CORRECTIONS
    # No need for additional_corrections - they're all in the config file

    # Clean up excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Remove garbled uppercase text patterns (like "BRAWLING" at start)
    cleaned = re.sub(r"^([A-Z]{5,})\s+", "", cleaned)

    return cleaned.strip()


def cleanup_common_powers_json(data_dir: Path, dry_run: bool) -> None:
    """Clean up OCR errors in existing common_powers.json file."""
    common_powers_path = data_dir / FILENAME_COMMON_POWERS

    if not common_powers_path.exists():
        console.print(f"[red]Error: {common_powers_path} not found![/red]")
        return

    console.print("[cyan]Loading existing common_powers.json...[/cyan]")
    with open(common_powers_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[cyan]Cleaning up {len(powers_data)} powers...[/cyan]\n")

    updated_count = 0
    for power in powers_data:
        power_name = power["name"]
        console.print(f"[bold]{power_name}[/bold]")

        for level_data in power["levels"]:
            level = level_data["level"]
            original_desc = level_data["description"]

            # Clean up the description
            cleaned_desc = cleanup_ocr_errors(original_desc)

            if cleaned_desc != original_desc:
                console.print(f"  Level {level}: [yellow]Updated[/yellow]")
                console.print(
                    f"    Before: {original_desc[:100]}{'...' if len(original_desc) > 100 else ''}"
                )
                console.print(
                    f"    After:  {cleaned_desc[:100]}{'...' if len(cleaned_desc) > 100 else ''}"
                )
                level_data["description"] = cleaned_desc
                updated_count += 1
            else:
                console.print(f"  Level {level}: [green]No changes needed[/green]")

        console.print()

    if updated_count > 0:
        if dry_run:
            console.print(f"[yellow]DRY RUN - Would update {updated_count} descriptions[/yellow]")
        else:
            # Create backup
            backup_path = common_powers_path.with_suffix(common_powers_path.suffix + ".backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(powers_data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓ Backup created: {backup_path}[/green]")

            # Write updated data
            with open(common_powers_path, "w", encoding="utf-8") as f:
                json.dump(powers_data, f, indent=2, ensure_ascii=False)

            console.print(
                f"[green]✓ Updated {updated_count} descriptions in {common_powers_path}[/green]"
            )
    else:
        console.print("[green]✓ No OCR errors found - all descriptions are clean![/green]")


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--sample-size",
    type=int,
    default=10,
    help="Number of character cards to sample for OCR extraction (default: 10)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be extracted/cleaned without updating files",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Clean up OCR errors in existing common_powers.json file",
)
def main(data_dir: Path, sample_size: int, dry_run: bool, cleanup: bool):
    """Extract common power levels from character cards and update files.

    Use --cleanup to fix OCR errors in existing common_powers.json file.
    """
    if cleanup:
        cleanup_common_powers_json(data_dir, dry_run)
        return
    console.print("[bold cyan]Extracting Common Powers from Character Cards[/bold cyan]\n")

    # Find all character directories with back images
    character_dirs: List[Path] = []
    for char_dir in data_dir.rglob("*"):
        if char_dir.is_dir() and (char_dir / FILENAME_CHARACTER_JSON).exists():
            for pattern in BACK_IMAGE_PATTERNS:
                if (char_dir / pattern).exists():
                    character_dirs.append(char_dir)
                    break

    console.print(f"[cyan]Found {len(character_dirs)} characters with back card images[/cyan]")

    if not character_dirs:
        console.print("[red]No character directories with back images found![/red]")
        return

    # Sample characters (prioritize those we know have powers)
    # Start with Adam since we know he has Marksman and Toughness
    sample_dirs = []
    for char_dir in character_dirs:
        if "adam" in char_dir.name.lower():
            sample_dirs.append(char_dir)
            break

    # Add more until we have enough
    for char_dir in character_dirs:
        if char_dir not in sample_dirs and len(sample_dirs) < sample_size:
            sample_dirs.append(char_dir)

    console.print(f"[cyan]Sampling {len(sample_dirs)} characters for OCR extraction[/cyan]\n")

    # Extract power levels from each character card
    all_extractions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    character_powers_map: Dict[str, List[str]] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Extracting from character cards...", total=len(sample_dirs))

        for char_dir in sample_dirs:
            char_name = char_dir.name
            progress.update(task, description=f"Processing {char_name}...")

            # Find back image
            back_image = None
            for pattern in BACK_IMAGE_PATTERNS:
                img_path = char_dir / pattern
                if img_path.exists():
                    back_image = img_path
                    break

            if not back_image:
                progress.update(task, advance=1)
                continue

            # Extract text with improved OCR settings
            text = extract_text_from_image(
                back_image,
                enhance_contrast=True,
                denoise_strength=15,  # More aggressive denoising for character cards
            )
            if not text:
                progress.update(task, advance=1)
                continue

            # Clean the OCR text before parsing
            cleaned_text = clean_ocr_text(text, preserve_newlines=True)

            # Extract power levels for each power
            for power_name in COMMON_POWERS:
                levels = parse_power_levels_from_text(cleaned_text, power_name)
                if levels:
                    all_extractions[power_name].append(levels)

            # Extract which powers this character has
            powers = extract_character_powers_from_card(back_image)
            if powers:
                character_powers_map[char_name] = powers

            progress.update(task, advance=1)

    # Aggregate power levels
    console.print("\n[cyan]Aggregating power level descriptions...[/cyan]")
    aggregated_levels = aggregate_power_levels(all_extractions)

    # Create common_powers.json structure
    common_powers_data: List[Dict[str, Any]] = []
    for power_name in COMMON_POWERS:
        levels = aggregated_levels.get(power_name, [])
        common_powers_data.append(
            {
                "name": power_name,
                "is_special": False,
                "levels": levels,
            }
        )

        found_levels = [l for l in levels if "Not found" not in l["description"]]
        console.print(f"  {power_name}: {len(found_levels)}/4 levels found")

    # Save common_powers.json
    common_powers_path = data_dir / FILENAME_COMMON_POWERS

    if not dry_run:
        with open(common_powers_path, "w", encoding="utf-8") as f:
            json.dump(common_powers_data, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]✓ Updated {common_powers_path}[/green]")
    else:
        console.print(f"\n[yellow]Would update {common_powers_path}[/yellow]")
        # Show sample
        if common_powers_data:
            sample = common_powers_data[0]
            console.print(f"\n[cyan]Sample: {sample['name']}[/cyan]")
            for level in sample["levels"][:2]:
                desc = (
                    level["description"][:80] + "..."
                    if len(level["description"]) > 80
                    else level["description"]
                )
                console.print(f"  Level {level['level']}: {desc}")

    # Now extract character powers from PDF or all cards
    console.print("\n[cyan]Extracting character power assignments...[/cyan]")

    # Try to extract from PDF first
    pdf_path = data_dir / "traits_booklet.pdf"
    if pdf_path.exists():
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pdf_text = "\n".join([p.extract_text() or "" for p in pdf.pages])

                # Look for "Common Skills: Power1, Power2" patterns
                lines = pdf_text.split("\n")
                current_char = None
                for line in lines:
                    # Look for character name
                    char_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d+)\)", line)
                    if char_match:
                        current_char = char_match.group(1).split()[0]  # First name

                    # Look for common skills
                    if "common skill" in line.lower() or "common trait" in line.lower():
                        powers_found = []
                        for power in COMMON_POWERS:
                            if power in line or power.upper() in line.upper():
                                powers_found.append(power)

                        if powers_found and current_char:
                            char_name_lower = current_char.lower()
                            if char_name_lower not in character_powers_map:
                                character_powers_map[char_name_lower] = []
                            character_powers_map[char_name_lower].extend(powers_found)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse PDF: {e}[/yellow]")

    # Also extract from all character cards we haven't processed yet
    remaining_dirs = [d for d in character_dirs if d not in sample_dirs]
    if remaining_dirs:
        console.print(
            f"[cyan]Extracting powers from {len(remaining_dirs)} additional characters...[/cyan]"
        )
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Extracting powers...", total=len(remaining_dirs))

            for char_dir in remaining_dirs:
                char_name = char_dir.name
                progress.update(task, description=f"Processing {char_name}...")

                # Find back image
                back_image = None
                for pattern in BACK_IMAGE_PATTERNS:
                    img_path = char_dir / pattern
                    if img_path.exists():
                        back_image = img_path
                        break

                if back_image:
                    powers = extract_character_powers_from_card(back_image)
                    if powers:
                        character_powers_map[char_name] = powers

                progress.update(task, advance=1)

    console.print(
        f"[green]✓ Found power assignments for {len(character_powers_map)} characters[/green]"
    )

    # Update character.json files
    if not dry_run:
        console.print("\n[cyan]Updating character.json files...[/cyan]")
        updated = 0

        character_files = list(data_dir.rglob(FILENAME_CHARACTER_JSON))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Updating files...", total=len(character_files))

            for char_file in character_files:
                char_dir = char_file.parent
                char_name = char_dir.name

                # Try to find powers for this character
                powers = character_powers_map.get(char_name, [])

                # Also try variations of the name
                if not powers:
                    for key in character_powers_map.keys():
                        if char_name.lower() in key.lower() or key.lower() in char_name.lower():
                            powers = character_powers_map[key]
                            break

                if powers:
                    try:
                        with open(char_file, encoding="utf-8") as f:
                            char_data = json.load(f)

                        # Update common_powers to be list of power names
                        char_data["common_powers"] = powers

                        with open(char_file, "w", encoding="utf-8") as f:
                            json.dump(char_data, f, indent=2, ensure_ascii=False)

                        updated += 1
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not update {char_file}: {e}[/yellow]"
                        )

                progress.update(task, advance=1)

        console.print(f"\n[green]✓ Updated {updated} character files[/green]")
    else:
        console.print("\n[yellow]Would update character files[/yellow]")
        # Show sample
        for char_name, powers in list(character_powers_map.items())[:5]:
            console.print(f"  {char_name}: {', '.join(powers)}")
        if len(character_powers_map) > 5:
            console.print(f"  ... and {len(character_powers_map) - 5} more")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()
