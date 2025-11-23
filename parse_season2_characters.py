#!/usr/bin/env python3
"""
Parse Season 2 character card images to extract story, motto, location, etc.
Updates character.json files with extracted data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from scripts.utils.optimal_ocr import extract_front_card_fields_with_optimal_strategies
    from scripts.utils.ocr import extract_text_from_image
except ImportError as e:
    print(f"Error: Missing import: {e}")
    print("Make sure you're running with: uv run python3 parse_season2_characters.py")
    sys.exit(1)

DATA_DIR = project_root / "data"
SEASON2_DIR = DATA_DIR / "season2" / "characters"


def parse_character(char_dir: Path) -> dict:
    """Parse a single character's card images."""
    char_id = char_dir.name
    
    front_path = None
    back_path = None
    
    # Find front image
    for ext in [".jpg", ".png", ".webp"]:
        if (char_dir / f"front{ext}").exists():
            front_path = char_dir / f"front{ext}"
            break
    
    # Find back image
    for ext in [".jpg", ".png", ".webp"]:
        if (char_dir / f"back{ext}").exists():
            back_path = char_dir / f"back{ext}"
            break
    
    if not front_path:
        print(f"  ⚠ {char_id}: No front image found")
        return {}
    
    print(f"  Parsing {char_id}...")
    
    # Extract front card fields using optimal strategies
    try:
        front_fields = extract_front_card_fields_with_optimal_strategies(front_path)
        
        extracted_data = {
            "name": front_fields.name,
            "location": front_fields.location,
            "motto": front_fields.motto,
            "story": front_fields.story,
        }
        
        # Clean up None values
        extracted_data = {k: v for k, v in extracted_data.items() if v}
        
        return extracted_data
    except Exception as e:
        print(f"  ✗ {char_id}: Error parsing: {e}")
        return {}


def update_character_json(char_dir: Path, extracted_data: dict) -> bool:
    """Update character.json with extracted data."""
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
    
    # Update with extracted data (only if not already present)
    updated = False
    
    if extracted_data.get("story") and not data.get("story"):
        data["story"] = extracted_data["story"]
        updated = True
    
    if extracted_data.get("motto") and not data.get("motto"):
        data["motto"] = extracted_data["motto"]
        updated = True
    
    if extracted_data.get("location") and not data.get("location", {}).get("original"):
        # Update location if we have extracted location
        if isinstance(data.get("location"), dict):
            if not data["location"].get("original"):
                data["location"]["original"] = extracted_data["location"]
                updated = True
        elif not data.get("location"):
            data["location"] = {
                "original": extracted_data["location"],
                "parsed": {
                    "city": None,
                    "administrative_division": None,
                    "administrative_division_type": None,
                    "country": None,
                    "region": None
                },
                "coordinates": None
            }
            updated = True
    
    if extracted_data.get("name") and data.get("name") != extracted_data["name"]:
        # Name might be different (case, etc.) - update if significantly different
        if extracted_data["name"].upper() != data.get("name", "").upper():
            print(f"    Note: Name mismatch - existing: '{data.get('name')}', extracted: '{extracted_data['name']}'")
    
    # Update metadata
    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    # Recalculate completeness
    completeness = 0.0
    if data.get("name"):
        completeness += 0.2
    if data.get("story"):
        completeness += 0.3
    if data.get("motto"):
        completeness += 0.1
    if data.get("location", {}).get("original"):
        completeness += 0.1
    if data.get("common_powers"):
        completeness += 0.1
    if data.get("special_power"):
        completeness += 0.1
    if data.get("images", {}).get("front") or data.get("images", {}).get("back"):
        completeness += 0.1
    
    data["metadata"]["completeness"] = completeness
    
    # Write updated JSON
    try:
        with open(char_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if updated:
            print(f"  ✓ {char_id}: Updated (completeness: {completeness:.1%})")
        else:
            print(f"  ⊘ {char_id}: No new data extracted (completeness: {completeness:.1%})")
        return True
    except Exception as e:
        print(f"  ✗ {char_id}: Error writing JSON: {e}")
        return False


def main():
    """Parse all Season 2 characters."""
    print("=" * 70)
    print("Parsing Season 2 Character Cards")
    print("=" * 70)
    print()
    
    if not SEASON2_DIR.exists():
        print(f"Error: {SEASON2_DIR} does not exist")
        sys.exit(1)
    
    character_dirs = [d for d in SEASON2_DIR.iterdir() if d.is_dir()]
    print(f"Found {len(character_dirs)} characters\n")
    
    success_count = 0
    updated_count = 0
    
    for char_dir in sorted(character_dirs):
        char_id = char_dir.name
        
        # Parse character cards
        extracted_data = parse_character(char_dir)
        
        if extracted_data:
            # Update character.json
            if update_character_json(char_dir, extracted_data):
                success_count += 1
                if any(extracted_data.values()):
                    updated_count += 1
        else:
            success_count += 1  # Still counted as processed
    
    print()
    print("=" * 70)
    print(f"✓ Processed {success_count}/{len(character_dirs)} characters")
    print(f"✓ Updated {updated_count} characters with new data")
    print("=" * 70)


if __name__ == "__main__":
    main()

