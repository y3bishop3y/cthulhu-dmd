#!/usr/bin/env python3
"""
Build inverted index files for fast character search.

Generates:
- powers.json - Maps powers to character IDs
- locations.json - Maps locations (city/administrative_division/country/region) to character IDs
- seasons_index.json - Maps seasons to character IDs
- characters.json - Full character data array (for detailed lookups)
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDEXES_DIR = DATA_DIR / "indexes"


def load_all_characters() -> List[Dict[str, Any]]:
    """Load all character JSON files from all seasons."""
    characters = []
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

    for season_id in seasons:
        season_dir = DATA_DIR / season_id / "characters"
        if not season_dir.exists():
            continue

        for char_dir in season_dir.iterdir():
            if not char_dir.is_dir():
                continue

            char_json = char_dir / "character.json"
            if not char_json.exists():
                continue

            try:
                with open(char_json, encoding="utf-8") as f:
                    char_data = json.load(f)
                    # Ensure we have the character ID
                    if "id" not in char_data:
                        char_data["id"] = char_dir.name
                    if "season" not in char_data:
                        char_data["season"] = season_id
                    characters.append(char_data)
            except Exception as e:
                print(f"Warning: Could not load {char_json}: {e}")

    return characters


def build_powers_index(characters: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build inverted index mapping powers to character IDs."""
    powers_index = defaultdict(list)

    for char in characters:
        char_id = char.get("id") or char.get("name", "").lower().replace(" ", "-")

        # Index common powers
        common_powers = char.get("common_powers", [])
        for power in common_powers:
            if power:  # Skip empty strings
                powers_index[power].append(char_id)

        # Index special power (if exists)
        special_power = char.get("special_power")
        if special_power and isinstance(special_power, dict):
            power_name = special_power.get("name")
            if power_name:
                # Add special power with a prefix to distinguish from common powers
                powers_index[f"Special: {power_name}"].append(char_id)

    # Convert defaultdict to regular dict and sort lists, remove duplicates
    return {power: sorted(set(char_ids)) for power, char_ids in powers_index.items()}


def build_locations_index(characters: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """Build inverted index mapping locations to character IDs."""
    locations_index = {
        "regions": defaultdict(list),
        "countries": defaultdict(list),
        "administrative_divisions": defaultdict(list),
        "cities": defaultdict(list),
    }

    for char in characters:
        char_id = char.get("id") or char.get("name", "").lower().replace(" ", "-")
        location = char.get("location", {})

        if isinstance(location, dict):
            parsed = location.get("parsed", {})

            # Index by region
            region = parsed.get("region")
            if region:
                locations_index["regions"][region].append(char_id)

            # Index by country
            country = parsed.get("country")
            if country:
                locations_index["countries"][country].append(char_id)

            # Index by administrative division (state/province/county/etc.)
            admin_div = parsed.get("administrative_division")
            if admin_div:
                locations_index["administrative_divisions"][admin_div].append(char_id)

            # Index by city
            city = parsed.get("city")
            if city:
                locations_index["cities"][city].append(char_id)

    # Convert defaultdicts to regular dicts and sort lists, remove duplicates
    return {
        "regions": {
            region: sorted(set(char_ids))
            for region, char_ids in locations_index["regions"].items()
        },
        "countries": {
            country: sorted(set(char_ids))
            for country, char_ids in locations_index["countries"].items()
        },
        "administrative_divisions": {
            admin_div: sorted(set(char_ids))
            for admin_div, char_ids in locations_index["administrative_divisions"].items()
        },
        "cities": {
            city: sorted(set(char_ids))
            for city, char_ids in locations_index["cities"].items()
        },
    }


def build_seasons_index(characters: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build index mapping seasons to character IDs."""
    seasons_index = defaultdict(list)

    for char in characters:
        char_id = char.get("id") or char.get("name", "").lower().replace(" ", "-")
        season = char.get("season")
        if season:
            seasons_index[season].append(char_id)

    return {season: sorted(set(char_ids)) for season, char_ids in seasons_index.items()}


def main():
    """Build all inverted index files."""
    print("=" * 70)
    print("Building Inverted Indexes")
    print("=" * 70)
    print(f"Data directory: {DATA_DIR}")
    print(f"Indexes directory: {INDEXES_DIR}\n")

    # Create indexes directory
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    # Load all characters
    print("[1/4] Loading all character data...")
    characters = load_all_characters()
    print(f"  ✓ Loaded {len(characters)} characters\n")

    if not characters:
        print("Error: No characters found!")
        sys.exit(1)

    # Build powers index
    print("[2/4] Building powers index...")
    powers_index = build_powers_index(characters)
    powers_file = INDEXES_DIR / "powers.json"
    with open(powers_file, "w", encoding="utf-8") as f:
        json.dump(powers_index, f, indent=2, ensure_ascii=False)
    print(f"  ✓ powers.json: {len(powers_index)} powers indexed")

    # Build locations index
    print("\n[3/4] Building locations index...")
    locations_index = build_locations_index(characters)
    locations_file = INDEXES_DIR / "locations.json"
    with open(locations_file, "w", encoding="utf-8") as f:
        json.dump(locations_index, f, indent=2, ensure_ascii=False)
    print("  ✓ locations.json:")
    print(f"    - {len(locations_index['regions'])} regions")
    print(f"    - {len(locations_index['countries'])} countries")
    print(f"    - {len(locations_index['administrative_divisions'])} administrative divisions")
    print(f"    - {len(locations_index['cities'])} cities")

    # Build seasons index
    print("\n[4/4] Building seasons index...")
    seasons_index = build_seasons_index(characters)
    seasons_file = INDEXES_DIR / "seasons_index.json"
    with open(seasons_file, "w", encoding="utf-8") as f:
        json.dump(seasons_index, f, indent=2, ensure_ascii=False)
    print(f"  ✓ seasons_index.json: {len(seasons_index)} seasons indexed")

    # Build full characters array (optional, for detailed lookups)
    print("\n[5/5] Building characters array...")
    characters_file = INDEXES_DIR / "characters.json"
    with open(characters_file, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)
    print(f"  ✓ characters.json: {len(characters)} characters")

    print("\n" + "=" * 70)
    print("✓ All indexes built successfully!")
    print("=" * 70)
    print(f"Output directory: {INDEXES_DIR}")


if __name__ == "__main__":
    main()
