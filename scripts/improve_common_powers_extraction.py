#!/usr/bin/env python3
"""
Improved extraction of common power level descriptions from character cards.
Aggregates from multiple cards and cleans up OCR errors.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Final, Dict, List, Any, Optional

try:
    import click
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/improve_common_powers_extraction.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/improve_common_powers_extraction.py [options]\n\n"
        "Recommended: uv run ./scripts/improve_common_powers_extraction.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
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

# Common OCR error corrections
OCR_CORRECTIONS: Final[Dict[str, str]] = {
    "goin": "gain",
    "isone": "is on",
    "santiy": "sanity",
    "ateck": "attack",
    "oneck": "attack",
    "arteck": "attack",
    "fre": "free",
    "resotve": "resolve",
    "bmi": "mythos",
    "fig": "figures",
    "Swarts": "Swiftness",
    "ccceerntnstnisinioincn": "",  # Garbage text
    "nme nena gn emmamnninnnac": "",  # Garbage text
    "GAS": "",
    "FDISCOVERY": "DISCOVERY",
    "cord": "card",
    "fay": "way",
    "kad": "card",
    "ond": "and",
    "Q®": "1",
    "PSOne": "1",
    "ewes": "successes",
    "val": "as",
    "G81": "Gain 1",
    "Pr": "space",
    "a Pr": "a space",
    "}": "",
    "@": "1",
    "|": "",
    "°": "",
    "—": "-",
    "—-—>": "",
    "~~": "",
    "Lc >": "",
}

# Dice symbol patterns - OCR might see these as various characters
# Green dice symbols might appear as: ●, ○, ◉, G, g, green, etc.
# Black dice symbols might appear as: ●, ○, B, b, black, etc.
DICE_SYMBOL_PATTERNS: Final[List[str]] = [
    r'\d+\s*(?:green|g|●|○|◉)\s*(?:dice|die|d)',
    r'\d+\s*(?:black|b|●|○)\s*(?:dice|die|d)',
    r'(?:gain|gain|get|use|add)\s+\d+\s*(?:green|g|●|○|◉)\s*(?:dice|die|d)',
    r'(?:gain|gain|get|use|add)\s+\d+\s*(?:black|b|●|○)\s*(?:dice|die|d)',
]

# Red swirl/sanity threshold patterns
# The red swirl indicates when sanity reaches a certain threshold
RED_SWIRL_PATTERNS: Final[List[str]] = [
    r'(?:when|while|if)\s+(?:your\s+)?sanity\s+(?:is\s+)?(?:on|at|reaches?)\s*(?:a\s+)?(?:red|marker|threshold|swirl)',
    r'(?:when|while|if)\s+(?:your\s+)?sanity\s+(?:is\s+)?(?:on|at)\s*(?:a\s+)?(?:red\s+)?(?:sanity\s+)?marker',
    r'sanity\s+(?:on|at|reaches?)\s*(?:red|marker|threshold)',
    r'[🌀🌀🌀]',  # Swirl symbols (if OCR captures them)
]


def preprocess_image_for_ocr(image_path: Path) -> np.ndarray:
    """Preprocess image for better OCR."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image using OCR."""
    try:
        processed_img = preprocess_image_for_ocr(image_path)
        custom_config = r"--oem 3 --psm 3"
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        return text
    except Exception as e:
        console.print(f"[yellow]Warning: Could not extract text from {image_path}: {e}[/yellow]")
        return ""


def normalize_dice_symbols(text: str) -> str:
    """Normalize dice symbol references in text.
    
    Dice symbols in OCR might appear as:
    - @ (common symbol for green dice)
    - B or b (for black dice)
    - Numbers followed by g/G or b/B
    - Actual words "green dice" or "black dice"
    """
    normalized = text
    
    # Pattern 1: "gain @" or "gain @ while" -> "gain 1 green dice"
    # The @ symbol often represents a green dice
    normalized = re.sub(
        r'gain\s+@\s+(?:while|when|if)',
        r'gain 1 green dice while',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 2: "gain @" standalone -> "gain 1 green dice"
    normalized = re.sub(
        r'gain\s+@\b',
        r'gain 1 green dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 3: "Gain B" or "gain B when" -> "gain 1 black dice"
    normalized = re.sub(
        r'gain\s+B\s+(?:when|while|if|attacking)',
        r'gain 1 black dice when',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 4: "Gain B" standalone -> "gain 1 black dice"
    normalized = re.sub(
        r'gain\s+B\b',
        r'gain 1 black dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 5: Numbers with dice indicators
    # "2 green dice" or "2 g dice" or "2 ● dice" -> "2 green dice"
    normalized = re.sub(
        r'(\d+)\s*(?:g|●|○|◉|green|@)\s*(?:dice|die|d)\b',
        r'\1 green dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 6: "1 black dice" or "1 b dice" -> "1 black dice"
    normalized = re.sub(
        r'(\d+)\s*(?:b|●|○|black)\s*(?:dice|die|d)\b',
        r'\1 black dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 7: "gain X green dice" patterns
    normalized = re.sub(
        r'(?:gain|get|use|add)\s+(\d+)\s*(?:green|g|●|○|◉|@)\s*(?:dice|die|d)\b',
        r'gain \1 green dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern 8: "gain X black dice" patterns
    normalized = re.sub(
        r'(?:gain|get|use|add)\s+(\d+)\s*(?:black|b|●|○)\s*(?:dice|die|d)\b',
        r'gain \1 black dice',
        normalized,
        flags=re.IGNORECASE,
    )
    
    return normalized


def normalize_red_swirl_symbols(text: str) -> str:
    """Normalize red swirl/sanity threshold references."""
    normalized = text
    
    # Handle OCR errors first: "ison" -> "is on"
    normalized = re.sub(r'\bison\b', 'is on', normalized, flags=re.IGNORECASE)
    
    # Handle red swirl symbols: "@®" or "oR" when in context of sanity
    # Pattern: "sanity sono @®" or "sanity ison oR" -> "sanity is on red"
    normalized = re.sub(
        r'sanity\s+(?:sono|ison|is\s+on)\s*(?:@®|oR|red)',
        r'sanity is on red',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Handle "@®" as red swirl symbol when near sanity context
    normalized = re.sub(
        r'sanity\s+(?:is\s+on|ison|sono)\s*@®',
        r'sanity is on red sanity marker',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Handle "oR" -> "red" but only in sanity context (not "or" as conjunction)
    # Only replace "oR" when it's clearly part of "red" (after sanity/on/at)
    normalized = re.sub(
        r'(?:sanity|on|at)\s+oR\b(?!\s+(?:rolling|attacking|fighting))',
        r'red',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Normalize various patterns for red sanity marker/threshold
    # Pattern: "when sanity is on red marker" -> "when sanity is on red sanity marker"
    normalized = re.sub(
        r'(?:when|while|if)\s+(?:your\s+)?sanity\s+(?:is\s+)?(?:on|at|reaches?)\s*(?:a\s+)?(?:red|marker|threshold|swirl)',
        r'when sanity is on red sanity marker',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern: "sanity on red" -> "sanity on red sanity marker"
    normalized = re.sub(
        r'sanity\s+(?:is\s+)?(?:on|at|reaches?)\s*(?:a\s+)?(?:red\s+)?(?:sanity\s+)?marker',
        r'sanity is on red sanity marker',
        normalized,
        flags=re.IGNORECASE,
    )
    
    # Pattern: "while sanity is on red" -> "while sanity is on red sanity marker"
    # But avoid double "sanity marker"
    if 'sanity marker' not in normalized.lower():
        normalized = re.sub(
            r'(?:while|when)\s+(?:your\s+)?sanity\s+(?:is\s+)?(?:on|at)\s*(?:a\s+)?red(?!\s+sanity\s+marker)',
            r'while sanity is on red sanity marker',
            normalized,
            flags=re.IGNORECASE,
        )
    
    # Clean up any duplicate "sanity marker" phrases
    normalized = re.sub(r'sanity marker\s+sanity marker', 'sanity marker', normalized, flags=re.IGNORECASE)
    
    return normalized


def clean_ocr_text(text: str, preserve_symbols: bool = True) -> str:
    """Clean up common OCR errors while preserving important symbols."""
    cleaned = text
    
    # First apply basic OCR corrections (like "goin" -> "gain", "ison" -> "is on")
    cleaned = cleaned.replace("goin", "gain").replace("Goin", "Gain")
    cleaned = cleaned.replace("isone", "is on").replace("Isone", "Is on")
    
    # Then normalize dice and red swirl symbols
    if preserve_symbols:
        cleaned = normalize_dice_symbols(cleaned)
        cleaned = normalize_red_swirl_symbols(cleaned)
    
    # Apply other corrections
    for error, correction in OCR_CORRECTIONS.items():
        cleaned = cleaned.replace(error, correction)
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove common OCR artifacts, but preserve dice/red swirl references
    # Keep: letters, numbers, spaces, punctuation, and words related to dice/sanity
    if preserve_symbols:
        # More lenient - keep more characters that might be part of dice/sanity references
        cleaned = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]\/●○◉🌀]', '', cleaned)
    else:
        cleaned = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]\/]', '', cleaned)
    
    return cleaned.strip()


def extract_power_section(text: str, power_name: str) -> Optional[str]:
    """Extract the section of text for a specific power."""
    lines = text.split("\n")
    power_start_idx = None
    
    # Find power name
    for i, line in enumerate(lines):
        line_upper = line.upper().strip()
        power_upper = power_name.upper()
        
        if (
            power_upper in line_upper
            and len(line.strip()) < 50
            and (
                line_upper.startswith(power_upper)
                or line_upper == power_upper
                or f"{power_upper} LEVEL" in line_upper
            )
        ):
            power_start_idx = i
            break
    
    if power_start_idx is None:
        return None
    
    # Extract section until next power
    section_lines: List[str] = []
    for i in range(power_start_idx, min(power_start_idx + 25, len(lines))):
        line = lines[i].strip()
        if not line:
            continue
        
        # Stop if we hit another power
        for other_power in COMMON_POWERS:
            if other_power != power_name:
                other_upper = other_power.upper()
                line_upper = line.upper()
                if (
                    other_upper in line_upper
                    and len(line.strip()) < 50
                    and (line_upper.startswith(other_upper) or line_upper == other_upper)
                ):
                    return "\n".join(section_lines)
        
        section_lines.append(line)
    
    return "\n".join(section_lines)


def parse_levels_from_section(section_text: str, power_name: str) -> List[Dict[str, Any]]:
    """Parse level descriptions from a power section.
    
    Levels are typically separated by:
    1. Explicit "Level X:" markers
    2. "Instead," which often indicates a new level
    3. Numbered bullets (1., 2., etc.)
    4. New paragraphs/sections
    """
    levels: List[Dict[str, Any]] = []
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    
    # First, try to find explicit level markers
    explicit_levels: Dict[int, List[str]] = {}
    current_level = None
    current_desc_lines: List[str] = []
    
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        # Look for explicit level indicators
        level_match = re.search(r"^(?:level\s*)?([1234])[:\-\.]?\s*(.*)", line, re.IGNORECASE)
        if level_match:
            # Save previous level
            if current_level and current_desc_lines:
                desc_text = " ".join(current_desc_lines).strip()
                desc_text = clean_ocr_text(desc_text)
                if desc_text and len(desc_text) > 10:
                    explicit_levels[current_level] = [desc_text]
            
            # Start new level
            current_level = int(level_match.group(1))
            desc_start = level_match.group(2).strip()
            current_desc_lines = [desc_start] if desc_start else []
        elif current_level:
            # Continuation of current level
            # Stop if we hit a new power or game rule
            if any(
                keyword in line_upper
                for keyword in [
                    "YOUR TURN",
                    "TAKE",
                    "DRAW",
                    "INVESTIGATE",
                    "FIGHT",
                    "RESOLVE",
                    "END OF TURN",
                ]
            ):
                # Save and stop
                if current_desc_lines:
                    desc_text = " ".join(current_desc_lines).strip()
                    desc_text = clean_ocr_text(desc_text)
                    if desc_text and len(desc_text) > 10:
                        explicit_levels[current_level] = [desc_text]
                current_level = None
                current_desc_lines = []
            else:
                # Check if it's a power name
                is_power_name = False
                for other_power in COMMON_POWERS:
                    if other_power != power_name:
                        other_upper = other_power.upper()
                        if other_upper in line_upper and len(line.strip()) < 50:
                            is_power_name = True
                            break
                
                if not is_power_name:
                    current_desc_lines.append(line)
    
    # Save last level
    if current_level and current_desc_lines:
        desc_text = " ".join(current_desc_lines).strip()
        desc_text = clean_ocr_text(desc_text)
        if desc_text and len(desc_text) > 10:
            explicit_levels[current_level] = [desc_text]
    
    # If we found explicit levels, use them
    if explicit_levels:
        for level_num in range(1, 5):
            if level_num in explicit_levels:
                levels.append({
                    "level": level_num,
                    "description": explicit_levels[level_num][0],
                })
        return levels
    
    # Otherwise, try to infer levels from "Instead," patterns and structure
    # Split by "Instead," which often indicates a new level
    full_text = " ".join(lines)
    
    # Look for patterns that indicate level breaks
    # Pattern 1: "Instead," or "Instead, you may" often starts a new level
    instead_splits = re.split(r"(?i)\s+instead[,\s]+", full_text)
    
    if len(instead_splits) >= 2:
        # First part is likely Level 1
        level1_text = instead_splits[0].strip()
        level1_text = clean_ocr_text(level1_text)
        if level1_text and len(level1_text) > 15:
            levels.append({"level": 1, "description": level1_text})
        
        # Remaining parts might be levels 2-4
        for i, part in enumerate(instead_splits[1:], start=2):
            if i > 4:
                break
            part_text = f"Instead, {part}".strip()
            part_text = clean_ocr_text(part_text)
            if part_text and len(part_text) > 15:
                levels.append({"level": i, "description": part_text})
    
    # If we still don't have levels, try to split by sentences/paragraphs
    if not levels:
        # Look for sentence endings followed by capital letters (new sentences)
        sentences = re.split(r"\.\s+([A-Z])", full_text)
        if len(sentences) >= 2:
            # Group sentences into potential levels
            level_texts = []
            current_sent = sentences[0]
            for i in range(1, len(sentences), 2):
                if i + 1 < len(sentences):
                    current_sent += ". " + sentences[i] + sentences[i + 1]
                else:
                    current_sent += ". " + sentences[i]
                
                # Check if this looks like a complete level description
                if len(current_sent.split()) >= 5:  # At least 5 words
                    level_texts.append(current_sent)
                    current_sent = ""
            
            if current_sent and len(current_sent.split()) >= 5:
                level_texts.append(current_sent)
            
            # Assign to levels 1-4
            for i, text in enumerate(level_texts[:4], start=1):
                cleaned = clean_ocr_text(text)
                if cleaned and len(cleaned) > 15:
                    levels.append({"level": i, "description": cleaned})
    
    return levels


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--min-samples",
    type=int,
    default=3,
    help="Minimum number of samples needed for a level description (default: 3)",
)
def main(data_dir: Path, min_samples: int):
    """Extract and improve common power level descriptions from character cards."""
    console.print("[bold cyan]Improving Common Power Level Descriptions[/bold cyan]\n")
    
    # Find all character directories with back images
    character_dirs: List[Path] = []
    for char_dir in data_dir.rglob("*"):
        if char_dir.is_dir() and (char_dir / "character.json").exists():
            for pattern in BACK_IMAGE_PATTERNS:
                if (char_dir / pattern).exists():
                    character_dirs.append(char_dir)
                    break
    
    console.print(f"[cyan]Found {len(character_dirs)} characters with back card images[/cyan]\n")
    
    # Extract power levels from all characters
    all_extractions: Dict[str, Dict[int, List[str]]] = defaultdict(lambda: defaultdict(list))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Extracting from character cards...", total=len(character_dirs))
        
        for char_dir in character_dirs:
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
            
            # Extract text
            text = extract_text_from_image(back_image)
            if not text:
                progress.update(task, advance=1)
                continue
            
            # Extract levels for each power
            for power_name in COMMON_POWERS:
                section = extract_power_section(text, power_name)
                if section:
                    levels = parse_levels_from_section(section, power_name)
                    for level_data in levels:
                        level_num = level_data["level"]
                        description = level_data["description"]
                        if description and len(description) > 15:  # Filter very short descriptions
                            all_extractions[power_name][level_num].append(description)
            
            progress.update(task, advance=1)
    
    # Aggregate and pick best descriptions
    console.print("\n[cyan]Aggregating level descriptions...[/cyan]")
    
    common_powers_data: List[Dict[str, Any]] = []
    
    for power_name in COMMON_POWERS:
        power_levels: List[Dict[str, Any]] = []
        
        for level_num in range(1, 5):
            descriptions = all_extractions[power_name][level_num]
            
            if descriptions:
                # Pick the most common or longest description
                # Count occurrences
                desc_counts: Dict[str, int] = defaultdict(int)
                for desc in descriptions:
                    desc_counts[desc] += 1
                
                # Sort by count, then by length
                sorted_descs = sorted(
                    desc_counts.items(),
                    key=lambda x: (x[1], len(x[0])),
                    reverse=True,
                )
                
                # Use the best one if we have enough samples
                if len(descriptions) >= min_samples:
                    best_desc = sorted_descs[0][0]
                    power_levels.append({"level": level_num, "description": best_desc})
                    console.print(
                        f"  {power_name} Level {level_num}: {len(descriptions)} samples, "
                        f"{len(best_desc)} chars"
                    )
                else:
                    # Not enough samples, use placeholder
                    power_levels.append({
                        "level": level_num,
                        "description": f"Level {level_num} description - Only {len(descriptions)} sample(s) found, need {min_samples}",
                    })
            else:
                # No samples found
                power_levels.append({
                    "level": level_num,
                    "description": f"Level {level_num} description - Not found in character cards",
                })
        
        common_powers_data.append({
            "name": power_name,
            "is_special": False,
            "levels": power_levels,
        })
    
    # Save updated common_powers.json
    common_powers_path = data_dir / FILENAME_COMMON_POWERS
    
    with open(common_powers_path, "w", encoding="utf-8") as f:
        json.dump(common_powers_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]✓ Updated {common_powers_path}[/green]")
    
    # Show summary
    console.print("\n[cyan]Summary:[/cyan]")
    for power_data in common_powers_data:
        found_levels = [
            l
            for l in power_data["levels"]
            if "Not found" not in l["description"] and "Only" not in l["description"]
        ]
        console.print(f"  {power_data['name']}: {len(found_levels)}/4 levels")
    
    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()

