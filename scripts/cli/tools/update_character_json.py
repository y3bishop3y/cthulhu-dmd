#!/usr/bin/env python3
"""
Update character JSON files with new schema fields.

Adds:
- id field
- season field
- Enhanced location structure (original + parsed)
- links (Wikipedia, Grokpedia for historical/fictional characters)
- images object
- audio_file references
- metadata
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOCATION_DATA_FILE = DATA_DIR / "location_data.json"
CHARACTER_LINKS_FILE = DATA_DIR / "character_links.json"


def load_character_links() -> Dict[str, Dict[str, Any]]:
    """Load character links from JSON file."""
    if not CHARACTER_LINKS_FILE.exists():
        return {}

    try:
        with open(CHARACTER_LINKS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Error loading character links: {e}")
        return {}


# Load character links once at module level
CHARACTER_LINKS = load_character_links()


# Load location data from JSON file
def load_location_data() -> Dict[str, Any]:
    """Load location parsing data from JSON file."""
    if not LOCATION_DATA_FILE.exists():
        print(f"Warning: {LOCATION_DATA_FILE} not found. Using empty defaults.")
        return {
            "administrative_division_types": {},
            "country_to_region": {},
            "us_states": [],
            "location_coordinates": {},
        }

    try:
        with open(LOCATION_DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading location data: {e}")
        return {
            "administrative_division_types": {},
            "country_to_region": {},
            "us_states": [],
            "location_coordinates": {},
        }


# Load location data once at module level
_location_data = load_location_data()
ADMIN_DIVISION_TYPES = _location_data.get("administrative_division_types", {})
COUNTRY_TO_REGION = _location_data.get("country_to_region", {})
US_STATES = _location_data.get("us_states", [])
LOCATION_COORDS = _location_data.get("location_coordinates", {})


def parse_location(location_str: Optional[str]) -> Dict[str, Any]:
    """Parse location string into structured format with appropriate administrative division type."""
    if not location_str or (isinstance(location_str, str) and location_str.upper() == "UNKNOWN"):
        return {
            "original": location_str,
            "parsed": {
                "city": None,
                "administrative_division": None,
                "administrative_division_type": None,
                "country": None,
                "region": None,
            },
            "coordinates": None,
        }

    # Check if we have a manual mapping
    if isinstance(location_str, str):
        location_upper = location_str.upper()
        if location_upper in LOCATION_COORDS:
            coords = LOCATION_COORDS[location_upper]
            return {
                "original": location_str,
                "parsed": {
                    "city": coords["city"],
                    "administrative_division": coords.get("administrative_division"),
                    "administrative_division_type": coords.get("administrative_division_type"),
                    "country": coords["country"],
                    "region": coords["region"],
                },
                "coordinates": {"lat": coords["lat"], "lon": coords["lon"]}
                if coords.get("lat")
                else None,
            }

        # Try to parse format: "CITY, STATE" or "CITY, COUNTRY"
        parts = [p.strip() for p in location_str.split(",")]

        if len(parts) == 2:
            city = parts[0].title()
            second_part = parts[1].title()

            # Check if second part is a US state
            if second_part in US_STATES:
                return {
                    "original": location_str,
                    "parsed": {
                        "city": city,
                        "administrative_division": second_part,
                        "administrative_division_type": "state",
                        "country": "USA",
                        "region": "North America",
                    },
                    "coordinates": None,
                }
            else:
                # Assume it's a country
                region = COUNTRY_TO_REGION.get(second_part, None)
                admin_type = ADMIN_DIVISION_TYPES.get(second_part, None)

                return {
                    "original": location_str,
                    "parsed": {
                        "city": city,
                        "administrative_division": None,  # We don't have this info from just "CITY, COUNTRY"
                        "administrative_division_type": admin_type,
                        "country": second_part,
                        "region": region,
                    },
                    "coordinates": None,
                }

    # Fallback - just store original
    return {
        "original": location_str if isinstance(location_str, str) else None,
        "parsed": {
            "city": None,
            "administrative_division": None,
            "administrative_division_type": None,
            "country": None,
            "region": None,
        },
        "coordinates": None,
    }


def get_image_files(char_dir: Path) -> Dict[str, Any]:
    """Detect available image files."""
    images = {"front": {"jpg": None, "webp": None}, "back": {"jpg": None, "webp": None}}

    for img_type in ["front", "back"]:
        for ext in ["jpg", "webp"]:
            img_path = char_dir / f"{img_type}.{ext}"
            if img_path.exists():
                images[img_type][ext] = f"{img_type}.{ext}"

    return images


def get_audio_file(char_dir: Path, char_id: str) -> Optional[str]:
    """Find audio file in character directory."""
    # Check for existing audio files
    audio_patterns = [f"{char_id}_audio*.wav", "*_audio*.wav", "*.wav"]

    for pattern in audio_patterns:
        for audio_file in char_dir.glob(pattern):
            return audio_file.name

    return None


def get_character_links(char_id: str, char_name: str) -> Dict[str, Any]:
    """Get Wikipedia/Grokpedia links for historical/fictional characters."""
    links = {"wikipedia": None, "grokpedia": None, "other": []}

    # Check if we have a mapping
    if char_id.lower() in CHARACTER_LINKS:
        links.update(CHARACTER_LINKS[char_id.lower()])

    return links


def calculate_completeness(data: Dict[str, Any]) -> float:
    """Calculate completeness score (0-1)."""
    score = 0.0
    max_score = 10.0

    if data.get("name"):
        score += 1.0
    if data.get("motto"):
        score += 0.5
    if data.get("story"):
        score += 1.0
    if data.get("location", {}).get("original"):
        score += 0.5
    if data.get("location", {}).get("parsed", {}).get("city"):
        score += 0.5
    if data.get("special_power"):
        score += 1.0
    if data.get("common_powers") and len(data["common_powers"]) > 0:
        score += 1.0
    if data.get("images", {}).get("front", {}).get("jpg"):
        score += 1.0
    if data.get("images", {}).get("back", {}).get("jpg"):
        score += 1.0
    if data.get("audio_file"):
        score += 1.0
    if data.get("links", {}).get("wikipedia"):
        score += 0.5
    if data.get("links", {}).get("grokpedia"):
        score += 0.5

    return min(score / max_score, 1.0)


def update_character_json(char_dir: Path, season_id: str) -> bool:
    """Update a single character JSON file."""
    char_json_path = char_dir / "character.json"
    char_id = char_dir.name

    if not char_json_path.exists():
        print(f"  ⚠ {char_id}: character.json not found")
        return False

    # Load existing JSON
    try:
        with open(char_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ✗ {char_id}: Error loading JSON: {e}")
        return False

    # Get original location string (handle both string and dict formats)
    original_location = data.get("location")
    if isinstance(original_location, dict):
        # Already updated, extract original string
        original_location = original_location.get("original")

    # Update with new schema
    updated_data = {
        "id": char_id,
        "name": data.get("name", ""),
        "season": season_id,
        "motto": data.get("motto"),
        "story": data.get("story"),
        "location": parse_location(original_location),
        "special_power": data.get("special_power"),
        "common_powers": data.get("common_powers", []),
        "links": get_character_links(char_id, data.get("name", "")),
        "images": get_image_files(char_dir),
        "has_audio": get_audio_file(char_dir, char_id) is not None,
        "audio_file": get_audio_file(char_dir, char_id),
        "metadata": {
            "extracted_date": None,  # Could parse from git history if needed
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "data_source": "ocr",  # Default, could be enhanced
            "completeness": 0.0,  # Will calculate below
        },
    }

    # Calculate completeness
    updated_data["metadata"]["completeness"] = calculate_completeness(updated_data)

    # Write updated JSON
    try:
        with open(char_json_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {char_id}: Updated")
        return True
    except Exception as e:
        print(f"  ✗ {char_id}: Error writing JSON: {e}")
        return False


def main():
    """Update all character JSON files in a season."""

    if len(sys.argv) < 2:
        print("Usage: update_character_json.py <season-id>")
        print("Example: update_character_json.py season1")
        sys.exit(1)

    season_id = sys.argv[1]
    season_dir = DATA_DIR / season_id / "characters"

    if not season_dir.exists():
        print(f"Error: {season_dir} does not exist")
        sys.exit(1)

    print(f"Updating character JSON files for {season_id}...")
    print("=" * 60)

    character_dirs = [d for d in season_dir.iterdir() if d.is_dir()]
    success_count = 0

    for char_dir in sorted(character_dirs):
        if update_character_json(char_dir, season_id):
            success_count += 1

    print("=" * 60)
    print(f"✓ Updated {success_count}/{len(character_dirs)} characters")


if __name__ == "__main__":
    main()
