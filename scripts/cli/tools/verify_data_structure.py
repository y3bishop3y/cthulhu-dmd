#!/usr/bin/env python3
"""
Verify and report on data directory structure consistency.

Checks all seasons/boxes for:
- Consistent directory structure (flat: data/{season}/{character}/)
- File naming consistency
- Missing character.json files
- Unexpected files/directories
"""

from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Expected seasons/boxes
EXPECTED_SEASONS = [
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

# Expected file patterns for character directories
EXPECTED_FILES = {
    "character.json": True,  # Required
    "front.jpg": False,
    "front.webp": False,
    "front.png": False,
    "back.jpg": False,
    "back.webp": False,
    "back.png": False,
    "story.txt": False,
}

# Files to ignore
IGNORE_PATTERNS = [
    ".DS_Store",
    ".archive",
    "enemies",
    "missions",
    "animation",
]


def check_season_structure(season_dir: Path, season_name: str):
    """Check structure of a single season/box."""
    issues = []
    character_dirs = []

    if not season_dir.exists():
        return {"season": season_name, "exists": False, "issues": ["Directory does not exist"]}

    # Check for nested characters/ directory (should not exist)
    characters_subdir = season_dir / "characters"
    if characters_subdir.exists():
        issues.append("Has nested 'characters/' subdirectory (should be flat)")

    # Find character directories
    for item in season_dir.iterdir():
        if item.name in IGNORE_PATTERNS:
            continue
        if item.is_dir():
            character_dirs.append(item)
        elif item.suffix in [".pdf", ".jpg", ".png"]:
            # Season-level files are OK
            pass

    # Check each character directory
    missing_json = []
    unexpected_files = defaultdict(list)
    missing_front = []
    missing_back = []

    for char_dir in character_dirs:
        char_name = char_dir.name

        # Check for character.json
        char_json = char_dir / "character.json"
        if not char_json.exists():
            missing_json.append(char_name)

        # Check for expected files
        has_front = False
        has_back = False

        for file_name in char_dir.iterdir():
            if file_name.is_dir():
                # Subdirectories (like animation/) are OK
                continue

            file_base = file_name.name

            # Check if it's an expected file
            if file_base in EXPECTED_FILES:
                if "front" in file_base:
                    has_front = True
                if "back" in file_base:
                    has_back = True
            elif not any(file_base.startswith(ignore) for ignore in IGNORE_PATTERNS):
                # Unexpected file
                if not file_base.endswith((".wav", ".gif")):  # Audio/animation files are OK
                    unexpected_files[char_name].append(file_base)

        if not has_front:
            missing_front.append(char_name)
        if not has_back:
            missing_back.append(char_name)

    if missing_json:
        issues.append(f"Missing character.json: {', '.join(missing_json)}")
    if missing_front:
        issues.append(f"Missing front card images: {', '.join(missing_front)}")
    if missing_back:
        issues.append(f"Missing back card images: {', '.join(missing_back)}")
    if unexpected_files:
        for char, files in unexpected_files.items():
            issues.append(f"{char}: Unexpected files: {', '.join(files[:3])}")

    return {
        "season": season_name,
        "exists": True,
        "character_count": len(character_dirs),
        "issues": issues,
        "characters": [d.name for d in character_dirs],
    }


def main():
    """Main verification function."""
    print("=" * 70)
    print("Data Directory Structure Verification")
    print("=" * 70)
    print()

    results = []
    total_characters = 0

    for season_name in EXPECTED_SEASONS:
        season_dir = DATA_DIR / season_name
        result = check_season_structure(season_dir, season_name)
        results.append(result)
        if result["exists"]:
            total_characters += result.get("character_count", 0)

    # Print results
    all_good = True
    for result in results:
        season = result["season"]
        if not result["exists"]:
            print(f"❌ {season}: Directory does not exist")
            all_good = False
        elif result["issues"]:
            print(f"⚠️  {season}: {result['character_count']} characters")
            for issue in result["issues"]:
                print(f"   - {issue}")
            all_good = False
        else:
            print(f"✅ {season}: {result['character_count']} characters - OK")

    print()
    print("=" * 70)
    print(
        f"Summary: {total_characters} total characters across {len([r for r in results if r['exists']])} seasons/boxes"
    )

    if all_good:
        print("✅ All seasons/boxes have consistent structure!")
    else:
        print("⚠️  Some issues found (see above)")

    print("=" * 70)


if __name__ == "__main__":
    main()
