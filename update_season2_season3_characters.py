#!/usr/bin/env python3
"""
Update character JSON files for Season 2 and Season 3.
- Loads story from story.txt if available
- Updates character.json with full schema (id, season, story, etc.)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"


def load_story_from_file(char_dir: Path) -> Optional[str]:
    """Load story from story.txt file if it exists."""
    story_file = char_dir / "story.txt"
    if story_file.exists():
        try:
            return story_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"  Warning: Error reading story.txt: {e}")
    return None


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

    # Load story from story.txt if not in JSON
    story = data.get("story")
    if not story:
        story = load_story_from_file(char_dir)

    # Get location (handle both string and dict formats)
    location = data.get("location")
    if isinstance(location, dict):
        # Already has parsed location, keep it
        pass
    elif isinstance(location, str):
        # Convert string to object format
        location = {
            "original": location,
            "parsed": {
                "city": None,
                "administrative_division": None,
                "administrative_division_type": None,
                "country": None,
                "region": None
            },
            "coordinates": None
        }
    else:
        location = {
            "original": None,
            "parsed": {
                "city": None,
                "administrative_division": None,
                "administrative_division_type": None,
                "country": None,
                "region": None
            },
            "coordinates": None
        }

    # Check for image files
    images = {
        "front": {},
        "back": {}
    }
    if (char_dir / "front.jpg").exists():
        images["front"]["jpg"] = "front.jpg"
    if (char_dir / "front.png").exists():
        images["front"]["png"] = "front.png"
    if (char_dir / "front.webp").exists():
        images["front"]["webp"] = "front.webp"
    if (char_dir / "back.jpg").exists():
        images["back"]["jpg"] = "back.jpg"
    if (char_dir / "back.png").exists():
        images["back"]["png"] = "back.png"
    if (char_dir / "back.webp").exists():
        images["back"]["webp"] = "back.webp"

    # Check for audio files
    audio_files = list(char_dir.glob("*audio*.wav"))
    has_audio = len(audio_files) > 0
    audio_file = audio_files[0].name if audio_files else None

    # Build updated data
    updated_data = {
        "id": char_id,
        "name": data.get("name", ""),
        "season": season_id,
        "motto": data.get("motto"),
        "story": story,
        "location": location,
        "special_power": data.get("special_power"),
        "common_powers": data.get("common_powers", []),
        "links": data.get("links", {
            "wikipedia": None,
            "grokpedia": None,
            "other": []
        }),
        "images": images if any(images["front"]) or any(images["back"]) else data.get("images", {}),
        "has_audio": has_audio,
        "audio_file": audio_file,
        "metadata": {
            "extracted_date": None,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "data_source": "ocr",
            "completeness": 0.0,
        },
    }

    # Calculate basic completeness
    completeness = 0.0
    if updated_data["name"]:
        completeness += 0.2
    if updated_data["story"]:
        completeness += 0.3
    if updated_data["motto"]:
        completeness += 0.1
    if updated_data["location"].get("original"):
        completeness += 0.1
    if updated_data["common_powers"]:
        completeness += 0.1
    if updated_data["special_power"]:
        completeness += 0.1
    if any(updated_data["images"].get("front", {}).values()) or any(updated_data["images"].get("back", {}).values()):
        completeness += 0.1

    updated_data["metadata"]["completeness"] = completeness

    # Write updated JSON
    try:
        with open(char_json_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {char_id}: Updated (completeness: {completeness:.1%})")
        return True
    except Exception as e:
        print(f"  ✗ {char_id}: Error writing JSON: {e}")
        return False


def main():
    """Update character JSON files for Season 2 and Season 3."""
    seasons = ["season2", "season3"]

    for season_id in seasons:
        print(f"\n{'='*70}")
        print(f"Updating {season_id}")
        print(f"{'='*70}")

        season_dir = DATA_DIR / season_id / "characters"
        if not season_dir.exists():
            print(f"  ⚠ {season_id}: characters directory not found")
            continue

        character_dirs = [d for d in season_dir.iterdir() if d.is_dir()]
        print(f"Found {len(character_dirs)} characters\n")

        success_count = 0
        for char_dir in sorted(character_dirs):
            if update_character_json(char_dir, season_id):
                success_count += 1

        print(f"\n✓ Updated {success_count}/{len(character_dirs)} characters in {season_id}")

    print(f"\n{'='*70}")
    print("Character JSON update complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

