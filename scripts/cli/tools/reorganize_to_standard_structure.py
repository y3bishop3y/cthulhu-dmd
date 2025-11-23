#!/usr/bin/env python3
"""
Reorganize ALL seasons/boxes to standard structure:

data/{season}/
  characters/
    {character}/
      character.json
      front.jpg
      back.jpg
      ...
  enemies/
  missions/
  elder-ones/  (if applicable)
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Seasons/boxes to reorganize
SEASONS = [
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

# Directories to create in each season
STANDARD_DIRS = ["characters", "enemies", "missions"]

# Directories/files to ignore (not character directories)
IGNORE_ITEMS = {
    "characters",
    "enemies",
    "missions",
    "elder-ones",
    "character-book.pdf",
    ".DS_Store",
    ".archive",
}


def get_character_directories(season_dir: Path):
    """Get list of character directories (directories that contain character.json)."""
    character_dirs = []
    for item in season_dir.iterdir():
        if item.is_dir() and item.name not in IGNORE_ITEMS:
            # Check if it's a character directory (has character.json)
            if (item / "character.json").exists():
                character_dirs.append(item)
    return character_dirs


def reorganize_season(season_name: str):
    """Reorganize a single season/box to standard structure."""
    season_dir = DATA_DIR / season_name

    if not season_dir.exists():
        print(f"  ⚠ {season_name}: Directory does not exist")
        return False

    print(f"\n[{season_name}]")

    # Create standard directories
    characters_dir = season_dir / "characters"
    characters_dir.mkdir(exist_ok=True)

    for dir_name in STANDARD_DIRS:
        (season_dir / dir_name).mkdir(exist_ok=True)

    # Find character directories (currently at season root)
    character_dirs = get_character_directories(season_dir)

    if not character_dirs:
        print("  ✓ Already organized (no characters at root level)")
        return True

    print(f"  Found {len(character_dirs)} character directories to move")

    # Move each character directory into characters/
    moved_count = 0
    for char_dir in character_dirs:
        dest = characters_dir / char_dir.name
        if dest.exists():
            print(f"  ⚠ {char_dir.name}: Already exists in characters/, skipping")
        else:
            print(f"  → Moving {char_dir.name}/ to characters/")
            shutil.move(str(char_dir), str(dest))
            moved_count += 1

    print(f"  ✓ Moved {moved_count} character directories")
    return True


def main():
    """Main reorganization function."""
    print("=" * 70)
    print("Reorganizing ALL seasons/boxes to standard structure")
    print("=" * 70)
    print("\nTarget structure:")
    print("  data/{season}/")
    print("    characters/")
    print("      {character}/")
    print("    enemies/")
    print("    missions/")
    print("=" * 70)

    success_count = 0
    for season_name in SEASONS:
        if reorganize_season(season_name):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"✓ Reorganization complete! Processed {success_count}/{len(SEASONS)} seasons/boxes")
    print("=" * 70)


if __name__ == "__main__":
    main()
