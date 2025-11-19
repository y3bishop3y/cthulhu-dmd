#!/usr/bin/env python3
"""
Parse traits booklet PDF to extract common power level descriptions.
Update common_powers.json with actual game text.
"""

import json
import re
import sys
from pathlib import Path
from typing import Final, Dict, List, Any, Optional

try:
    import click
    import pdfplumber
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_common_powers_from_booklet.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_common_powers_from_booklet.py [options]\n\n"
        "Recommended: uv run ./scripts/parse_common_powers_from_booklet.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_TRAITS_BOOKLET: Final[str] = "traits_booklet.pdf"
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
DATA_DIR: Final[str] = "data"

# Common power names
COMMON_POWERS: Final[List[str]] = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF."""
    text_parts: List[str] = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    
    return "\n".join(text_parts)


def find_power_section(text: str, power_name: str) -> Optional[str]:
    """Find the section of text for a specific power."""
    # Look for power name as heading (all caps, standalone, or with "Level" nearby)
    patterns = [
        rf"^{re.escape(power_name.upper())}\s*$",
        rf"^{re.escape(power_name)}\s*$",
        rf"^{re.escape(power_name.upper())}\s+Level",
        rf"^{re.escape(power_name)}\s+Level",
    ]
    
    lines = text.split("\n")
    start_idx = None
    
    for i, line in enumerate(lines):
        line_upper = line.upper().strip()
        power_upper = power_name.upper()
        
        # Check if this line contains the power name as a heading
        if power_upper in line_upper and (
            line_upper.startswith(power_upper) or 
            line_upper == power_upper or
            f"{power_upper} LEVEL" in line_upper or
            f"LEVEL {power_upper}" in line_upper
        ):
            start_idx = i
            break
    
    if start_idx is None:
        return None
    
    # Extract section until next power or end
    section_lines: List[str] = []
    for i in range(start_idx, min(start_idx + 50, len(lines))):
        line = lines[i].strip()
        if not line:
            continue
        
        # Stop if we hit another power name (but not if it's part of a description)
        if i > start_idx + 2:  # Skip first few lines
            for other_power in COMMON_POWERS:
                if other_power != power_name and other_power.upper() in line.upper():
                    # Check if it's a heading (all caps or starts the line)
                    if line.upper().startswith(other_power.upper()) or line.upper() == other_power.upper():
                        return "\n".join(section_lines)
        
        section_lines.append(line)
    
    return "\n".join(section_lines)


def parse_power_levels(section_text: str, power_name: str) -> List[Dict[str, Any]]:
    """Parse level descriptions from power section text."""
    levels: List[Dict[str, Any]] = []
    
    # Look for level indicators: "Level 1", "Level1", "1:", "1.", etc.
    level_patterns = [
        r"Level\s*(\d+)[:\-\.]?\s*(.*)",
        r"^(\d+)[:\-\.]\s*(.*)",
        r"^(\d+)\s+(.*)",
    ]
    
    lines = section_text.split("\n")
    current_level = None
    current_description: List[str] = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_level and current_description:
                levels.append({
                    "level": current_level,
                    "description": " ".join(current_description).strip(),
                })
                current_description = []
            continue
        
        # Check for level indicator
        level_found = False
        for pattern in level_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                level_num = int(match.group(1))
                description_start = match.group(2) if len(match.groups()) > 1 else ""
                
                # Save previous level
                if current_level and current_description:
                    levels.append({
                        "level": current_level,
                        "description": " ".join(current_description).strip(),
                    })
                
                # Start new level
                current_level = level_num
                current_description = [description_start] if description_start else []
                level_found = True
                break
        
        if not level_found and current_level:
            # Continuation of current level description
            current_description.append(line)
    
    # Save last level
    if current_level and current_description:
        levels.append({
            "level": current_level,
            "description": " ".join(current_description).strip(),
        })
    
    # Ensure we have 4 levels (1-4)
    result_levels: List[Dict[str, Any]] = []
    for level_num in range(1, 5):
        # Find matching level
        level_data = next((l for l in levels if l["level"] == level_num), None)
        if level_data:
            result_levels.append(level_data)
        else:
            # Create placeholder
            result_levels.append({
                "level": level_num,
                "description": f"Level {level_num} description - Not found in PDF",
            })
    
    return result_levels


def extract_character_powers_from_pdf(text: str) -> Dict[str, List[str]]:
    """Extract which characters have which common powers from the PDF."""
    character_powers: Dict[str, List[str]] = {}
    
    # Look for patterns like "Character Name (Number) - Power1, Power2"
    # Or "Common Skills: Power1, Power2"
    lines = text.split("\n")
    
    current_character = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for character name patterns
        # Format: "Name (Number)" or "Name - Quote"
        char_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d+)\)", line)
        if char_match:
            current_character = char_match.group(1)
            continue
        
        # Look for "Common Skills:" or "Common Trait:" pattern
        if "common skill" in line.lower() or "common trait" in line.lower():
            # Extract power names from this line
            powers_found: List[str] = []
            for power in COMMON_POWERS:
                if power in line or power.upper() in line.upper():
                    powers_found.append(power)
            
            if powers_found and current_character:
                # Normalize character name (remove extra spaces, handle variations)
                char_name_normalized = current_character.split()[0] if current_character else None
                if char_name_normalized:
                    if char_name_normalized not in character_powers:
                        character_powers[char_name_normalized] = []
                    character_powers[char_name_normalized].extend(powers_found)
    
    return character_powers


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
    help="Show what would be extracted without updating files",
)
def main(data_dir: Path, dry_run: bool):
    """Parse traits booklet PDF and update common_powers.json with real data."""
    console.print("[bold cyan]Parsing Traits Booklet PDF[/bold cyan]\n")
    
    pdf_path = data_dir / FILENAME_TRAITS_BOOKLET
    if not pdf_path.exists():
        console.print(f"[red]Error: PDF not found: {pdf_path}[/red]")
        sys.exit(1)
    
    console.print(f"[cyan]Extracting text from {pdf_path.name}...[/cyan]")
    text = extract_text_from_pdf(pdf_path)
    
    console.print(f"[green]✓ Extracted {len(text)} characters of text[/green]\n")
    
    # Parse each power
    common_powers_data: List[Dict[str, Any]] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Parsing powers...", total=len(COMMON_POWERS))
        
        for power_name in COMMON_POWERS:
            progress.update(task, description=f"Parsing {power_name}...")
            
            section = find_power_section(text, power_name)
            if section:
                levels = parse_power_levels(section, power_name)
                common_powers_data.append({
                    "name": power_name,
                    "is_special": False,
                    "levels": levels,
                })
                console.print(f"[green]✓ Found {power_name}: {len([l for l in levels if 'Not found' not in l['description']])} levels[/green]")
            else:
                console.print(f"[yellow]⚠ {power_name}: Section not found, using placeholders[/yellow]")
                common_powers_data.append({
                    "name": power_name,
                    "is_special": False,
                    "levels": [
                        {"level": i, "description": f"Level {i} description - Not found in PDF"}
                        for i in range(1, 5)
                    ],
                })
            
            progress.update(task, advance=1)
    
    # Save common_powers.json
    common_powers_path = data_dir / FILENAME_COMMON_POWERS
    
    if not dry_run:
        with open(common_powers_path, "w", encoding="utf-8") as f:
            json.dump(common_powers_data, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]✓ Updated {common_powers_path}[/green]")
    else:
        console.print(f"\n[yellow]Would update {common_powers_path}[/yellow]")
        # Show sample of what would be saved
        console.print("\n[cyan]Sample power data:[/cyan]")
        if common_powers_data:
            sample = common_powers_data[0]
            console.print(f"  {sample['name']}:")
            for level in sample["levels"][:2]:
                desc = level["description"][:60] + "..." if len(level["description"]) > 60 else level["description"]
                console.print(f"    Level {level['level']}: {desc}")
    
    # Extract character powers
    console.print("\n[cyan]Extracting character power assignments...[/cyan]")
    character_powers = extract_character_powers_from_pdf(text)
    
    if character_powers:
        console.print(f"[green]✓ Found power assignments for {len(character_powers)} characters[/green]")
        if not dry_run:
            # Show sample
            for char_name, powers in list(character_powers.items())[:5]:
                console.print(f"  {char_name}: {', '.join(powers)}")
            if len(character_powers) > 5:
                console.print(f"  ... and {len(character_powers) - 5} more")
    
    return character_powers if not dry_run else None


if __name__ == "__main__":
    main()

