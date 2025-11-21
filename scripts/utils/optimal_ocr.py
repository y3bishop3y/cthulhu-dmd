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
from typing import Any, Dict, Final, List, Optional, Tuple

from scripts.cli.parse.parsing_constants import (
    COMMON_POWER_CLOSE_MATCH_LENGTH_DIFF,
    COMMON_POWER_DESCRIPTION_KEYWORDS,
    COMMON_POWER_FUZZY_MATCH_THRESHOLD,
    COMMON_POWER_LINE_KEYWORDS,
    COMMON_POWER_MAX_LENGTH_DIFF,
    COMMON_POWER_MAX_LINE_LENGTH,
    COMMON_POWER_MAX_POWERS,
    COMMON_POWER_MAX_WORDS,
    COMMON_POWER_MULTIWORD_START_CHARS,
    COMMON_POWER_PARTIAL_FUZZY_THRESHOLD,
    COMMON_POWER_PARTIAL_LENGTH_DIFF_THRESHOLD,
    COMMON_POWER_PARTIAL_MATCH_THRESHOLD,
    COMMON_POWER_PREV_LINE_ENDINGS,
    COMMON_POWER_PREV_LINE_LENGTH_THRESHOLD,
    COMMON_POWER_REGIONS,
    COMMON_POWER_SINGLEWORD_START_CHARS,
    COMMON_POWER_WITHOUT_FUZZY_LENGTH_DIFF,
    FRONT_CARD_LOCATION_END_PERCENT,
    FRONT_CARD_MOTTO_END_PERCENT,
    FRONT_CARD_MOTTO_START_PERCENT,
    FRONT_CARD_STORY_HEIGHT_PERCENT,
    FRONT_CARD_STORY_START_PERCENT,
    FRONT_CARD_TOP_PERCENT,
    PUNCTUATION_CONTINUATION_CHARS,
    QUOTE_CHARACTERS,
    SPECIAL_POWER_LEVEL_WIDTHS,
    SPECIAL_POWER_REGION,
)
from scripts.cli.parse.parsing_models import FieldStrategies, FrontCardFields, ImageRegions
from scripts.models.character_constants import (
    LOCATION_MAX_LENGTH,
    NAME_MAX_LENGTH,
)

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
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

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
        config: Dict[str, Dict] = json.load(f)

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
        strategy_name: Optional[str] = strategy_info.get("strategy_name")
        return strategy_name

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
        location=get_optimal_strategy_for_category("location", config)
        or "tesseract_bilateral_psm3",
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
    top_height = int(img_height * FRONT_CARD_TOP_PERCENT)
    location_start = int(img_height * 0.32)  # 32% from top
    location_end = int(img_height * FRONT_CARD_LOCATION_END_PERCENT)  # Currently 30%, but should be > 35%
    # If end < start, use a default height (will be adjusted by user)
    if location_end <= location_start:
        location_height = int(img_height * 0.05)  # Default 5% height
    else:
        location_height = location_end - location_start
    motto_start = int(img_height * FRONT_CARD_MOTTO_START_PERCENT)
    motto_height = int(img_height * FRONT_CARD_MOTTO_END_PERCENT) - motto_start
    story_start = int(img_height * FRONT_CARD_STORY_START_PERCENT)
    story_height = int(img_height * FRONT_CARD_STORY_HEIGHT_PERCENT)

    name_start = int(img_height * 0.26)  # Name region starts at 26%
    name_height = int(img_height * 0.06)  # Name region height is 6%
    name_width = int(img_width * 0.45)  # Name region width is 45% (same as other regions)
    
    # All regions use 45% width starting at 5% X
    region_x_start = int(img_width * 0.05)  # Start at 5% from left
    region_width = int(img_width * 0.45)  # Width is 45%
    
    return ImageRegions(
        name=(region_x_start, name_start, name_width, name_height),
        location=(region_x_start, location_start, region_width, location_height),
        motto=(region_x_start, motto_start, region_width, motto_height),
        story=(region_x_start, story_start, region_width, story_height),
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
        line_stripped = line.strip()
        # Skip empty lines
        if not line_stripped:
            continue
        # Skip all-caps lines longer than threshold (likely name/location that leaked in)
        # BUT allow all-caps lines if they're in quotes (could be a motto like "HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAW!")
        # Check for both straight and curly quotes
        is_quoted = any(quote_char in line_stripped for quote_char in QUOTE_CHARACTERS)
        if line_stripped.isupper() and len(line_stripped) > MOTTO_MAX_ALL_CAPS_LENGTH and not is_quoted:
            continue
        # Skip very short lines (but allow 2-char lines if they're part of a phrase)
        if len(line_stripped) < MOTTO_MIN_LINE_LENGTH:
            continue
        # Skip lines that are mostly symbols/numbers (less than threshold alphanumeric)
        alnum_ratio = (
            sum(c.isalnum() for c in line_stripped) / len(line_stripped) if line_stripped else 0
        )
        if alnum_ratio < MOTTO_MIN_ALNUM_RATIO:
            continue
        # Skip lines that look like OCR garbage (too many special chars)
        special_char_count = sum(
            1 for c in line_stripped if not c.isalnum() and c not in " .,!?\"'-"
        )
        if special_char_count > len(line_stripped) * 0.3:  # More than 30% special chars
            continue
        filtered.append(line_stripped)
    return filtered


def _extract_quoted_motto(filtered_lines: List[str]) -> str:
    """Extract motto from lines containing quotes.

    Args:
        filtered_lines: Filtered motto lines

    Returns:
        Extracted motto or empty string
    """
    # Pattern to match both straight and curly quotes
    quote_patterns = [
        r'["\']([^"\']+)["\']',  # Straight quotes
        r'[\u201c\u201d]([^\u201c\u201d]+)[\u201c\u201d]',  # Curly double quotes
        r'[\u2018\u2019]([^\u2018\u2019]+)[\u2018\u2019]',  # Curly single quotes
    ]

    for line in filtered_lines:
        # Check if line has any type of quotes
        has_quotes = any(quote_char in line for quote_char in QUOTE_CHARACTERS)

        if has_quotes:
            # Try each quote pattern
            for pattern in quote_patterns:
                quoted_match = re.search(pattern, line)
                if quoted_match:
                    motto = quoted_match.group(1).strip()
                    # For quoted mottos, be more lenient:
                    # - Allow single-word mottos (like "HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAW!")
                    # - Allow all-caps mottos if they're in quotes
                    # - Allow longer mottos if they're in quotes (up to reasonable limit)
                    if (
                        len(motto) >= MOTTO_MIN_LINE_LENGTH  # At least 2 chars
                        and len(motto) <= MOTTO_MAX_CHARS_QUOTED * 2  # Allow up to 300 chars for quoted
                    ):
                        return motto

            # If no clean quote match, check if entire line is reasonable
            word_count = len(line.split())
            if (
                MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_QUOTED
                and len(line) < MOTTO_MAX_CHARS_QUOTED
            ):
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
        if (line1.isupper() and len(line1) > MOTTO_MIN_WORDS_COMBINED) or (
            line2.isupper() and len(line2) > MOTTO_MIN_WORDS_COMBINED
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
            if '"' in combined or combined.endswith((".", "!", "?", '."', '!"', '?"')):
                return combined
            # Or if both lines together form a reasonable phrase
            elif word_count >= MOTTO_MIN_WORDS_PHRASE:
                # Prefer if it has quotes or looks complete
                if '"' in combined or any(p in combined for p in [".", "!", "?"]):
                    return combined
    return ""


def _extract_single_line_motto(filtered_lines: List[str]) -> str:
    """Extract motto from single lines (last resort).

    Args:
        filtered_lines: Filtered motto lines

    Returns:
        Extracted motto or empty string
    """
    # Prefer lines with quotes or punctuation
    quoted_lines = [line for line in filtered_lines if '"' in line or "'" in line]
    if quoted_lines:
        for line in quoted_lines:
            word_count = len(line.split())
            if (
                MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_SINGLE
                and len(line) < MOTTO_MAX_CHARS_SINGLE
            ):
                return line

    # Then try lines ending with punctuation
    punctuated_lines = [
        line for line in filtered_lines if line.endswith((".", "!", "?", ".", "!", "?"))
    ]
    if punctuated_lines:
        for line in punctuated_lines:
            # Skip all-caps (likely name/location)
            if line.isupper() and len(line) > MOTTO_MAX_ALL_CAPS_LENGTH:
                continue
            word_count = len(line.split())
            if (
                MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_SINGLE
                and len(line) < MOTTO_MAX_CHARS_SINGLE
            ):
                return line

    # Last resort: any reasonable line
    for line in filtered_lines:
        # Skip all-caps (likely name/location) unless very short
        if line.isupper() and len(line) > MOTTO_MAX_ALL_CAPS_LENGTH:
            continue
        word_count = len(line.split())
        if (
            MOTTO_MIN_WORDS <= word_count <= MOTTO_MAX_WORDS_SINGLE
            and len(line) < MOTTO_MAX_CHARS_SINGLE
        ):
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
    motto = re.sub(r"^[-|~_\s]+", "", motto)
    motto = re.sub(r"[-|~_\s]+$", "", motto)
    # Remove pipes and other separators in the middle
    motto = re.sub(r"\s*[|~_]\s*", " ", motto)
    # Remove leading prefixes like "- |" or "id —~—~~ ie 4" before quotes
    motto = re.sub(r'^[-|\s~_id0-9]+\s*["\']', '"', motto)
    # Remove leading garbage before quotes (more aggressive)
    if '"' in motto or "'" in motto:
        quote_char = '"' if '"' in motto else "'"
        quote_start = motto.find(quote_char)
        if quote_start > 0 and quote_start < MOTTO_MAX_GARBAGE_BEFORE_QUOTE:
            motto = motto[quote_start:]
    # Fix common OCR errors in mottos
    motto = motto.replace("qT.", "is")
    motto = motto.replace("wriften", "written")
    motto = motto.replace("writen", "written")
    motto = motto.replace("writtn", "written")
    # Fix "4" -> "I" (common OCR error, can appear at start or middle)
    # Handle both straight and curly quotes, and both quoted and unquoted cases
    motto = motto.replace('"4 ', '"I ').replace("'4 ", "'I ")
    # Handle curly quotes (Unicode U+201C and U+201D)
    motto = motto.replace("\u201c4 ", "\u201cI ")  # Left double quotation mark
    motto = motto.replace("\u201d4 ", "\u201dI ")  # Right double quotation mark
    motto = re.sub(r"\s+4\s+", r" I ", motto)  # In middle of text
    motto = re.sub(r"^4\s+", r"I ", motto)  # At very start (no quote)
    # Fix "|" -> "I" (common OCR error)
    motto = motto.replace(" | ", " I ")
    motto = motto.replace("| ", "I ")
    # Fix "Instead." -> "Instead," (common OCR error where comma is read as period)
    motto = re.sub(r"\bInstead\.\s+", r"Instead, ", motto)
    # Fix missing "I" before "make" (common OCR error: "Instead, make" -> "Instead, I make")
    motto = re.sub(r"\bInstead,?\s+make\b", r"Instead, I make", motto, flags=re.IGNORECASE)
    # Fix duplicate words (common OCR error: "is is" -> "is")
    motto = re.sub(r"\b(\w+)\s+\1\b", r"\1", motto)
    # Clean up multiple spaces
    motto = re.sub(r"\s+", " ", motto).strip()
    # Remove trailing incomplete words (common OCR error at end)
    motto = re.sub(r"\s+\w{1,2}$", "", motto)

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
        story_start = int(img_height * FRONT_CARD_STORY_START_PERCENT)
        story_height = int(img_height * FRONT_CARD_STORY_HEIGHT_PERCENT)
        bottom_region = (0, story_start, img_width, story_height)
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

    # Convert to PNG if lossy format (improves OCR accuracy)
    # PNG files are saved alongside originals for reuse (not auto-deleted)
    # They're gitignored so won't be committed
    optimized_path = image_path
    try:
        from scripts.utils.image_conversion import get_ocr_optimized_path

        optimized_path = get_ocr_optimized_path(image_path, use_temp=False)
    except ImportError:
        # Fallback if conversion utility not available
        pass

    # Load image
    img = cv2.imread(str(optimized_path))
    if img is None:
        raise ValueError(f"Could not read image: {optimized_path}")

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
        # Clean up temp file (cropped region)
        if tmp_path.exists():
            tmp_path.unlink()
        # Note: optimized_path PNG files are kept for reuse (not deleted)


def _is_line_likely_description(line: str) -> bool:
    """Check if a line looks like a description rather than a power header.

    Args:
        line: Line to check

    Returns:
        True if line looks like a description, False otherwise
    """
    line_stripped = line.strip()
    line_len = len(line_stripped)
    line_upper = line_stripped.upper()

    # Skip very long lines (likely descriptions)
    if line_len > COMMON_POWER_MAX_LINE_LENGTH:
        return True

    # Skip lines that look like descriptions (contain common description words)
    if any(keyword in line_upper for keyword in COMMON_POWER_DESCRIPTION_KEYWORDS):
        return True

    # Skip lines that contain multiple words (power names are usually 1-2 words)
    word_count = len(line_stripped.split())
    if word_count > COMMON_POWER_MAX_WORDS:
        return True

    # Skip lines that start with lowercase (likely continuation of description)
    if line_stripped and line_stripped[0].islower():
        return True

    # Skip lines that start with punctuation (likely continuation of previous line)
    if line_stripped:
        first_char = line_stripped[0]
        if first_char in PUNCTUATION_CONTINUATION_CHARS:
            return True
        # Also skip if second character is punctuation
        if len(line_stripped) > 1 and line_stripped[1] in PUNCTUATION_CONTINUATION_CHARS:
            return True

    return False


def _reject_partial_match(line: str, power_name: str, rapidfuzz_fuzz: Optional[Any]) -> bool:
    """Check if a power match should be rejected as a partial match.

    Args:
        line: Line that matched the power name
        power_name: Detected power name
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        True if match should be rejected, False otherwise
    """
    line_len = len(line)
    line_upper = line.upper()
    power_upper = power_name.upper()

    # Skip if line is much longer than power name (likely has extra text)
    if line_len > len(power_name) + COMMON_POWER_MAX_LENGTH_DIFF:
        return True

    # For multi-word powers, check if line contains the second word first
    # (e.g., "| MASTERY" for "ARCANE MASTERY" - missing first word but has second)
    # This allows us to accept partial matches that have the second word even if length differs
    if rapidfuzz_fuzz and " " in power_name:
        power_words = power_upper.split()
        if len(power_words) > 1:
            second_word = power_words[1]
            second_word_start = second_word[:COMMON_POWER_MULTIWORD_START_CHARS]
            # If line contains the second word (even if first word is missing), accept it
            if second_word_start in line_upper or second_word in line_upper:
                return False  # Accept this match - has second word

    # Reject partial matches where the power name is much longer than the line
    # (but only if we didn't already accept it above for having the second word)
    if len(power_name) > line_len + COMMON_POWER_PARTIAL_MATCH_THRESHOLD:
        return True

    # Reject if line appears to be missing the beginning of the power name
    if rapidfuzz_fuzz:
        if " " in power_name:
            # Multi-word power name: check if line starts with first word
            power_words = power_upper.split()
            line_words = line_upper.split()
            if line_words and power_words:
                power_start = power_words[0][:COMMON_POWER_MULTIWORD_START_CHARS]
                if not line_words[0].startswith(power_start) and power_start not in line_upper:
                    return True
        else:
            # Single-word power name: check if line is missing significant beginning
            if len(line_upper) < len(power_upper) - 1:  # Line is at least 2 chars shorter
                power_start = power_upper[:COMMON_POWER_SINGLEWORD_START_CHARS]
                if power_start not in line_upper:
                    # Additional check: verify with fuzzy ratio and length difference
                    ratio = rapidfuzz_fuzz.ratio(line_upper, power_upper)
                    length_diff = len(power_upper) - len(line_upper)
                    if (
                        ratio < COMMON_POWER_PARTIAL_FUZZY_THRESHOLD
                        and length_diff >= COMMON_POWER_PARTIAL_LENGTH_DIFF_THRESHOLD
                    ):
                        return True

    return False


def _validate_power_match_quality(
    line: str, power_name: str, rapidfuzz_fuzz: Optional[Any]
) -> bool:
    """Validate if a detected power match is of good quality.

    Args:
        line: Line that matched the power name
        power_name: Detected power name
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        True if match is good quality, False otherwise
    """
    line_len = len(line)
    line_upper = line.upper()
    power_upper = power_name.upper()

    # Exact match - always accept
    if power_upper == line_upper:
        return True

    # Close match - verify with fuzzy matching if available
    if line_len <= len(power_name) + COMMON_POWER_CLOSE_MATCH_LENGTH_DIFF:
        if rapidfuzz_fuzz:
            ratio = rapidfuzz_fuzz.ratio(line_upper, power_upper)
            # Use standard threshold (75%) for strict matching
            if ratio >= COMMON_POWER_FUZZY_MATCH_THRESHOLD:
                return True
            # But if power was already detected by _detect_common_power, be more lenient
            # Accept matches with >= 60% similarity if length is close (OCR errors)
            if ratio >= 60.0 and abs(line_len - len(power_name)) <= COMMON_POWER_CLOSE_MATCH_LENGTH_DIFF:
                return True
        else:
            # Without fuzzy matching, accept if lengths are very close
            if abs(line_len - len(power_name)) <= COMMON_POWER_WITHOUT_FUZZY_LENGTH_DIFF:
                return True

    return False


def _check_line_has_description_keywords(line: str) -> bool:
    """Check if line contains description keywords.

    Args:
        line: Line to check

    Returns:
        True if line contains description keywords, False otherwise
    """
    line_upper = line.upper()
    return any(kw in line_upper for kw in COMMON_POWER_LINE_KEYWORDS)


def _check_previous_line_suggests_description(
    prev_line: str, lines: List[str], current_index: int
) -> bool:
    """Check if previous line suggests current line is part of a description.

    Args:
        prev_line: Previous line text
        lines: All lines
        current_index: Current line index

    Returns:
        True if previous line suggests description, False otherwise
    """
    if not prev_line or len(prev_line) <= COMMON_POWER_PREV_LINE_LENGTH_THRESHOLD:
        return False

    prev_line_upper = prev_line.upper()
    # If previous line is very long AND ends with description keywords, current line might be continuation
    return any(prev_line_upper.endswith(kw) for kw in COMMON_POWER_PREV_LINE_ENDINGS)


def _extract_common_powers_from_region(
    image_path: Path, region: Tuple[int, int, int, int], strategy_name: str
) -> List[str]:
    """Extract common power names from a specific region on the back card.

    Uses active search against all known common power names with fuzzy matching
    to improve detection of OCR errors.

    Args:
        image_path: Path to back card image
        region: (x, y, width, height) bounding box for common powers region
        strategy_name: OCR strategy to use

    Returns:
        List of common power names found in the region
    """
    # Extract text from region
    region_text = extract_text_from_region_with_strategy(image_path, region, strategy_name)
    if not region_text:
        return []

    # Split into lines and match common power names
    lines = [line.strip() for line in region_text.split("\n") if line.strip()]
    found_powers: List[str] = []

    # Import the detection function from character.py
    from scripts.models.character import BackCardData
    from scripts.models.constants import get_common_power_names

    # Get all known common power names
    all_common_powers = get_common_power_names()

    # Import fuzzy matching if available
    try:
        from rapidfuzz import fuzz as rapidfuzz_fuzz
    except ImportError:
        rapidfuzz_fuzz = None

    # Filter lines to only consider short lines that look like power headers
    # Also check individual words in longer lines (OCR might extract power name with garbage)
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        line_upper = line_stripped.upper()
        
        # If line is SHORT (<=15 chars) and contains multiple words, try extracting just the power name part
        # This handles cases like "ps sss" where "sss" is part of "Swiftness"
        # But DON'T do this for long description lines (too many false positives from common words)
        words = line_stripped.split()
        power_candidate_line = None
        if len(words) > 1 and len(line_stripped) <= 15:  # SHORT line with multiple words/characters
            # First check if the full line matches (prefer exact matches)
            full_line_power = BackCardData._detect_common_power(line_stripped)
            if not full_line_power:
                # Try to find a word or word combination that matches a power name
                # Prefer longer words (more likely to be power names)
                words_by_length = sorted(words, key=lambda w: len(w.rstrip(';:.,!?|~-_').strip()), reverse=True)
                for word in words_by_length:
                    word_clean = word.rstrip(';:.,!?|~-_').strip()
                    if len(word_clean) >= 3:  # At least 3 chars (reject 2-char words entirely)
                        detected = BackCardData._detect_common_power(word_clean)
                        if detected:
                            # Found a power name in this word, use just this word
                            power_candidate_line = word_clean
                            break
                # If no single word matched, try 2-word combinations (for "Arcane Mastery" etc)
                if not power_candidate_line and len(words) >= 2:
                    for j in range(len(words) - 1):
                        two_words = f"{words[j]} {words[j+1]}"
                        two_words_clean = two_words.rstrip(';:.,!?|~-_').strip()
                        detected = BackCardData._detect_common_power(two_words_clean)
                        if detected:
                            power_candidate_line = two_words_clean
                            break
        
        # Use the extracted power candidate if found, otherwise use full line
        if power_candidate_line:
            line_stripped = power_candidate_line
            line_upper = line_stripped.upper()

        # First try the detection function (handles exact matches and common patterns)
        power_name = BackCardData._detect_common_power(line_stripped)

        # If not detected, actively search all known power names using fuzzy matching
        # This helps catch OCR errors like "sea:" -> "Stealth" or "i steetsess" -> "Swiftness"
        if not power_name and rapidfuzz_fuzz:
            best_match = None
            best_score = 0.0
            best_partial_score = 0.0  # Track partial ratio separately
            best_power = None

            # Clean the line for better matching
            line_clean = line_stripped.rstrip(';:.,!?|~-_').strip()
            
            # Determine threshold based on line length
            # Very short lines (3-5 chars) might be OCR errors, so be more lenient
            is_very_short = len(line_clean) <= 5
            is_short = len(line_clean) <= 10
            is_long = len(line_clean) > 30
            
            for known_power in all_common_powers:
                # Try exact match first
                if known_power.upper() == line_clean.upper():
                    best_match = known_power
                    best_score = 100.0
                    best_partial_score = 100.0
                    break
                
                # Try fuzzy matching
                ratio = rapidfuzz_fuzz.ratio(line_clean.upper(), known_power.upper())
                partial_ratio = rapidfuzz_fuzz.partial_ratio(line_clean.upper(), known_power.upper())
                
                # Use the better of the two ratios
                score = max(ratio, partial_ratio)
                
                # Adjust threshold based on line length
                if is_very_short:
                    # Very short lines: 60% threshold, but allow 75%+ partial matches even if short
                    threshold = 60.0
                    max_length_multiplier = 2.0  # Allow up to 2x the power name length
                elif is_short:
                    # Short lines: 65% threshold
                    threshold = 65.0
                    max_length_multiplier = 1.8
                elif is_long:
                    # Long lines: 75% threshold and must be close to power name length
                    threshold = 75.0
                    max_length_multiplier = 1.3
                else:
                    # Medium lines: 70% threshold
                    threshold = 70.0
                    max_length_multiplier = 1.5
                
                # Check if score meets threshold and length is reasonable
                # For very short lines with high partial match (>=75%), be more lenient
                if score > best_score and (
                    score >= threshold or 
                    (is_very_short and partial_ratio >= 75.0)  # High partial match for short lines
                ):
                    # Additional validation: reject if line is too long (likely description)
                    if len(line_clean) <= len(known_power) * max_length_multiplier:
                        best_score = score
                        best_partial_score = partial_ratio
                        best_match = known_power
            
            # Accept the best match if it's good enough
            # Require stronger matches to reduce false positives
            if best_match:
                if is_very_short:
                    # Very short lines: require at least 65% OR 75%+ partial match
                    if best_score >= 65.0 or best_partial_score >= 75.0:
                        power_name = best_match
                elif is_short:
                    # Short lines: require at least 70% (was 65%)
                    if best_score >= 70.0:
                        power_name = best_match
                else:
                    # Medium/long lines: require at least 75% (was 70%)
                    if best_score >= 75.0:
                        power_name = best_match

        # If it's detected as a power, skip description check (OCR errors might cause false positives)
        # But still reject if line is too long (likely description text with accidental match)
        if not power_name:
            # Skip lines that look like descriptions (only if not detected as power)
            if _is_line_likely_description(line_stripped):
                continue
        else:
            # Even if detected as power, reject if line is too long (likely description with false positive)
            # Power headers are typically short (<=20 chars)
            if len(line_stripped) > 20:
                # Long line detected as power - likely false positive from description text
                # Exception: allow if it's a multi-word power name like "Arcane Mastery"
                if power_name not in ["Arcane Mastery"]:  # Known multi-word powers
                    continue

        if power_name and power_name not in found_powers:
            # Track if this power was found via fuzzy matching (more lenient validation)
            # Also check if it has a high partial match score (even if detected by function)
            found_via_fuzzy = False
            has_high_partial_match = False
            if rapidfuzz_fuzz:
                # Check if this was found via our active fuzzy search (not the detection function)
                line_clean = line_stripped.rstrip(';:.,!?|~-_').strip()
                ratio = rapidfuzz_fuzz.ratio(line_clean.upper(), power_name.upper())
                partial = rapidfuzz_fuzz.partial_ratio(line_clean.upper(), power_name.upper())
                score = max(ratio, partial)
                # If fuzzy match score is high enough, it was likely found via fuzzy search
                found_via_fuzzy = score >= 60.0 and power_name.upper() != line_clean.upper()
                # Also check if partial match is high (>=75%) - indicates good match despite OCR errors
                has_high_partial_match = partial >= 75.0

            # Reject very short lines that are likely OCR garbage (unless exact match or fuzzy match)
            # e.g., "Ye" matching "Arcane Mastery" or "AAN" matching "Marksman"
            # Reject 2-character lines entirely unless exact match (too many false positives)
            if len(line_stripped) == 2 and power_name.upper() != line_stripped.upper():
                # 2-character lines are almost always false positives
                continue
            elif len(line_stripped) < 4 and power_name.upper() != line_stripped.upper() and not found_via_fuzzy:
                # Very short line that's not an exact match - likely OCR garbage
                continue

            # Reject lines that are too short compared to power name (missing too much)
            # But be lenient for OCR errors - allow if at least 50% of power name length
            # Also allow very short lines (3-4 chars) if they're detected as power names
            # (e.g., "sea:" for "Stealth" - OCR might extract just part of the word)
            min_length_threshold = len(power_name) * 0.5  # Reduced from 0.6 to 0.5
            if len(line_stripped) < min_length_threshold:
                # Exception: Allow very short lines if found via fuzzy matching OR has high partial match
                if found_via_fuzzy or has_high_partial_match:
                    # Check if partial match was high (>=75%) - indicates good match despite short length
                    if rapidfuzz_fuzz:
                        partial = rapidfuzz_fuzz.partial_ratio(line_stripped.upper(), power_name.upper())
                        if partial >= 75.0:
                            # High partial match, trust it even if short (e.g., "sss" -> "Swiftness")
                            pass
                        elif len(line_stripped) >= 3:
                            # Lower partial match but at least 3 chars, allow it
                            pass
                        else:
                            continue
                    elif len(line_stripped) >= 3:
                        # Fuzzy match found it, trust it even if short
                        pass
                    else:
                        continue
                elif len(line_stripped) >= 3:
                    # Check if removing punctuation makes it match better
                    line_no_punct = line_stripped.rstrip(';:.,!?|~-_').strip()
                    if line_no_punct and BackCardData._detect_common_power(line_no_punct) == power_name:
                        # If removing punctuation still matches, allow it (OCR error with punctuation)
                        line_stripped = line_no_punct
                    elif len(line_stripped) >= 3:
                        # Very short line (3-4 chars) that's detected as a power - likely OCR partial extraction
                        # Allow it if fuzzy matching confirms it's close
                        if rapidfuzz_fuzz:
                            ratio = rapidfuzz_fuzz.ratio(line_stripped.upper(), power_name.upper())
                            if ratio >= 60.0:  # At least 60% similarity
                                pass  # Allow it
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                else:
                    continue

            # Reject partial matches, but be more lenient for detected power names
            # (OCR errors like ";CANE MASTERY" for "ARCANE MASTERY" should be allowed)
            # Skip this check if found via fuzzy matching (we already validated it)
            if not found_via_fuzzy and _reject_partial_match(line_stripped, power_name, rapidfuzz_fuzz):
                # If the line was detected as a power name, be more lenient
                # Check if removing leading punctuation makes it a better match
                line_no_punct = line_stripped.lstrip(';:.,!?|~-_').strip()
                if line_no_punct and BackCardData._detect_common_power(line_no_punct) == power_name:
                    # If removing punctuation still matches, use the cleaned version
                    line_stripped = line_no_punct
                else:
                    continue

            # Validate match quality - skip if found via fuzzy matching (already validated)
            if found_via_fuzzy:
                is_good_match = True  # Trust fuzzy match
            else:
                is_good_match = _validate_power_match_quality(line_stripped, power_name, rapidfuzz_fuzz)

            # Additional validation for non-exact matches
            if is_good_match and power_name.upper() != line_upper:
                # Check if line contains description keywords
                if _check_line_has_description_keywords(line_stripped):
                    is_good_match = False

                # Check if previous line suggests this is part of a description
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    if _check_previous_line_suggests_description(prev_line, lines, i):
                        is_good_match = False

            if is_good_match:
                found_powers.append(power_name)
                # Limit to 2 common powers (characters always have exactly 2)
                if len(found_powers) >= 2:
                    break

    return found_powers


def extract_common_powers_from_back_card(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> List[str]:
    """Extract common powers from back card using region-specific extraction.

    Common powers appear in a consistent region on the back card (typically
    right side or middle-right section). This function extracts text from that
    region and matches common power names.

    Args:
        image_path: Path to back card image
        config: Optional pre-loaded optimal strategies config

    Returns:
        List of common power names found
    """
    if cv2 is None or np is None:
        # Fallback: extract from whole card and parse
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return [cp.name for cp in back_data.common_powers]

    try:
        from scripts.core.parsing.layout import CardLayoutExtractor
    except ImportError:
        # Fallback
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return [cp.name for cp in back_data.common_powers]

    # Load optimal strategies config
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback
            back_text = extract_back_card_with_optimal_strategy(image_path, config)
            from scripts.models.character import BackCardData

            back_data = BackCardData.parse_from_text(back_text)
            return [cp.name for cp in back_data.common_powers]

    extractor = CardLayoutExtractor()

    try:
        # Preprocess image to get dimensions
        image = extractor.preprocess_image(image_path, invert_for_white_text=False)
        img_height, img_width = image.shape[:2]

        # Convert region percentages to pixel coordinates
        regions_to_try = [
            (
                int(img_width * x_percent),
                int(img_height * y_percent),
                int(img_width * width_percent),
                int(img_height * height_percent),
            )
            for x_percent, y_percent, width_percent, height_percent in COMMON_POWER_REGIONS
        ]

        # Try multiple OCR strategies for common powers
        # Some strategies work better for different power names (e.g., psm6/psm11 for "Brawling")
        strategies_to_try = [
            get_optimal_strategy_for_category("special_power", config) or "tesseract_bilateral_psm3",
            "tesseract_psm6",  # Better for single words like "Brawling"
            "tesseract_psm11",  # Alternative for single words
        ]
        # Remove duplicates while preserving order
        seen = set()
        strategies_to_try = [s for s in strategies_to_try if s not in seen and not seen.add(s)]

        # Try each region with each strategy and collect powers
        # Strategy: For each region, try strategies in order and use the first that finds powers
        # If a region finds exactly 2 powers with any strategy, use that immediately
        # Otherwise, collect one power from each region (Region 1 = first power, Region 2 = second power)
        found_powers: List[str] = []
        region_powers: List[List[str]] = []  # Powers found in each region
        
        for region in regions_to_try:
            # Try each strategy for this region until we find at least one power
            region_powers_this_region: List[str] = []
            for power_strategy in strategies_to_try:
                try:
                    region_powers_found = _extract_common_powers_from_region(image_path, region, power_strategy)
                    # If this strategy found exactly 2 powers, use it immediately (perfect match)
                    if len(region_powers_found) == 2:
                        return region_powers_found[:COMMON_POWER_MAX_POWERS]
                    
                    # Collect unique powers from this region
                    for power in region_powers_found:
                        if power not in region_powers_this_region:
                            region_powers_this_region.append(power)
                    
                    # If we found at least one power with this strategy, prefer it
                    # (don't try other strategies for this region to avoid false positives)
                    if region_powers_this_region:
                        break
                except Exception:
                    # If a strategy fails, continue with next strategy
                    continue
            
            # Store powers found in this region
            region_powers.append(region_powers_this_region)
        
        # Now combine results: prefer one power from each region
        # Region 1 should have the first power, Region 2 should have the second power
        if len(region_powers) >= 2:
            # Take first power from Region 1, first power from Region 2
            if region_powers[0]:
                found_powers.append(region_powers[0][0])
            if region_powers[1] and len(found_powers) < COMMON_POWER_MAX_POWERS:
                # Make sure we don't add a duplicate
                if region_powers[1][0] not in found_powers:
                    found_powers.append(region_powers[1][0])
        elif region_powers and region_powers[0]:
            # Only one region defined, take up to 2 powers from it
            found_powers = region_powers[0][:COMMON_POWER_MAX_POWERS]
        
        return found_powers

    except Exception as e:
        # If region extraction fails, fall back to whole-card extraction
        print(f"Warning: Region-specific common power extraction failed: {e}", file=sys.stderr)
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return [cp.name for cp in back_data.common_powers]


def extract_special_power_from_back_card(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> Optional["Power"]:
    """Extract special power from back card using region-specific extraction.

    Special powers appear in a consistent region on the back card (typically
    top-right section). This function extracts text from that region and parses
    the power name and all 4 levels.

    Args:
        image_path: Path to back card image
        config: Optional pre-loaded optimal strategies config

    Returns:
        Power object with name and levels, or None if not found
    """
    if cv2 is None or np is None:
        # Fallback: extract from whole card and parse
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return back_data.special_power

    try:
        from scripts.core.parsing.layout import CardLayoutExtractor
    except ImportError:
        # Fallback
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return back_data.special_power

    # Load optimal strategies config
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback
            back_text = extract_back_card_with_optimal_strategy(image_path, config)
            from scripts.models.character import BackCardData

            back_data = BackCardData.parse_from_text(back_text)
            return back_data.special_power

    extractor = CardLayoutExtractor()

    try:
        # Preprocess image to get dimensions
        image = extractor.preprocess_image(image_path, invert_for_white_text=False)
        img_height, img_width = image.shape[:2]

        # Convert region percentages to pixel coordinates
        sp_x_pct, sp_y_pct, sp_width_pct, sp_height_pct = SPECIAL_POWER_REGION
        sp_x = int(img_width * sp_x_pct)
        sp_y = int(img_height * sp_y_pct)
        sp_width = int(img_width * sp_width_pct)
        sp_height = int(img_height * sp_height_pct)
        region = (sp_x, sp_y, sp_width, sp_height)

        # Use special_power strategy
        power_strategy = get_optimal_strategy_for_category("special_power", config)
        if not power_strategy:
            power_strategy = "tesseract_bilateral_psm3"

        # Extract power name from the entire special power region first
        # (power name might span across level boundaries)
        region_text = extract_text_from_region_with_strategy(image_path, region, power_strategy)
        if not region_text:
            return None

        # Extract power name from the full region text
        from scripts.models.character import BackCardData, Power, PowerLevel
        import re
        from scripts.core.parsing.text import clean_ocr_text

        cleaned_text = clean_ocr_text(region_text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        power_name = None
        for line in lines[:10]:  # Check first 10 lines for power name
            # Skip single digits/numbers (level indicators)
            if line.isdigit() and len(line) == 1:
                continue
            # Look for all-caps line (power name)
            if line.isupper() and len(line) > 3 and not any(char.isdigit() for char in line):
                power_name = line
                break

        # If no all-caps line found, try to extract from first substantial line
        if not power_name:
            for line in lines[:10]:
                if len(line) > 3 and not line.isdigit():
                    words = line.split()
                    if len(words) >= 2 and words[0][0].isupper():
                        power_name = line
                        break

        if not power_name:
            return None

        # Create Power object
        power = Power(name=power_name, is_special=True, levels=[])

        # Extract text from each of the 4 level regions
        current_x_pct = sp_x_pct
        for level_idx in range(4):
            level_width_pct = sp_width_pct * SPECIAL_POWER_LEVEL_WIDTHS[level_idx]
            level_region = (
                int(img_width * current_x_pct),
                int(img_height * sp_y_pct),
                int(img_width * level_width_pct),
                int(img_height * sp_height_pct),
            )
            
            level_text = extract_text_from_region_with_strategy(image_path, level_region, power_strategy)
            if level_text:
                # Clean the text
                cleaned_level_text = clean_ocr_text(level_text, preserve_newlines=False)
                cleaned_level_text = cleaned_level_text.strip()
                
                # Remove power name if it appears in the level text (handle partial matches)
                power_name_upper = power_name.upper()
                cleaned_level_text_upper = cleaned_level_text.upper()
                
                # Remove full power name
                cleaned_level_text = re.sub(rf"\b{re.escape(power_name)}\b", "", cleaned_level_text, flags=re.I)
                
                # Remove partial power name matches (e.g., "GATE MANIPUI" or "ATION")
                # Split power name into words and remove each word if it appears alone
                power_words = power_name.split()
                for word in power_words:
                    if len(word) > 3:  # Only remove substantial words
                        # Remove word if it appears as a standalone word
                        cleaned_level_text = re.sub(rf"\b{re.escape(word)}\b", "", cleaned_level_text, flags=re.I)
                
                # Remove partial matches at the start (e.g., "MANIPUI" for "MANIPULATION", "ATION" for "MANIPULATION")
                # Check if text starts with a partial match of power name words
                cleaned_words = cleaned_level_text.split()
                if cleaned_words:
                    first_word = cleaned_words[0].upper()
                    # Check if first word is a partial match of any power name word
                    for word in power_words:
                        word_upper = word.upper()
                        # If first word starts with or is contained in a power name word (or vice versa)
                        # Also check if first word starts with same letters as power name word (for OCR errors)
                        if (
                            (first_word in word_upper or word_upper in first_word) 
                            or (len(first_word) >= 4 and len(word_upper) >= 4 and first_word[:4] == word_upper[:4])
                        ) and len(first_word) >= 3:
                            cleaned_words = cleaned_words[1:]  # Remove first word
                            cleaned_level_text = " ".join(cleaned_words)
                            break
                    
                    # Also check if first word looks like OCR error of power name (e.g., "MANIPUI" for "MANIPULATION")
                    # Check if first 4-5 characters match any power name word
                    if cleaned_words and len(first_word) >= 4:
                        for word in power_words:
                            word_upper = word.upper()
                            if len(word_upper) >= 6 and first_word[:4] == word_upper[:4]:
                                # Likely OCR error, remove it
                                cleaned_words = cleaned_words[1:]
                                cleaned_level_text = " ".join(cleaned_words)
                                break
                
                # Remove leading digits and clean up
                cleaned_level_text = re.sub(r"^\d+\s*", "", cleaned_level_text)  # Remove leading digits
                cleaned_level_text = re.sub(r"\s+", " ", cleaned_level_text)  # Normalize whitespace
                cleaned_level_text = cleaned_level_text.strip()
                
                # Only add if it has substantial content (at least 3 words) and doesn't look like just OCR garbage
                if cleaned_level_text and len(cleaned_level_text.split()) >= 3:
                    # Check if it's mostly letters (not just symbols/garbage)
                    letter_count = sum(1 for c in cleaned_level_text if c.isalpha())
                    if letter_count >= len(cleaned_level_text) * 0.3:  # At least 30% letters
                        level_num = level_idx + 1
                        power.add_level_from_text(level_num, cleaned_level_text)
            
            # Move to next level's X position
            current_x_pct += level_width_pct

        return power if power.levels else None

    except Exception as e:
        # If region extraction fails, fall back to whole-card extraction
        print(f"Warning: Region-specific special power extraction failed: {e}", file=sys.stderr)
        back_text = extract_back_card_with_optimal_strategy(image_path, config)
        from scripts.models.character import BackCardData

        back_data = BackCardData.parse_from_text(back_text)
        return back_data.special_power


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

        # Fallback: If name/location not found in their regions, try extracting from motto region
        # (some cards have name/location in the motto region area)
        if not name or not location:
            motto_lines = [line.strip() for line in motto_text.split("\n") if line.strip()]
            # Look for all-caps lines that might be name/location
            for line in motto_lines:
                line_stripped = line.strip()
                # Skip if it's the motto (has quotes)
                if (
                    '"' in line_stripped
                    or "'" in line_stripped
                    or "\u201c" in line_stripped
                    or "\u201d" in line_stripped
                ):
                    continue
                # Skip decorative lines
                if line_stripped in ["~~", "—", "-", "~", "—~"]:
                    continue
                # Check if it looks like a name (all caps, reasonable length, no comma)
                if (
                    line_stripped.isupper()
                    and len(line_stripped) >= 3
                    and len(line_stripped) <= NAME_MAX_LENGTH
                    and "," not in line_stripped
                    and not name
                ):
                    name = line_stripped
                # Check if it looks like a location (all caps, has comma or is "UNKNOWN")
                elif (
                    line_stripped.isupper()
                    and len(line_stripped) >= 3
                    and len(line_stripped) <= LOCATION_MAX_LENGTH
                    and ("," in line_stripped or line_stripped == "UNKNOWN")
                    and not location
                ):
                    location = line_stripped

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
    # Handle best_strategies which is a dict mapping category names to BestStrategyPerCategory objects
    story_strategy = best_strategies.get("story")
    story_name = story_strategy.strategy_name if story_strategy else ""
    story_score = story_strategy.score if story_strategy else 0.0

    special_power_strategy = best_strategies.get("special_power")
    power_name = special_power_strategy.strategy_name if special_power_strategy else ""
    power_score = special_power_strategy.score if special_power_strategy else 0.0

    # Convert BestStrategyPerCategory objects to dict format for JSON serialization
    strategies_dict: Dict[str, Dict] = {}
    for category, strategy_obj in best_strategies.items():
        strategies_dict[category] = {
            "strategy_name": strategy_obj.strategy_name,
            "score": strategy_obj.score,
        }

    config: Dict[str, Any] = {
        "version": "1.0.0",
        "last_updated": benchmark_data.get("timestamp", "").split("T")[0],
        "description": "Optimal OCR strategies per category, determined from benchmark results",
        "strategies": strategies_dict,
        "front_card_strategy": {
            "strategy_name": story_name,
            "description": f"Best for story extraction ({story_score:.1f}%)",
            "reason": "Story is the most important and hardest to extract from front card",
        },
        "back_card_strategy": {
            "strategy_name": power_name,
            "description": f"Best for power extraction ({power_score:.1f}%)",
            "reason": "Special power extraction is the most important back card field",
        },
    }

    if output_config is None:
        output_config = project_root / "scripts" / "data" / "optimal_ocr_strategies.json"

    output_config.parent.mkdir(parents=True, exist_ok=True)
    with open(output_config, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return config
