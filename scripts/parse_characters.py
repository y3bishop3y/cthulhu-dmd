#!/usr/bin/env python3
"""
Parse character card images to extract character data.
Extracts name, location, motto, story from front.jpg
and powers/abilities from back.jpg.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

try:
    import click
    import cv2
    import numpy as np
    import pytesseract
    import yaml
    from pydantic import BaseModel, Field
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/parse_characters.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/parse_characters.py [options]\n\n"
        "Note: You may also need to install Tesseract OCR:\n"
        "  macOS: brew install tesseract\n"
        "  Linux: sudo apt-get install tesseract-ocr\n"
        "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
FILENAME_FRONT: Final[str] = "front.jpg"
FILENAME_BACK: Final[str] = "back.jpg"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"
FILENAME_STORY_TXT: Final[str] = "story.txt"
OUTPUT_FORMAT_JSON: Final[str] = "json"
OUTPUT_FORMAT_YAML: Final[str] = "yaml"

# Common power names (from the game)
COMMON_POWERS: Final[List[str]] = [
    "Arcane Mastery",
    "Brawling",
    "Marksman",
    "Stealth",
    "Swiftness",
    "Toughness",
]


# Pydantic Models
class PowerLevel(BaseModel):
    """Represents a single level of a power."""

    level: int
    description: str


class Power(BaseModel):
    """Represents a character power (special or common)."""

    name: str
    is_special: bool = False
    levels: List[PowerLevel] = Field(default_factory=list)


class CharacterData(BaseModel):
    """Complete character data extracted from cards."""

    name: str
    location: Optional[str] = None
    motto: Optional[str] = None
    story: Optional[str] = None
    special_power: Optional[Power] = None
    common_powers: List[Power] = Field(default_factory=list)


def preprocess_image_for_ocr(image_path: Path) -> np.ndarray:
    """Preprocess image to improve OCR accuracy."""
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to get binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Apply denoising
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

    return denoised


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image using OCR."""
    try:
        # Preprocess image
        processed_img = preprocess_image_for_ocr(image_path)

        # Use pytesseract to extract text
        # Use --psm 3 for fully automatic page segmentation (works better for cards)
        custom_config = r"--oem 3 --psm 3"
        text: str = pytesseract.image_to_string(processed_img, config=custom_config)

        return text.strip()
    except Exception as e:
        console.print(f"[red]Error extracting text from {image_path}:[/red] {e}")
        return ""


def clean_ocr_text(text: str, preserve_newlines: bool = False) -> str:
    """Clean up OCR artifacts from text."""
    if preserve_newlines:
        # Preserve newlines, only clean within lines
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove excessive whitespace within line
            line = re.sub(r"[ \t]+", " ", line)
            # Remove common OCR artifacts
            line = re.sub(r"\s*[|]\s*", " ", line)  # Vertical bars
            line = re.sub(r"\s*[~]\s*", " ", line)  # Tildes
            cleaned_lines.append(line.strip())
        return "\n".join(cleaned_lines)
    else:
        # Remove all whitespace including newlines
        text = re.sub(r"\s+", " ", text)
        # Remove common OCR artifacts
        text = re.sub(r"\s*[|]\s*", " ", text)  # Vertical bars
        text = re.sub(r"\s*[~]\s*", " ", text)  # Tildes
        return text.strip()


def parse_front_card(text: str) -> Dict[str, Optional[str]]:
    """Parse front card text to extract name, location, motto, and story."""
    data: Dict[str, Optional[str]] = {
        "name": None,
        "location": None,
        "motto": None,
        "story": None,
    }

    # Clean the text first, preserving newlines for line-by-line parsing
    text = clean_ocr_text(text, preserve_newlines=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Look for name (usually in all caps, first few lines, looks like a name)
    for line in lines[:10]:
        # Check if it's all caps and looks like a name (has letters, reasonable length)
        if (
            line.isupper()
            and len(line) > 5
            and len(line) < 60
            and re.match(r"^[A-Z\s]+$", line)
            and not re.match(r"^[A-Z\s]{1,3}$", line)  # Not just initials
        ):
            # Convert to Title Case
            data["name"] = line.title()
            break

    # Look for location (usually after name, in format "CITY, COUNTRY" or "CITY, STATE")
    for line in lines:
        # Look for location pattern: CITY, COUNTRY/STATE
        if "," in line and line.isupper() and len(line) < 60 and re.match(r"^[A-Z\s,]+$", line):
            if data["location"] is None:
                data["location"] = line.title()
                break

    # Look for motto (usually in quotes, may span multiple lines)
    # First try to find quoted text
    quote_pattern = r'"([^"]+)"'
    quotes = re.findall(quote_pattern, text)
    if quotes:
        # Take the first complete quote
        data["motto"] = quotes[0].strip()
    else:
        # Look for multi-line quotes or motto-like text
        # Motto is usually short, not all caps, and may contain keywords
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if (
                len(line) < 150
                and not line.isupper()
                and not line.isdigit()
                and data["motto"] is None
            ):
                # Check if it looks like a motto (short, may have keywords)
                if any(
                    word in line_lower
                    for word in ["first", "never", "always", "shoot", "ask", "trust"]
                ):
                    # Check if next line completes it
                    if i + 1 < len(lines) and len(lines[i + 1]) < 100:
                        combined = f"{line} {lines[i + 1]}"
                        if len(combined) < 150:
                            data["motto"] = combined.strip()
                            break
                    else:
                        data["motto"] = line.strip()
                        break

    # Story is usually the longest paragraph after the motto
    # Find paragraphs (separated by blank lines or significant whitespace)
    paragraphs = re.split(r"\n\s*\n+", text)
    # Filter out very short paragraphs and the name/location/motto
    story_paragraphs = [
        p.strip()
        for p in paragraphs
        if len(p.strip()) > 100
        and not p.strip().isupper()
        and (not data["name"] or data["name"] not in p)
        and (not data["location"] or data["location"] not in p)
        and (not data["motto"] or data["motto"] not in p)
    ]

    if story_paragraphs:
        # Take the longest paragraph as the story
        longest_para = max(story_paragraphs, key=len)
        # Clean up the story text
        story = clean_ocr_text(longest_para)
        # Remove any remaining OCR artifacts
        story = re.sub(r"\s+", " ", story).strip()
        data["story"] = story

    return data


def parse_back_card(text: str) -> Dict[str, Any]:
    """Parse back card text to extract powers and their levels."""
    data: Dict[str, Any] = {
        "special_power": None,
        "common_powers": [],
    }

    # Clean the text first, preserving newlines for line-by-line parsing
    text = clean_ocr_text(text, preserve_newlines=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Look for special power (usually mentioned first, has unique name)
    # For Adam: "Fueled by Madness"
    current_power: Optional[Dict[str, Any]] = None
    current_power_type: Optional[str] = None  # "special" or "common"
    power_content_lines: List[str] = []
    found_common_power = False

    i = 0
    while i < len(lines):
        line = lines[i]
        line_lower = line.lower()
        line_upper = line.upper()

        # Skip game rules sections (YOUR TURN, TAKE ACTIONS, etc.)
        if any(
            keyword in line_upper
            for keyword in [
                "YOUR TURN",
                "TAKE",
                "DRAW MYTHOS",
                "INVESTIGATE",
                "FIGHT",
                "RESOLVE",
                "OR FIGHT!",
                "INVESTIGATE OR FIGHT!",
            ]
        ):
            i += 1
            continue

        # Check for special power BEFORE we find any common powers
        is_special_power = False
        special_power_name = None

        # Check for "Fueled by Madness" pattern
        if "fueled" in line_lower and "madness" in line_lower:
            # Extract the power name
            words = line.split()
            power_words = []
            for word in words:
                if word[0].isupper() or word.lower() in ["by", "the"]:
                    power_words.append(word)
                elif power_words:
                    break
            if power_words:
                special_power_name = " ".join(power_words)
                is_special_power = True

        # Check for special power description pattern (Gain X while your sanity...)
        # Handle OCR errors: "Goin" instead of "Gain", "isone" instead of "is on"
        # Also handle multi-line patterns where "gain" and "sanity" are on different lines
        gain_patterns = ["gain", "goin", "go in"]
        sanity_patterns = ["sanity", "santiy"]

        # Check current line and surrounding lines for the pattern
        has_gain = any(g in line_lower for g in gain_patterns)
        has_sanity = any(s in line_lower for s in sanity_patterns)

        # Check next few lines for sanity if current line has gain
        if has_gain and not has_sanity and i + 1 < len(lines):
            for j in range(i + 1, min(i + 4, len(lines))):
                if any(s in lines[j].lower() for s in sanity_patterns):
                    has_sanity = True
                    break

        # Check previous lines for gain if current line has sanity
        if has_sanity and not has_gain and i > 0:
            for j in range(max(0, i - 3), i):
                if any(g in lines[j].lower() for g in gain_patterns):
                    has_gain = True
                    break

        # Only detect special power if we haven't found any common powers yet
        # and the pattern appears before any common power names
        if not is_special_power and not found_common_power and (has_gain and has_sanity):
            # This is likely the special power description
            # The special power name typically doesn't appear on the card
            # For Adam, it's "Fueled by Madness" - we'll use this as default
            # when we detect the gain/sanity pattern before any common powers
            special_power_name = "Fueled by Madness"
            is_special_power = True

        # Check if it's a common power name (all caps, matches known powers)
        is_common_power = False
        common_power_name = None

        for common_power in COMMON_POWERS:
            if common_power.upper() in line_upper or line_upper == common_power.upper():
                common_power_name = common_power
                is_common_power = True
                found_common_power = True
                break

        # If we found a power name, save previous power and start new one
        if is_special_power and special_power_name:
            # Save previous power
            if current_power and current_power_type:
                if current_power_type == "special":
                    data["special_power"] = current_power
                else:
                    data["common_powers"].append(current_power)

            # Start tracking special power
            current_power = {
                "name": special_power_name,
                "is_special": True,
                "levels": [],
            }
            current_power_type = "special"
            power_content_lines = [line]  # Include current line
            i += 1
            continue

        elif is_common_power and common_power_name:
            # Save previous power
            if current_power and current_power_type:
                if current_power_type == "special":
                    data["special_power"] = current_power
                else:
                    data["common_powers"].append(current_power)

            # Start tracking common power
            current_power = {
                "name": common_power_name,
                "is_special": False,
                "levels": [],
            }
            current_power_type = "common"
            power_content_lines = []
            i += 1
            continue

        # If we're tracking a power, collect content lines
        if current_power:
            # Check for level indicators (Level 1, Level 2, etc. or just numbers at start)
            level_match = re.search(r"^(?:level\s*)?(\d+)[:\-]?\s*", line_lower)
            if level_match:
                # Save previous level if we have accumulated content
                if power_content_lines:
                    level_num = len(current_power["levels"]) + 1
                    description = " ".join(power_content_lines).strip()
                    if description and len(description.split()) > 2:
                        current_power["levels"].append(
                            {"level": level_num, "description": description}
                        )
                    power_content_lines = []

                # Start new level
                level_num = int(level_match.group(1))
                description = re.sub(r"^(?:level\s*)?\d+[:\-]?\s*", "", line, flags=re.I).strip()
                if description:
                    power_content_lines = [description]
            else:
                # Check if this looks like a level description continuation
                # Level descriptions often start with "You may", "Instead", "Gain", etc.
                is_description = any(
                    line_lower.startswith(prefix)
                    for prefix in [
                        "you may",
                        "instead",
                        "gain",
                        "when",
                        "reduce",
                        "attacking",
                        "target",
                    ]
                ) or (
                    re.match(r"^[A-Z]", line)
                    and len(line.split()) > 2
                    and line_upper
                    not in ["MARKSMAN", "TOUGHNESS"] + [cp.upper() for cp in COMMON_POWERS]
                )

                # Check if this is a continuation of the current description
                is_continuation = (
                    len(line.split()) <= 8
                    and not line[0].isupper()
                    and power_content_lines
                    and not any(cp.upper() in line_upper for cp in COMMON_POWERS)
                )

                if is_description or is_continuation:
                    power_content_lines.append(line)
                elif power_content_lines:
                    # We have accumulated content but hit something that doesn't look like continuation
                    # Check if next line is a new power or if we should save this level
                    next_is_power = False
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        next_upper = next_line.upper()
                        # Check if next line is a common power name
                        if any(
                            cp.upper() in next_upper or next_upper == cp.upper()
                            for cp in COMMON_POWERS
                        ):
                            next_is_power = True

                    # Save accumulated level if we have enough content and haven't hit max levels
                    if len(current_power["levels"]) < 4 and not next_is_power:
                        level_num = len(current_power["levels"]) + 1
                        description = " ".join(power_content_lines).strip()
                        if description and len(description.split()) > 2:
                            current_power["levels"].append(
                                {"level": level_num, "description": description}
                            )
                        power_content_lines = []

        i += 1

    # Don't forget the last power
    if current_power and current_power_type:
        # Save any remaining accumulated level content
        if power_content_lines and len(current_power["levels"]) < 4:
            level_num = len(current_power["levels"]) + 1
            description = " ".join(power_content_lines).strip()
            if description and len(description.split()) > 2:
                current_power["levels"].append({"level": level_num, "description": description})

        if current_power_type == "special":
            data["special_power"] = current_power
        else:
            data["common_powers"].append(current_power)

    # Post-process: ensure special power has at least one level with description
    if data["special_power"] and not data["special_power"].get("levels"):
        # Try to extract description from the text
        gain_patterns = ["gain", "goin", "go in"]
        sanity_patterns = ["sanity", "santiy"]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if this line has gain pattern
            has_gain = any(g in line_lower for g in gain_patterns)
            has_sanity = any(s in line_lower for s in sanity_patterns)

            # Also check surrounding lines for multi-line patterns
            if has_gain and not has_sanity and i + 1 < len(lines):
                for j in range(i + 1, min(i + 4, len(lines))):
                    if any(s in lines[j].lower() for s in sanity_patterns):
                        has_sanity = True
                        break

            if has_gain and has_sanity:
                # Collect multi-line description
                desc_lines = [line.strip()]
                # Look ahead for continuation (up to 3 more lines)
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    # Skip empty lines and common power names
                    if not next_line or any(
                        cp.upper() in next_line.upper() for cp in COMMON_POWERS
                    ):
                        break
                    # Include short lines that might be continuation
                    if len(next_line.split()) <= 10:
                        desc_lines.append(next_line)
                    else:
                        break
                description = " ".join(desc_lines).strip()
                if description and len(description) > 10:
                    data["special_power"]["levels"].append({"level": 1, "description": description})
                    break

    return data


def detect_parsing_issues(front_data: Dict[str, Any], back_data: Dict[str, Any]) -> List[str]:
    """Detect issues with parsed OCR data."""
    issues: List[str] = []

    # Check front card issues
    if not front_data.get("name"):
        issues.append("Missing character name")
    elif len(front_data["name"]) < 3:
        issues.append(f"Character name too short: '{front_data['name']}'")

    if not front_data.get("location"):
        issues.append("Missing location")

    if not front_data.get("motto"):
        issues.append("Missing motto")

    if not front_data.get("story"):
        issues.append("Missing story")

    # Check back card issues
    special_power = back_data.get("special_power")
    if not special_power:
        issues.append("Missing special power")
    elif isinstance(special_power, dict):
        if not special_power.get("name"):
            issues.append("Special power missing name")
        if not special_power.get("levels"):
            issues.append("Special power missing levels")
        elif len(special_power["levels"]) == 0:
            issues.append("Special power has no levels")
        else:
            # Check level descriptions
            for level in special_power["levels"]:
                if isinstance(level, dict):
                    desc = level.get("description", "")
                    if not desc or len(desc) < 10:
                        issues.append(f"Special power level {level.get('level', '?')} has poor description")

    common_powers = back_data.get("common_powers", [])
    if not common_powers:
        issues.append("Missing common powers")
    elif len(common_powers) < 2:
        issues.append(f"Only found {len(common_powers)} common power(s), expected 2")
    else:
        for cp in common_powers:
            if isinstance(cp, dict):
                cp_name = cp.get("name", "")
                if not cp_name:
                    issues.append("Common power missing name")
                cp_levels = cp.get("levels", [])
                if not cp_levels:
                    issues.append(f"Common power '{cp_name}' has no levels")
                elif len(cp_levels) < 4:
                    issues.append(f"Common power '{cp_name}' has only {len(cp_levels)} level(s), expected 4")
                else:
                    # Check level descriptions
                    for level in cp_levels:
                        if isinstance(level, dict):
                            desc = level.get("description", "")
                            if not desc or len(desc) < 10:
                                issues.append(
                                    f"Common power '{cp_name}' level {level.get('level', '?')} has poor description"
                                )

    return issues


def load_existing_character_json(char_dir: Path) -> Optional[CharacterData]:
    """Load existing character.json if it exists."""
    json_path = char_dir / FILENAME_CHARACTER_JSON
    if not json_path.exists():
        return None

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        # Convert dict to CharacterData model
        return CharacterData(**data)
    except (json.JSONDecodeError, Exception) as e:
        console.print(f"[yellow]Warning: Could not load existing {FILENAME_CHARACTER_JSON}: {e}[/yellow]")
        return None


def merge_character_data(
    existing: Optional[CharacterData], parsed: CharacterData, story_file: Optional[Path]
) -> CharacterData:
    """Merge parsed OCR data with existing data, preferring HTML-extracted data."""
    if not existing:
        return parsed

    # Start with existing data (which has HTML-extracted name/story)
    merged = CharacterData(
        name=existing.name,  # Prefer HTML-extracted name
        location=existing.location or parsed.location,  # Use parsed if existing is None
        motto=existing.motto or parsed.motto,  # Use parsed if existing is None
        story=existing.story,  # Prefer HTML-extracted story
    )

    # Use HTML-extracted story if available, otherwise keep existing
    if story_file and story_file.exists():
        story_text = story_file.read_text(encoding="utf-8").strip()
        merged.story = story_text
    elif not merged.story:
        merged.story = parsed.story

    # Merge powers - prefer existing if they exist, otherwise use parsed
    if existing.special_power:
        merged.special_power = existing.special_power
    elif parsed.special_power:
        merged.special_power = parsed.special_power

    # Merge common powers - prefer existing if they exist and are complete
    if existing.common_powers and len(existing.common_powers) >= 2:
        # Check if existing powers have all 4 levels
        all_complete = all(
            len(power.levels) >= 4 for power in existing.common_powers if power.levels
        )
        if all_complete:
            merged.common_powers = existing.common_powers
        else:
            # Merge: use existing power names but update levels if parsed has better data
            merged.common_powers = existing.common_powers
            for existing_power in merged.common_powers:
                # Try to find matching parsed power
                for parsed_power in parsed.common_powers:
                    if parsed_power.name.lower() == existing_power.name.lower():
                        # Use parsed power if it has more complete levels
                        if len(parsed_power.levels) > len(existing_power.levels):
                            existing_power.levels = parsed_power.levels
                        break
    elif parsed.common_powers:
        merged.common_powers = parsed.common_powers

    return merged


def parse_character_images(
    front_path: Path,
    back_path: Path,
    story_file: Optional[Path] = None,
    existing_data: Optional[CharacterData] = None,
) -> Tuple[CharacterData, List[str]]:
    """Parse both front and back images for a character, returning data and issues."""
    console.print("[cyan]Parsing images for character...[/cyan]")

    # Extract text from images
    console.print("  Extracting text from front image...")
    front_text = extract_text_from_image(front_path)
    if not front_text:
        console.print("[yellow]Warning: No text extracted from front image[/yellow]")

    console.print("  Extracting text from back image...")
    back_text = extract_text_from_image(back_path)
    if not back_text:
        console.print("[yellow]Warning: No text extracted from back image[/yellow]")

    # Parse front card
    front_data = parse_front_card(front_text)
    console.print(f"  Parsed front: name={front_data['name']}, location={front_data['location']}")

    # Parse back card
    back_data = parse_back_card(back_text)
    special_power_name = None
    special_power_dict = back_data.get("special_power")
    if special_power_dict and isinstance(special_power_dict, dict):
        special_power_name = special_power_dict.get("name")
    console.print(
        f"  Parsed back: special_power={special_power_name}, "
        f"common_powers={len(back_data.get('common_powers', []))}"
    )

    # Use HTML-extracted story if available, otherwise use OCR-extracted story
    story_text = None
    if story_file and story_file.exists():
        story_text = story_file.read_text(encoding="utf-8").strip()
        console.print(f"  Using HTML-extracted story (length: {len(story_text)} chars)")
    else:
        story_text = front_data["story"]

    # Combine parsed data
    parsed_data = CharacterData(
        name=front_data["name"] or "Unknown",
        location=front_data["location"],
        motto=front_data["motto"],
        story=story_text,
    )

    # Add special power
    special_power_data = back_data.get("special_power")
    if special_power_data and isinstance(special_power_data, dict):
        sp = special_power_data
        parsed_data.special_power = Power(
            name=str(sp.get("name", "")),
            is_special=True,
            levels=[
                PowerLevel(**level) for level in sp.get("levels", []) if isinstance(level, dict)
            ],
        )

    # Add common powers
    common_powers_data = back_data.get("common_powers", [])
    if isinstance(common_powers_data, list):
        for cp in common_powers_data:
            if isinstance(cp, dict):
                parsed_data.common_powers.append(
                    Power(
                        name=str(cp.get("name", "")),
                        is_special=False,
                        levels=[
                            PowerLevel(**level)
                            for level in cp.get("levels", [])
                            if isinstance(level, dict)
                        ],
                    )
                )

    # Detect parsing issues
    issues = detect_parsing_issues(front_data, back_data)

    # Merge with existing data
    merged_data = merge_character_data(existing_data, parsed_data, story_file)

    return merged_data, issues


@click.command()
@click.option(
    "--character-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Directory containing front.jpg and back.jpg for a character",
)
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Root data directory to process all characters",
)
@click.option(
    "--output-format",
    type=click.Choice([OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_YAML], case_sensitive=False),
    default=OUTPUT_FORMAT_JSON,
    help="Output format for character data files",
)
@click.option(
    "--character",
    help="Specific character name to parse (e.g., 'adam')",
)
def main(
    character_dir: Optional[Path],
    data_dir: Path,
    output_format: str,
    character: Optional[str],
):
    """Parse character card images to extract character data."""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Character Parser[/bold cyan]\n"
            "Extracts character data from card images",
            border_style="cyan",
        )
    )

    # Determine which characters to process
    characters_to_process: List[Path] = []

    if character_dir:
        # Process single character directory
        characters_to_process.append(character_dir)
    elif character:
        # Find character in data directory
        char_path = None
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir():
                char_dir = season_dir / character.lower()
                if char_dir.exists():
                    char_path = char_dir
                    break
        if char_path:
            characters_to_process.append(char_path)
        else:
            console.print(f"[red]Character '{character}' not found in {data_dir}[/red]")
            sys.exit(1)
    else:
        # Process all characters in data directory
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir():
                for char_dir in season_dir.iterdir():
                    if char_dir.is_dir():
                        # Check if images exist (either as files or in zip)
                        char_name = char_dir.name
                        zip_path = char_dir / f"{char_name}.zip"
                        front_path = char_dir / FILENAME_FRONT
                        back_path = char_dir / FILENAME_BACK

                        if zip_path.exists() or (front_path.exists() and back_path.exists()):
                            characters_to_process.append(char_dir)

    if not characters_to_process:
        console.print(f"[red]No character directories found in {data_dir}[/red]")
        sys.exit(1)

    console.print(f"\n[green]Found {len(characters_to_process)} characters to process[/green]\n")

    # Process each character
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        for char_dir in characters_to_process:
            task = progress.add_task(f"Processing {char_dir.name}", total=1)

            front_path = char_dir / FILENAME_FRONT
            back_path = char_dir / FILENAME_BACK

            if not front_path.exists() or not back_path.exists():
                console.print(f"[yellow]Skipping {char_dir.name}: missing images[/yellow]")
                progress.update(task, advance=1)
                continue

            try:
                # Load existing character.json if it exists
                existing_data = load_existing_character_json(char_dir)
                if existing_data:
                    console.print(f"  [cyan]Loaded existing {FILENAME_CHARACTER_JSON}[/cyan]")

                # Check for HTML-extracted story file
                story_file = char_dir / FILENAME_STORY_TXT
                story_path = story_file if story_file.exists() else None

                # Parse character data
                character_data, issues = parse_character_images(
                    front_path, back_path, story_path, existing_data
                )

                # Report issues
                if issues:
                    console.print("  [yellow]⚠ Parsing issues detected:[/yellow]")
                    for issue in issues:
                        console.print(f"    • {issue}")
                else:
                    console.print("  [green]✓ No parsing issues detected[/green]")

                # Save to file
                output_file = char_dir / FILENAME_CHARACTER_JSON
                if output_format == OUTPUT_FORMAT_JSON:
                    output_file.write_text(
                        json.dumps(character_data.model_dump(), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                else:
                    output_file = char_dir / f"character.{output_format}"
                    with open(output_file, "w") as f:
                        yaml.dump(
                            character_data.model_dump(),
                            f,
                            default_flow_style=False,
                            sort_keys=False,
                        )

                console.print(f"[green]✓ Saved {output_file}[/green]")
                progress.update(task, advance=1)

            except Exception as e:
                console.print(f"[red]Error processing {char_dir.name}:[/red] {e}")
                progress.update(task, advance=1)

    console.print("\n[green]✓ Parsing complete![/green]")


if __name__ == "__main__":
    main()
