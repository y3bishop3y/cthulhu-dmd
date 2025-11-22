#!/usr/bin/env python3
"""Diagnostic script to check story extraction for a specific character."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import cv2

from scripts.cli.parse.parsing_constants import (
    FRONT_CARD_STORY_HEIGHT_PERCENT,
    FRONT_CARD_STORY_START_PERCENT,
)
from scripts.core.parsing.layout import CardLayoutExtractor
from scripts.utils.optimal_ocr import (
    extract_text_from_region_with_strategy,
    load_optimal_strategies,
)


def diagnose_story_extraction(character_dir: Path) -> None:
    """Diagnose story extraction for a character."""
    front_path = None
    for ext in [".png", ".jpg", ".webp"]:
        candidate = character_dir / f"front{ext}"
        if candidate.exists():
            front_path = candidate
            break

    if not front_path:
        print(f"ERROR: No front card image found in {character_dir}")
        return

    print(f"Analyzing story extraction for: {character_dir.name}")
    print(f"Front card: {front_path}")
    print()

    # Load image to get dimensions
    img = cv2.imread(str(front_path))
    if img is None:
        print(f"ERROR: Could not load image {front_path}")
        return

    img_height, img_width = img.shape[:2]
    print(f"Image dimensions: {img_width}x{img_height}")
    print()

    # Method 1: extract_description_region (CardLayoutExtractor)
    print("=" * 80)
    print("METHOD 1: CardLayoutExtractor.extract_description_region()")
    print("=" * 80)
    extractor = CardLayoutExtractor()
    story_text_1 = extractor.extract_description_region(front_path)
    print(f"Raw text (length: {len(story_text_1)}):")
    print(repr(story_text_1))
    print()
    print("Cleaned text:")
    print(story_text_1)
    print()

    # Method 2: Region-based extraction with optimal strategy
    print("=" * 80)
    print("METHOD 2: Region-based extraction with optimal strategy")
    print("=" * 80)
    story_start = int(img_height * FRONT_CARD_STORY_START_PERCENT)
    story_height = int(img_height * FRONT_CARD_STORY_HEIGHT_PERCENT)
    bottom_region = (0, story_start, img_width, story_height)
    print(f"Story region: X=0, Y={story_start}, Width={img_width}, Height={story_height}")
    print(
        f"Story region percentages: Y={FRONT_CARD_STORY_START_PERCENT * 100:.1f}%, Height={FRONT_CARD_STORY_HEIGHT_PERCENT * 100:.1f}%"
    )
    print()

    # Load optimal strategies
    config = load_optimal_strategies()
    story_strategy = config.get("story", {}).get("strategy", "tesseract_enhanced_psm3")
    print(f"Using strategy: {story_strategy}")
    print()

    story_text_2 = extract_text_from_region_with_strategy(front_path, bottom_region, story_strategy)
    print(f"Raw text (length: {len(story_text_2)}):")
    print(repr(story_text_2))
    print()
    print("Cleaned text:")
    print(story_text_2)
    print()

    # Show what's currently in the JSON
    json_path = character_dir / "character.json"
    if json_path.exists():
        import json

        with open(json_path) as f:
            data = json.load(f)
            current_story = data.get("story", "")
            print("=" * 80)
            print("CURRENT STORY IN JSON:")
            print("=" * 80)
            print(current_story[:500] + "..." if len(current_story) > 500 else current_story)
            print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_story_extraction.py <character_dir>")
        print("Example: python diagnose_story_extraction.py data/season1/the-kid")
        sys.exit(1)

    character_dir = Path(sys.argv[1])
    if not character_dir.exists():
        print(f"ERROR: Directory not found: {character_dir}")
        sys.exit(1)

    diagnose_story_extraction(character_dir)
