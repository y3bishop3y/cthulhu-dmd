#!/usr/bin/env python3
"""
Utilities for using optimal OCR strategies based on benchmark results.

This module provides functions to extract text using the best OCR strategy
for each category (name, location, motto, story, special_power, etc.)
as determined by benchmark testing.
"""

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, Final, List, Optional, Tuple

from scripts.cli.parse.parsing_models import FieldStrategies, FrontCardFields, ImageRegions

# Motto extraction constants
MOTTO_MIN_WORDS: Final[int] = 2
MOTTO_MAX_WORDS_QUOTED: Final[int] = 15
MOTTO_MAX_CHARS_QUOTED: Final[int] = 150
MOTTO_MIN_WORDS_COMBINED: Final[int] = 3
MOTTO_MIN_WORDS_PHRASE: Final[int] = 4
MOTTO_MAX_WORDS_SINGLE: Final[int] = 10
MOTTO_MAX_CHARS_SINGLE: Final[int] = 100
MOTTO_MIN_ALNUM_RATIO: Final[float] = 0.3
MOTTO_MIN_LINE_LENGTH: Final[int] = 2
MOTTO_MAX_ALL_CAPS_LENGTH: Final[int] = 5
MOTTO_MAX_GARBAGE_BEFORE_QUOTE: Final[int] = 15  # Max chars of garbage before quote to remove

# Story extraction constants
STORY_MIN_LENGTH: Final[int] = 10  # Minimum story text length to consider valid

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from scripts.core.parsing.ocr_engines import get_all_strategies
except ImportError as e:
    print(f"Error: Missing required import: {e}\n", file=sys.stderr)
    raise


def load_optimal_strategies(config_path: Optional[Path] = None) -> Dict[str, Dict]:
    """Load optimal OCR strategies from config file.

    Args:
        config_path: Optional path to config file (defaults to scripts/data/optimal_ocr_strategies.json)

    Returns:
        Dictionary with optimal strategy configuration
    """
    if config_path is None:
        config_path = project_root / "scripts" / "data" / "optimal_ocr_strategies.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Optimal strategies config not found: {config_path}\n"
            "Run benchmark first to generate optimal strategies."
        )

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return config


def get_optimal_strategy_for_category(
    category: str, config: Optional[Dict[str, Dict]] = None
) -> Optional[str]:
    """Get the optimal strategy name for a specific category.

    Args:
        category: Category name (name, location, motto, story, special_power, etc.)
        config: Optional pre-loaded config (will load if not provided)

    Returns:
        Strategy name or None if not found
    """
    if config is None:
        config = load_optimal_strategies()

    strategy_info = config.get("strategies", {}).get(category)
    if strategy_info:
        return strategy_info.get("strategy_name")

    return None


def extract_text_with_optimal_strategy(
    image_path: Path,
    category: str = "story",
    config: Optional[Dict[str, Dict]] = None,
    fallback_strategy: Optional[str] = None,
) -> str:
    """Extract text from image using optimal strategy for category.

    Args:
        image_path: Path to image file
        category: Category name (name, location, motto, story, special_power, etc.)
        config: Optional pre-loaded config (will load if not provided)
        fallback_strategy: Fallback strategy name if optimal not found

    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # If config doesn't exist, use fallback
            if fallback_strategy:
                return _extract_with_strategy(image_path, fallback_strategy)
            # Last resort: use first available strategy
            strategies = get_all_strategies()
            if strategies:
                return strategies[0].extract(image_path)
            return ""

    # Get optimal strategy for category
    strategy_name = get_optimal_strategy_for_category(category, config)

    if not strategy_name:
        # Try fallback
        if fallback_strategy:
            return _extract_with_strategy(image_path, fallback_strategy)
        # Last resort
        strategies = get_all_strategies()
        if strategies:
            return strategies[0].extract(image_path)
        return ""

    return _extract_with_strategy(image_path, strategy_name)


def extract_front_card_with_optimal_strategy(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> str:
    """Extract text from front card using optimal strategy.

    Uses the strategy optimized for story extraction (most important front card field).

    Args:
        image_path: Path to front card image
        config: Optional pre-loaded config

    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback to basic strategy
            return _extract_with_strategy(image_path, "tesseract_basic_psm3")

    # Use front_card_strategy if available, otherwise use story strategy
    front_strategy = config.get("front_card_strategy", {}).get("strategy_name")
    if not front_strategy:
        front_strategy = get_optimal_strategy_for_category("story", config)

    if front_strategy:
        return _extract_with_strategy(image_path, front_strategy)

    # Fallback
    return _extract_with_strategy(image_path, "tesseract_basic_psm3")


def extract_back_card_with_optimal_strategy(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> str:
    """Extract text from back card using optimal strategy.

    Uses the strategy optimized for special power extraction (most important back card field).

    Args:
        image_path: Path to back card image
        config: Optional pre-loaded config

    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback to basic strategy
            return _extract_with_strategy(image_path, "tesseract_basic_psm3")

    # Use back_card_strategy if available, otherwise use special_power strategy
    back_strategy = config.get("back_card_strategy", {}).get("strategy_name")
    if not back_strategy:
        back_strategy = get_optimal_strategy_for_category("special_power", config)

    if back_strategy:
        return _extract_with_strategy(image_path, back_strategy)

    # Fallback
    return _extract_with_strategy(image_path, "tesseract_basic_psm3")


def _extract_with_strategy(image_path: Path, strategy_name: str) -> str:
    """Extract text using a specific strategy by name.

    Args:
        image_path: Path to image file
        strategy_name: Name of OCR strategy

    Returns:
        Extracted text
    """
    strategies = get_all_strategies()
    strategy_dict = {s.name: s for s in strategies}

    strategy = strategy_dict.get(strategy_name)
    if not strategy:
        # Strategy not found, use first available
        if strategies:
            return strategies[0].extract(image_path)
        return ""

    return strategy.extract(image_path)


def _get_field_strategies(config: Dict[str, Dict]) -> FieldStrategies:
    """Get optimal OCR strategies for each field from config.

    Args:
        config: Optimal strategies configuration

    Returns:
        FieldStrategies model with strategy names for each field
    """
    return FieldStrategies(
        name=get_optimal_strategy_for_category("name", config) or "tesseract_bilateral_psm3",
        location=get_optimal_strategy_for_category("location", config) or "tesseract_bilateral_psm3",
        motto=get_optimal_strategy_for_category("motto", config) or "tesseract_bilateral_psm3",
        story=get_optimal_strategy_for_category("story", config) or "tesseract_enhanced_psm3",
    )


def _get_image_regions(img_height: int, img_width: int) -> ImageRegions:
    """Calculate region coordinates for front card fields.

    Args:
        img_height: Image height in pixels
        img_width: Image width in pixels

    Returns:
        ImageRegions model with region coordinates for each field
    """
    top_height = int(img_height * 0.25)
    return ImageRegions(
        name=(0, 0, img_width, top_height // 2),
        location=(0, top_height // 2, img_width, top_height // 2),
        motto=(
            0,
            int(img_height * 0.30),
            img_width,
            int(img_height * 0.65) - int(img_height * 0.30),
        ),
        story=(0, int(img_height * 0.60), img_width, int(img_height * 0.40)),
    )


def _parse_name_from_text(text: str) -> str:
    """Parse character name from extracted text.

    Args:
        text: Raw OCR text from name region

    Returns:
        Extracted name or empty string
    """
    name_lines = [line.strip() for line in text.split("\n") if line.strip()]
    # Sort by length descending to prefer longer matches
    sorted_lines = sorted(name_lines, key=len, reverse=True)
    for line in sorted_lines:
        if line.isupper() and len(line) >= 3:
            return line
    return ""


def _parse_location_from_text(text: str) -> str:
    """Parse character location from extracted text.

    Args:
        text: Raw OCR text from location region

    Returns:
        Extracted location or empty string
    """
    location_lines = [line.strip() for line in text.split("\n") if line.strip()]
    # Sort by length descending to prefer longer matches
    sorted_lines = sorted(location_lines, key=len, reverse=True)
    for line in sorted_lines:
        if line.isupper() and len(line) >= 3:
            return line
    return ""


def _filter_motto_lines(lines: List[str]) -> List[str]:
    """Filter out name/location lines and OCR garbage from motto lines.

    Args:
        lines: List of text lines from motto region

    Returns:
        Filtered list of lines that might be mottos
    """
    filtered = []
    for line in lines:
        # Skip all-caps lines longer than threshold (likely name/location that leaked in)
        if line.isupper() and len(line) > MOTTO_MAX_ALL_CAPS_LENGTH:
            continue
        # Skip very short lines
        if len(line) < MOTTO_MIN_LINE_LENGTH:
            continue
        # Skip lines that are mostly symbols/numbers (less than threshold alphanumeric)
        alnum_ratio = sum(c.isalnum() for c in line) / len(line) if line else 0
        if alnum_ratio < MOTTO_MIN_ALNUM_RATIO:
            continue
        filtered.append(line)
    return filtered


def _extract_quoted_motto(filtered_lines: List[str]) -> str:
    """Extract motto from lines containing quotes.

    Args:
        filtered_lines: Filtered motto lines

    Returns:
        Extracted motto or empty string
    """
    for line in filtered_lines:
        if '"' in line or "'" in line:
            word_count = len(line.split())
            if (
                MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_QUOTED
                and len(line) < MOTTO_MAX_CHARS_QUOTED
            ):
                # Try to extract just the quoted part
                quoted_match = re.search(r'["\']([^"\']+)["\']', line)
                if quoted_match:
                    motto = quoted_match.group(1).strip()
                    if len(motto.split()) >= MOTTO_MIN_WORDS:  # At least minimum words
                        return motto
                else:
                    return line
    return ""


def _extract_combined_motto(filtered_lines: List[str]) -> str:
    """Extract motto by combining consecutive lines.

    Args:
        filtered_lines: Filtered motto lines

    Returns:
        Extracted motto or empty string
    """
    if len(filtered_lines) < 2:
        return ""

    for i in range(len(filtered_lines) - 1):
        line1 = filtered_lines[i]
        line2 = filtered_lines[i + 1]

        # Skip if either line looks like name/location (all caps)
        if (
            (line1.isupper() and len(line1) > MOTTO_MIN_WORDS_COMBINED)
            or (line2.isupper() and len(line2) > MOTTO_MIN_WORDS_COMBINED)
        ):
            continue

        combined = f"{line1} {line2}".strip()
        word_count = len(combined.split())

        # Combined mottos can be longer (up to max words and chars)
        if (
            MOTTO_MIN_WORDS_COMBINED <= word_count <= MOTTO_MAX_WORDS_QUOTED
            and len(combined) < MOTTO_MAX_CHARS_QUOTED
        ):
            # Check if it looks like a motto (has quotes, ends with punctuation)
            if '"' in combined or combined.endswith(('.', '!', '?', '."', '!"', '?"')):
                return combined
            # Or if both lines together form a reasonable phrase
            elif word_count >= MOTTO_MIN_WORDS_PHRASE:
                # Prefer if it has quotes or looks complete
                if '"' in combined or any(p in combined for p in ['.', '!', '?']):
                    return combined
    return ""


def _extract_single_line_motto(filtered_lines: List[str]) -> str:
    """Extract motto from single lines (last resort).

    Args:
        filtered_lines: Filtered motto lines

    Returns:
        Extracted motto or empty string
    """
    for line in filtered_lines:
        # Skip all-caps (likely name/location)
        if line.isupper():
            continue
        word_count = len(line.split())
        if MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_SINGLE and len(line) < MOTTO_MAX_CHARS_SINGLE:
            return line
    return ""


def _clean_motto_text(motto: str) -> str:
    """Clean up motto text by removing OCR artifacts and fixing common errors.

    Args:
        motto: Raw motto text

    Returns:
        Cleaned motto text
    """
    if not motto:
        return ""

    # Remove leading/trailing pipes, dashes, and other OCR artifacts
    motto = re.sub(r'^[-|~_\s]+', '', motto)
    motto = re.sub(r'[-|~_\s]+$', '', motto)
    # Remove pipes and other separators in the middle
    motto = re.sub(r'\s*[|~_]\s*', ' ', motto)
    # Remove leading prefixes like "- |" or "id —~—~~ ie 4" before quotes
    motto = re.sub(r'^[-|\s~_id0-9]+\s*["\']', '"', motto)
    # Remove leading garbage before quotes (more aggressive)
    if '"' in motto or "'" in motto:
        quote_char = '"' if '"' in motto else "'"
        quote_start = motto.find(quote_char)
        if quote_start > 0 and quote_start < MOTTO_MAX_GARBAGE_BEFORE_QUOTE:
            motto = motto[quote_start:]
    # Fix common OCR errors in mottos
    motto = motto.replace('qT.', 'is')
    motto = motto.replace('wriften', 'written')
    motto = motto.replace('writen', 'written')
    motto = motto.replace('writtn', 'written')
    # Fix duplicate words (common OCR error: "is is" -> "is")
    motto = re.sub(r'\b(\w+)\s+\1\b', r'\1', motto)
    # Clean up multiple spaces
    motto = re.sub(r'\s+', ' ', motto).strip()
    # Remove trailing incomplete words (common OCR error at end)
    motto = re.sub(r'\s+\w{1,2}$', '', motto)

    return motto


def _parse_motto_from_text(text: str) -> str:
    """Parse character motto from extracted text.

    Args:
        text: Raw OCR text from motto region

    Returns:
        Extracted and cleaned motto or empty string
    """
    motto_lines = [line.strip() for line in text.split("\n") if line.strip()]
    filtered_lines = _filter_motto_lines(motto_lines)

    # Try different extraction strategies in order
    motto = _extract_quoted_motto(filtered_lines)
    if not motto:
        motto = _extract_combined_motto(filtered_lines)
    if not motto:
        motto = _extract_single_line_motto(filtered_lines)

    return _clean_motto_text(motto)


def _extract_story_text(
    image_path: Path, extractor, img_height: int, img_width: int, story_strategy: str
) -> str:
    """Extract story text from bottom region of front card.

    Args:
        image_path: Path to front card image
        extractor: CardLayoutExtractor instance
        img_height: Image height
        img_width: Image width
        story_strategy: OCR strategy to use for story extraction

    Returns:
        Extracted story text
    """
    # Use specialized extraction for white-on-black text
    story_text = extractor.extract_description_region(image_path)

    # If story extraction failed, try with optimal strategy on bottom region
    if not story_text or len(story_text) < STORY_MIN_LENGTH:
        bottom_region = (0, int(img_height * 0.60), img_width, int(img_height * 0.40))
        story_text = extract_text_from_region_with_strategy(
            image_path, bottom_region, story_strategy
        )

    return story_text or ""


def extract_text_from_region_with_strategy(
    image_path: Path,
    region: Tuple[int, int, int, int],
    strategy_name: str,
) -> str:
    """Extract text from a specific image region using an OCR strategy.

    Args:
        image_path: Path to full image file
        region: (x, y, width, height) bounding box
        strategy_name: Name of OCR strategy to use

    Returns:
        Extracted text from region
    """
    if cv2 is None or np is None:
        raise ImportError("cv2 and numpy required for region extraction")

    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Crop region
    x, y, w, h = region
    # Ensure coordinates are within image bounds
    x = max(0, x)
    y = max(0, y)
    w = min(w, img.shape[1] - x)
    h = min(h, img.shape[0] - y)

    if w <= 0 or h <= 0:
        return ""

    cropped = img[y : y + h, x : x + w]

    # Save cropped region to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        cv2.imwrite(str(tmp_path), cropped)

    try:
        # Extract using strategy
        text = _extract_with_strategy(tmp_path, strategy_name)
        return text
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


def extract_front_card_fields_with_optimal_strategies(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> FrontCardFields:
    """Extract front card fields using layout-aware extraction with optimal strategies per field.

    Uses CardLayoutExtractor to identify regions, then extracts each field
    with its optimal strategy from the benchmark results.

    Args:
        image_path: Path to front card image
        config: Optional pre-loaded optimal strategies config

    Returns:
        FrontCardFields model with extracted fields: name, location, motto, story
    """
    if cv2 is None or np is None:
        # Fallback to whole-card extraction
        return FrontCardFields(
            name="",
            location="",
            motto="",
            story=extract_front_card_with_optimal_strategy(image_path, config),
        )

    try:
        from scripts.core.parsing.layout import CardLayoutExtractor
    except ImportError:
        # Fallback if layout extractor not available
        return FrontCardFields(
            name="",
            location="",
            motto="",
            story=extract_front_card_with_optimal_strategy(image_path, config),
        )

    # Load optimal strategies config
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback to whole-card extraction
            return FrontCardFields(
                name="",
                location="",
                motto="",
                story=extract_front_card_with_optimal_strategy(image_path, config),
            )

    extractor = CardLayoutExtractor()

    try:
        # Get optimal strategies for each field
        strategies = _get_field_strategies(config)

        # Preprocess image for layout detection
        image = extractor.preprocess_image(image_path, invert_for_white_text=False)
        img_height, img_width = image.shape[:2]

        # Get region coordinates
        regions = _get_image_regions(img_height, img_width)

        # Extract text from each region
        name_text = extract_text_from_region_with_strategy(
            image_path, regions.name, strategies.name
        )
        location_text = extract_text_from_region_with_strategy(
            image_path, regions.location, strategies.location
        )
        motto_text = extract_text_from_region_with_strategy(
            image_path, regions.motto, strategies.motto
        )

        # Parse extracted text into fields
        name = _parse_name_from_text(name_text)
        location = _parse_location_from_text(location_text)
        motto = _parse_motto_from_text(motto_text)
        story = _extract_story_text(image_path, extractor, img_height, img_width, strategies.story)

        return FrontCardFields(
            name=name or None,
            location=location or None,
            motto=motto or None,
            story=story or None,
        )

    except Exception as e:
        # If layout-aware extraction fails, fall back to whole-card extraction
        print(f"Warning: Layout-aware extraction failed: {e}", file=sys.stderr)
        return FrontCardFields(
            name="",
            location="",
            motto="",
            story=extract_front_card_with_optimal_strategy(image_path, config),
        )


def update_optimal_strategies_from_benchmark(
    benchmark_file: Path, output_config: Optional[Path] = None
) -> Dict[str, Dict]:
    """Update optimal strategies config from benchmark results.

    Args:
        benchmark_file: Path to benchmark JSON file
        output_config: Optional output path (defaults to scripts/data/optimal_ocr_strategies.json)

    Returns:
        Updated config dictionary
    """
    from scripts.cli.parse.benchmark import find_best_strategies_per_category

    with open(benchmark_file, encoding="utf-8") as f:
        benchmark_data = json.load(f)

    best_strategies = find_best_strategies_per_category(benchmark_data["results"])

    # Build config structure
    config = {
        "version": "1.0.0",
        "last_updated": benchmark_data.get("timestamp", "").split("T")[0],
        "description": "Optimal OCR strategies per category, determined from benchmark results",
        "strategies": best_strategies,
        "front_card_strategy": {
            "strategy_name": best_strategies.get("story", {}).get("strategy_name", ""),
            "description": f"Best for story extraction ({best_strategies.get('story', {}).get('score', 0):.1f}%)",
            "reason": "Story is the most important and hardest to extract from front card",
        },
        "back_card_strategy": {
            "strategy_name": best_strategies.get("special_power", {}).get("strategy_name", ""),
            "description": f"Best for power extraction ({best_strategies.get('special_power', {}).get('score', 0):.1f}%)",
            "reason": "Special power extraction is the most important back card field",
        },
    }

    if output_config is None:
        output_config = project_root / "scripts" / "data" / "optimal_ocr_strategies.json"

    output_config.parent.mkdir(parents=True, exist_ok=True)
    with open(output_config, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return config
