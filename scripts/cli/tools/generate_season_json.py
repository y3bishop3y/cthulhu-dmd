#!/usr/bin/env python3
"""
Generate season.json files for each season directory.

Creates comprehensive season metadata including:
- Publication info (year, release date)
- Box images
- Purchase/affiliate links
- Character summaries
- Completeness metadata
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def find_box_image(season_dir: Path) -> Optional[str]:
    """Find box art image in season directory."""
    # Common box image patterns
    patterns = [
        "*box*.jpg",
        "*box*.png",
        "*box*.webp",
        "box.jpg",
        "box.png",
        f"{season_dir.name}-box.jpg",
        f"{season_dir.name}-box.png",
    ]

    for pattern in patterns:
        matches = list(season_dir.glob(pattern))
        if matches:
            return matches[0].name

    return None


def find_character_book(season_dir: Path) -> Optional[str]:
    """Find character book PDF in season directory."""
    pdf_file = season_dir / "character-book.pdf"
    if pdf_file.exists():
        return pdf_file.name
    return None


def get_box_type(season_id: str) -> str:
    """Determine box type from season ID."""
    season_lower = season_id.lower()

    if season_lower == "season1":
        return "base_game"
    elif season_lower.startswith("season"):
        return "expansion"
    elif "promo" in season_lower or "extra" in season_lower:
        return "promo"
    elif "comic" in season_lower:
        return "comic"
    elif "unknowable" in season_lower or "unspeakable" in season_lower:
        return "standalone"
    else:
        return "expansion"  # Default


def format_display_name(season_id: str) -> str:
    """Format season ID into display name."""
    if season_id.startswith("season"):
        num = season_id.replace("season", "")
        return f"Season {num}"
    # Handle kebab-case like "unknowable-box"
    return season_id.replace("-", " ").title()


def get_season_metadata(season_id: str) -> Dict[str, Any]:
    """Get hardcoded metadata for known seasons."""
    # Expanded with publication dates, links, etc.
    metadata = {
        "season1": {
            "year_published": 2019,
            "release_date": "2019-06-01",  # Approximate
            "description": "The original Cthulhu: Death May Die base game featuring 10 investigators battling the Old Ones.",
            "purchase_links": {
                "amazon": None,  # Add when available
                "publisher": "https://cmon.com/product/cthulhu-death-may-die",
                "boardgamegeek": "https://boardgamegeek.com/boardgame/266524/cthulhu-death-may-die",
                "other": [],
            },
        },
        "season2": {
            "year_published": 2020,
            "release_date": "2020-06-01",  # Approximate
            "description": "Season 2 expansion adding 10 new investigators to the Cthulhu: Death May Die universe.",
            "purchase_links": {
                "amazon": "https://www.amazon.com/Cthulu-Expansion-Mystery-Cooperative-Playtime/dp/B07Z7D443R/ref=sr_1_3?crid=UOJ1O5ZWZ8ZT&dib=eyJ2IjoiMSJ9.fz4MR9Iu7cP5_TLvVAgVs93ACJ45ErzfMjL_dW2-yPJ1-MGQguQjzN32jPYB5GxTPDA0lKX4xyFMcIcQ9wl_QLriD6yr7a-XeAFYGUlOgVU9ZHhJeoQA0YoUgVK2Ct3iN6zTDZFLMdFqS-F_dGjTQT6hbbRJf3Lfm_SqvG4Snf27KsD6FGonEKzzHvSkBdGcP6ljzzueUW2g2TPamLlEFtg_StF_Gn32MhmLhpoqOyMKfAiVSon5dElV0SbHeNGqQKGa8Ijy6EfWZ4eBhVNGxV4xHH9WANtsFRCrhUYlMiE.3Lq-9xGlIfi4yO3vAvOGdnK8RQwPcka2CqsiRNIHxC8&dib_tag=se&keywords=cthulhu+dead+may+die&qid=1763857033&sprefix=chathulu+dead+%2Caps%2C185&sr=8-3&ufe=app_do%3Aamzn1.fos.9fe8cbfa-bf43-43d1-a707-3f4e65a4b666",
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "season3": {
            "year_published": 2021,
            "release_date": None,
            "description": "Season 3 expansion with 10 new investigators.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "season4": {
            "year_published": 2022,
            "release_date": None,
            "description": "Season 4 expansion with 5 new investigators.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "unknowable-box": {
            "year_published": None,
            "release_date": None,
            "description": "The Unknowable Box standalone expansion featuring 27 investigators.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "unspeakable-box": {
            "year_published": None,
            "release_date": None,
            "description": "The Unspeakable Box standalone expansion featuring 16 investigators.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "comic-book-extras": {
            "year_published": None,
            "release_date": None,
            "description": "Comic book extras with 6 additional characters.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "comic-book-v2": {
            "year_published": None,
            "release_date": None,
            "description": "Comic book version 2 with 5 additional characters.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
        "extra-promos": {
            "year_published": None,
            "release_date": None,
            "description": "Extra promotional characters.",
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
    }

    return metadata.get(
        season_id,
        {
            "year_published": None,
            "release_date": None,
            "description": None,
            "purchase_links": {
                "amazon": None,
                "publisher": None,
                "boardgamegeek": None,
                "other": [],
            },
        },
    )


def load_characters(season_dir: Path) -> List[Dict[str, str]]:
    """Load character summaries from season directory."""
    characters = []
    chars_dir = season_dir / "characters"

    if not chars_dir.exists():
        return characters

    for char_dir in sorted(chars_dir.iterdir()):
        if not char_dir.is_dir():
            continue

        char_json = char_dir / "character.json"
        if not char_json.exists():
            continue

        try:
            with open(char_json, encoding="utf-8") as f:
                char_data = json.load(f)
                characters.append(
                    {"id": char_data.get("id", char_dir.name), "name": char_data.get("name", "")}
                )
        except Exception as e:
            print(f"  Warning: Error loading {char_json}: {e}")
            # Fallback to directory name
            characters.append(
                {"id": char_dir.name, "name": char_dir.name.replace("-", " ").title()}
            )

    return characters


def calculate_completeness(season_dir: Path, characters: List[Dict[str, str]]) -> Dict[str, Any]:
    """Calculate completeness metrics for the season."""
    chars_dir = season_dir / "characters"
    total_chars = len(characters)

    if total_chars == 0:
        return {
            "data_completeness": 0.0,
            "characters_complete": False,
            "audio_complete": False,
            "images_complete": False,
        }

    chars_with_data = 0
    chars_with_audio = 0
    chars_with_images = 0

    for char_dir in chars_dir.iterdir():
        if not char_dir.is_dir():
            continue

        char_json = char_dir / "character.json"
        if not char_json.exists():
            continue

        try:
            with open(char_json, encoding="utf-8") as f:
                char_data = json.load(f)

                # Check if character has basic data
                if char_data.get("name") and char_data.get("story"):
                    chars_with_data += 1

                # Check for audio
                if char_data.get("has_audio") or char_data.get("audio_file"):
                    chars_with_audio += 1

                # Check for images
                images = char_data.get("images", {})
                if images.get("front", {}).get("jpg") or images.get("front", {}).get("webp"):
                    chars_with_images += 1
        except Exception:
            pass

    data_completeness = (
        (
            (chars_with_data / total_chars * 0.4)
            + (chars_with_audio / total_chars * 0.3)
            + (chars_with_images / total_chars * 0.3)
        )
        if total_chars > 0
        else 0.0
    )

    return {
        "data_completeness": round(data_completeness, 2),
        "characters_complete": chars_with_data == total_chars,
        "audio_complete": chars_with_audio == total_chars,
        "images_complete": chars_with_images == total_chars,
    }


def generate_season_json(season_id: str) -> bool:
    """Generate season.json for a specific season."""
    season_dir = DATA_DIR / season_id

    if not season_dir.exists():
        print(f"  ✗ {season_id}: Directory not found")
        return False

    # Get metadata
    metadata = get_season_metadata(season_id)

    # Find images
    box_art = find_box_image(season_dir)
    character_book = find_character_book(season_dir)

    # Load characters
    characters = load_characters(season_dir)

    # Calculate completeness
    completeness = calculate_completeness(season_dir, characters)

    # Build season JSON
    season_data = {
        "id": season_id,
        "name": format_display_name(season_id).replace("Season ", "Season "),
        "display_name": format_display_name(season_id),
        "description": metadata["description"],
        "year_published": metadata["year_published"],
        "release_date": metadata["release_date"],
        "box_type": get_box_type(season_id),
        "character_count": len(characters),
        "images": {
            "box_art": box_art,
            "box_art_webp": None,  # Can be generated later
            "character_book": character_book,
        },
        "purchase_links": metadata["purchase_links"],
        "metadata": {"last_updated": datetime.now().strftime("%Y-%m-%d"), **completeness},
        "characters": characters,
    }

    # Write season.json
    season_json_path = season_dir / "season.json"
    try:
        with open(season_json_path, "w", encoding="utf-8") as f:
            json.dump(season_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {season_id}: Generated ({len(characters)} characters)")
        return True
    except Exception as e:
        print(f"  ✗ {season_id}: Error writing JSON: {e}")
        return False


def main():
    """Generate season.json files for all seasons."""
    if len(sys.argv) > 1:
        # Generate for specific season
        season_id = sys.argv[1]
        if generate_season_json(season_id):
            sys.exit(0)
        else:
            sys.exit(1)

    # Generate for all seasons
    print("Generating season.json files...")
    print("=" * 60)

    # Find all season directories (exclude non-season dirs like 'indexes')
    exclude_dirs = {"indexes", "__pycache__", ".git"}
    season_dirs = [
        d
        for d in DATA_DIR.iterdir()
        if d.is_dir() and d.name not in exclude_dirs and not d.name.startswith(".")
    ]
    success_count = 0

    for season_dir in sorted(season_dirs):
        if generate_season_json(season_dir.name):
            success_count += 1

    print("=" * 60)
    print(f"✓ Generated {success_count}/{len(season_dirs)} season.json files")


if __name__ == "__main__":
    main()
