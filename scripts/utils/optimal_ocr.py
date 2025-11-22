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
    PUNCTUATION_CONTINUATION_CHARS,
    QUOTE_CHARACTERS,
    SPECIAL_POWER_LEVEL_WIDTHS,
    SPECIAL_POWER_REGION,
)
from scripts.cli.parse.parsing_models import FieldStrategies, FrontCardFields, ImageRegions
from scripts.models.character import Power
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
    location_start = int(img_height * 0.32)  # 32% from top
    location_end = int(
        img_height * FRONT_CARD_LOCATION_END_PERCENT
    )  # Currently 30%, but should be > 35%
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
    name_height = int(img_height * 0.068)  # Name region height is 6.8%
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
        # Remove leading digits/numbers and OCR artifacts (like "5", "7", "p", etc.)
        cleaned_line = re.sub(r"^[\d\s\-_|~pP]+", "", line)
        cleaned_line = cleaned_line.strip()
        # Check if cleaned line is all uppercase (name should be uppercase)
        if cleaned_line.isupper() and len(cleaned_line) >= 3:
            return cleaned_line
        # Also check original line if it's mostly uppercase (handles cases like "5 LORD ADAM")
        if line.isupper() and len(line) >= 3:
            return line
        # Handle cases like "p LORD ADAM BENCHLEY" - remove leading single lowercase letter
        if len(line) > 3 and line[0].islower() and line[1:].isupper():
            return line[1:].strip()
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
        if (
            line_stripped.isupper()
            and len(line_stripped) > MOTTO_MAX_ALL_CAPS_LENGTH
            and not is_quoted
        ):
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
        r"[\u201c\u201d]([^\u201c\u201d]+)[\u201c\u201d]",  # Curly double quotes
        r"[\u2018\u2019]([^\u2018\u2019]+)[\u2018\u2019]",  # Curly single quotes
    ]

    for line in filtered_lines:
        # Check if line has any type of quotes
        has_quotes = any(quote_char in line for quote_char in QUOTE_CHARACTERS)

        if has_quotes:
            # Try each quote pattern - but handle multi-line quoted mottos
            # First, try to find the full quoted text across multiple lines
            full_line = " ".join(filtered_lines)  # Combine all lines to catch multi-line quotes
            for pattern in quote_patterns:
                # Find all matches (might span multiple lines)
                matches = list(re.finditer(pattern, full_line))
                if matches:
                    # Use the longest match (likely the full motto)
                    longest_match = max(matches, key=lambda m: len(m.group(1)))
                    motto = longest_match.group(1).strip()
                    # For quoted mottos, be more lenient:
                    # - Allow single-word mottos (like "HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAW!")
                    # - Allow all-caps mottos if they're in quotes
                    # - Allow longer mottos if they're in quotes (up to reasonable limit)
                    if (
                        len(motto) >= MOTTO_MIN_LINE_LENGTH  # At least 2 chars
                        and len(motto)
                        <= MOTTO_MAX_CHARS_QUOTED * 2  # Allow up to 300 chars for quoted
                    ):
                        return motto

            # If no pattern match, try individual line
            for pattern in quote_patterns:
                quoted_match = re.search(pattern, line)
                if quoted_match:
                    motto = quoted_match.group(1).strip()
                    if (
                        len(motto) >= MOTTO_MIN_LINE_LENGTH
                        and len(motto) <= MOTTO_MAX_CHARS_QUOTED * 2
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


def _fix_power_description_ocr_errors(text: str) -> str:
    """Fix common OCR errors in power level descriptions.

    Args:
        text: Power description text with potential OCR errors

    Returns:
        Corrected text
    """
    fixed = text

    # Fix "7 space" -> "1 space" when in context of "within X space of"
    fixed = re.sub(r"\b7\s+space\s+of\s+a\b", "1 space of a", fixed, flags=re.I)
    fixed = re.sub(r"\bwithin\s+7\s+space\s+of\s+a\b", "within 1 space of a", fixed, flags=re.I)

    # Fix "." -> "Gate" when in context of "space of a ." (period at end of sentence)
    # Match "space of a ." - try multiple patterns to catch all variations
    # Use word boundary before "space" and match period with optional trailing space
    fixed = re.sub(r"\bspace\s+of\s+a\s*\.", "space of a Gate", fixed, flags=re.I)
    # Handle comma case - "space of a ," -> "space of a Gate"
    fixed = re.sub(r"\bspace\s+of\s+a\s*,", "space of a Gate", fixed, flags=re.I)
    # Also try without word boundary (in case there's punctuation before "space")
    fixed = re.sub(r"space\s+of\s+a\s*\.", "space of a Gate", fixed, flags=re.I)
    fixed = re.sub(r"space\s+of\s+a\s*,", "space of a Gate", fixed, flags=re.I)

    # Fix "guidemce" -> "guidance"
    fixed = re.sub(r"\bguidemce\b", "guidance", fixed, flags=re.I)

    # Fix level 4 description OCR errors
    # "J EY eemaerewrerenerean Gili S:" -> remove (OCR garbage at start)
    fixed = re.sub(r"^J\s+EY\s+eemaerewrerenerean\s+Gili\s+S:\s*", "", fixed, flags=re.I)
    # "hove" -> "have"
    fixed = re.sub(r"\bhove\b", "have", fixed, flags=re.I)
    # "gain and have" -> "gain Green Dice and have" (if "Green Dice" is missing)
    fixed = re.sub(r"\bgain\s+and\s+have\b", "gain Green Dice and have", fixed, flags=re.I)
    # "gain green dice" -> "gain Green Dice" (capitalize)
    fixed = re.sub(r"\bgain\s+green\s+dice\b", "gain Green Dice", fixed, flags=re.I)
    # "with 1 space" -> "within 1 space" (if "in" is missing)
    fixed = re.sub(
        r"\bwith\s+1\s+space\s+of\s+a\s+gate\b", "within 1 space of a Gate", fixed, flags=re.I
    )
    # "Rest" -> "rest" (lowercase for consistency)
    fixed = re.sub(r"\bRest\s+action\b", "rest action", fixed, flags=re.I)
    # Remove trailing OCR garbage like "--", "-", "e C", etc.
    fixed = re.sub(r"\s+--\s*$", "", fixed)
    fixed = re.sub(r"\s+-\s*$", "", fixed)
    # Remove "e C" at end (common OCR garbage)
    fixed = re.sub(r"\s+e\s+C\s*$", "", fixed, flags=re.I)
    fixed = re.sub(r"\s+e\s+C\.\s*$", "", fixed, flags=re.I)

    # Fix "wound" -> "would" when followed by "die" or "not"
    fixed = re.sub(r"\bwound\s+(die|not)\b", r"would \1", fixed, flags=re.I)
    # Fix "fo" -> "to" when followed by "life"
    fixed = re.sub(r"\bfo\s+life\b", "to life", fixed, flags=re.I)
    # Fix "ail" -> "all" when followed by "your"
    fixed = re.sub(r"\bail\s+your\b", "all your", fixed, flags=re.I)
    # Fix "and" -> "die" when in context of "count X and as"
    fixed = re.sub(r"\bcount\s+(\d+)\s+and\s+as\b", r"count \1 die as", fixed, flags=re.I)
    # Fix "aso" -> "as a"
    fixed = re.sub(r"\baso\b", "as a", fixed, flags=re.I)
    # Fix "os" -> "as"
    fixed = re.sub(r"\bos\s+a\b", "as a", fixed, flags=re.I)
    # Fix "I" -> "1" when followed by "of your wounds"
    fixed = re.sub(r"\bI\s+of\s+your\s+wounds\b", "1 of your wounds", fixed, flags=re.I)
    # Fix "13" -> "3" when followed by "total"
    fixed = re.sub(r"\b13\s+total\b", "3 total", fixed, flags=re.I)
    # Fix "Bb" -> "BB" (likely dice reference)
    fixed = re.sub(r"\bBb\b", "BB", fixed)
    # Remove leading "." followed by space or number
    fixed = re.sub(r"^\.\s+", "", fixed)
    # Remove trailing "ee a", "a )", "i )"
    fixed = re.sub(r"\s+ee\s+a\s*$", "", fixed, flags=re.I)
    fixed = re.sub(r"\s+[a-z]\s*\)\s*$", "", fixed, flags=re.I)
    # Remove trailing single letter + space
    fixed = re.sub(r"\s+[a-zA-Z]\s*$", "", fixed)
    # Remove trailing ")." or ")."
    fixed = re.sub(r"\)\.\s*$", ")", fixed)
    # Remove trailing comma if followed by nothing meaningful
    fixed = re.sub(r",\s*$", "", fixed)
    # Remove leading ";" or "; "
    fixed = re.sub(r"^;\s*", "", fixed)
    # Remove leading "d," or "d, "
    fixed = re.sub(r"^d,\s*", "", fixed, flags=re.I)
    # Remove leading "FON Nee a" or "FON Nee a "
    fixed = re.sub(r"^FON\s+Nee\s+a\s+", "", fixed, flags=re.I)
    # Remove "you:" -> "you"
    fixed = re.sub(r"\byou:\b", "you", fixed, flags=re.I)
    # Remove trailing "ee" (OCR garbage)
    fixed = re.sub(r"\s+ee\s*$", "", fixed, flags=re.I)
    # Remove leading "1 " if followed by "additional" (duplicate)
    fixed = re.sub(r"^1\s+additional\s+", "additional ", fixed, flags=re.I)

    return fixed


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
    # Prioritize region-based extraction using carefully calibrated coordinates
    story_start = int(img_height * FRONT_CARD_STORY_START_PERCENT)
    story_height = int(img_height * FRONT_CARD_STORY_HEIGHT_PERCENT)
    bottom_region = (0, story_start, img_width, story_height)
    story_text = extract_text_from_region_with_strategy(image_path, bottom_region, story_strategy)

    # Only fall back to extract_description_region if region-based extraction failed
    if not story_text or len(story_text) < STORY_MIN_LENGTH:
        story_text = extractor.extract_description_region(image_path)

    # Clean story text with advanced NLP post-processing
    if story_text:
        from scripts.core.parsing.text import clean_ocr_text
        from scripts.models.character_parsing_helpers import fix_story_ocr_errors

        story_text = clean_ocr_text(story_text, preserve_newlines=True)
        story_text = fix_story_ocr_errors(story_text)
        # Try advanced NLP post-processing for better correction
        try:
            from scripts.core.parsing.nlp_postprocessing import advanced_nlp_postprocess

            story_text = advanced_nlp_postprocess(story_text)
        except ImportError:
            # Fallback if NLP post-processing not available
            pass

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
            if (
                ratio >= 60.0
                and abs(line_len - len(power_name)) <= COMMON_POWER_CLOSE_MATCH_LENGTH_DIFF
            ):
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
    from scripts.models.character import BackCardData
    from scripts.models.constants import get_common_power_names
    from scripts.utils.power_extraction_helpers import (
        check_fuzzy_match_quality,
        extract_power_candidate_from_words,
        find_power_via_fuzzy_matching,
        validate_power_length,
        validate_power_partial_match,
        validate_power_quality,
    )

    # Extract text from region
    region_text = extract_text_from_region_with_strategy(image_path, region, strategy_name)
    if not region_text:
        return []

    # Split into lines and match common power names
    lines = [line.strip() for line in region_text.split("\n") if line.strip()]
    found_powers: List[str] = []

    # Get all known common power names
    all_common_powers = get_common_power_names()

    # Import fuzzy matching if available
    try:
        from rapidfuzz import fuzz as rapidfuzz_fuzz
    except ImportError:
        rapidfuzz_fuzz = None

    # Process each line to find power names
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Try extracting power candidate from short multi-word lines
        power_candidate = extract_power_candidate_from_words(line_stripped, all_common_powers)
        if power_candidate:
            line_stripped = power_candidate

        # First try the detection function (handles exact matches and common patterns)
        power_name = BackCardData._detect_common_power(line_stripped)

        # If not detected, try fuzzy matching
        if not power_name:
            power_name = find_power_via_fuzzy_matching(
                line_stripped, all_common_powers, rapidfuzz_fuzz
            )

        # Skip lines that look like descriptions (only if not detected as power)
        if not power_name:
            if _is_line_likely_description(line_stripped):
                continue
        else:
            # Reject long lines detected as power (likely false positives)
            # Exception: allow multi-word power names like "Arcane Mastery"
            if len(line_stripped) > 20 and power_name not in ["Arcane Mastery"]:
                continue

        # Validate and process detected power
        if power_name and power_name not in found_powers:
            # Check fuzzy match quality
            found_via_fuzzy, has_high_partial_match = check_fuzzy_match_quality(
                line_stripped, power_name, rapidfuzz_fuzz
            )

            # Validate length
            is_valid_length, line_stripped = validate_power_length(
                line_stripped, power_name, found_via_fuzzy, has_high_partial_match, rapidfuzz_fuzz
            )
            if not is_valid_length:
                continue

            # Validate partial matches
            is_valid_partial, line_stripped = validate_power_partial_match(
                line_stripped, power_name, found_via_fuzzy, rapidfuzz_fuzz
            )
            if not is_valid_partial:
                continue

            # Validate overall quality
            prev_line = lines[i - 1].strip() if i > 0 else None
            is_good_match = validate_power_quality(
                line_stripped, power_name, found_via_fuzzy, rapidfuzz_fuzz, prev_line
            )

            if is_good_match:
                found_powers.append(power_name)
                # Limit to 2 common powers (characters always have exactly 2)
                if len(found_powers) >= COMMON_POWER_MAX_POWERS:
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
            get_optimal_strategy_for_category("special_power", config)
            or "tesseract_bilateral_psm3",
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
                    region_powers_found = _extract_common_powers_from_region(
                        image_path, region, power_strategy
                    )
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
) -> Optional[Power]:
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
        from scripts.core.parsing.text import clean_ocr_text
        from scripts.models.character import BackCardData

        cleaned_text = clean_ocr_text(region_text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        power_name = None
        # Skip OCR garbage patterns (like "5 pe BY MADNESS", random characters, etc.)
        garbage_patterns = [
            r"^[\d\s]+$",  # Just digits and spaces
            r"^[a-z]{1,2}\s+[a-z]{1,2}",  # Very short lowercase words
            r"^[A-Z]{1,2}\s+[A-Z]{1,2}\s+[A-Z]{1,2}",  # Very short uppercase words (likely OCR garbage)
            r"Instead, gain",  # Common phrase that's not a power name
            r"Gain @",  # Common phrase
        ]

        # Common power name patterns to look for (handle OCR errors)
        # Look for "BY MADNESS" pattern and reconstruct "FUELED BY MADNESS"
        full_text = " ".join(lines[:15])

        # Check for "BY MADNESS" pattern
        by_madness_match = re.search(r"BY\s+MADNESS", full_text, re.I)
        if by_madness_match:
            # Look for "FUELED" before "BY MADNESS"
            before_match = full_text[: by_madness_match.start()]
            fueled_match = re.search(r"FUELED|FUEL|FUELE", before_match, re.I)
            if fueled_match:
                # Found "FUELED BY MADNESS"
                power_name = "FUELED BY MADNESS"
            else:
                # Just "BY MADNESS" - reconstruct as "FUELED BY MADNESS"
                power_name = "FUELED BY MADNESS"

        # If not found, look for other power name patterns
        if not power_name:
            power_name_patterns = [
                r"FUELED\s+BY\s+MADNESS",  # Full match
                r"FUELED\s+BY",  # Partial
                r"MADNESS",  # Just "MADNESS" if preceded by "BY"
            ]

            for pattern in power_name_patterns:
                match = re.search(pattern, full_text, re.I)
                if match:
                    # Extract surrounding context to get full power name
                    start = max(0, match.start() - 20)
                    end = min(len(full_text), match.end() + 20)
                    context = full_text[start:end]
                    # Look for all-caps words around the match
                    words = context.split()
                    caps_words = [
                        w
                        for w in words
                        if w.isupper()
                        and len(w) > 2
                        and w not in ["INSTEAD", "GAIN", "WHILE", "YOUR", "SANITY", "SPACE", "BACK"]
                    ]
                    if caps_words:
                        # Try to reconstruct power name (e.g., "FUELED BY MADNESS")
                        power_name = " ".join(caps_words[-3:])  # Take up to 3 words
                        if len(power_name) > 5:
                            break

        # Known special power names to look for (handle OCR errors)
        known_power_names = {
            "UNKILLABLE": ["UNKILLABLE", "UNKILLABL", "UNKILL", "UNKIL", "KILLABLE"],
            "SAVAGE": ["SAVAGE", "SAVAG", "SAVA"],
            "HEALING PRAYER": ["HEALING PRAYER", "HEALING PRAYE", "HEAL PRAYER", "PRAYER"],
            "GATE MANIPULATION": ["GATE MANIPULATION", "GATE MANIPUL", "MANIPULATION"],
            "VENGEANCE OBSESSION": ["VENGEANCE OBSESSION", "VENGEANCE", "OBSESSION", "VENGANCE"],
            "LUCKY": ["LUCKY", "LUCK"],
            "PROPHECY": ["PROPHECY", "PROPHEC"],
            "STRONG": ["STRONG", "STRON"],
        }

        # Check for known power names in the text
        if not power_name:
            full_text_upper = full_text.upper()
            for correct_name, variants in known_power_names.items():
                for variant in variants:
                    if variant in full_text_upper:
                        # Check if it's not part of a longer description
                        variant_pos = full_text_upper.find(variant)
                        # Look for context around the variant
                        context_start = max(0, variant_pos - 10)
                        context_end = min(len(full_text_upper), variant_pos + len(variant) + 10)
                        context = full_text_upper[context_start:context_end]
                        # If variant appears as a standalone word or short phrase, use it
                        if (
                            variant_pos == 0
                            or full_text_upper[variant_pos - 1] in [" ", "\n"]
                            or context.startswith(variant)
                        ):
                            power_name = correct_name
                            break
                if power_name:
                    break

        # Check for "UNKILLABLE" pattern (Rasputin)
        if not power_name:
            if re.search(r"UNKILL|KILLABLE|free\s+death", full_text, re.I):
                power_name = "UNKILLABLE"

        # Check for "STRONG" pattern (Sister Beth - reroll related)
        if not power_name:
            if re.search(r"STRONG|reroll|count.*as.*success", full_text, re.I):
                power_name = "STRONG"

        # If no pattern match, look for all-caps lines
        if not power_name:
            for line in lines[:15]:
                line_clean = line.strip()
                # Skip empty lines
                if not line_clean:
                    continue
                # Skip single digits/numbers (level indicators)
                if line_clean.isdigit() and len(line_clean) == 1:
                    continue
                # Skip garbage patterns
                if any(re.match(pattern, line_clean, re.I) for pattern in garbage_patterns):
                    continue
                # Skip description phrases that are not power names
                if any(
                    phrase in line_clean.upper()
                    for phrase in [
                        "WHEN YOU RETURN",
                        "INSTEAD, YOU MAY",
                        "YOU MAY PUT",
                        "INSTEAD,",
                        "GAIN",
                        "WHILE YOUR",
                    ]
                ):
                    continue
                # Skip lines that are mostly punctuation or special characters
                if sum(1 for c in line_clean if c.isalnum()) < len(line_clean) * 0.5:
                    continue
                # Look for all-caps line (power name) - must be substantial
                if (
                    line_clean.isupper()
                    and len(line_clean) > 5
                    and not any(char.isdigit() for char in line_clean)
                ):
                    # Make sure it's not just common words
                    if line_clean not in [
                        "INSTEAD",
                        "GAIN",
                        "WHILE",
                        "YOUR",
                        "SANITY",
                        "SPACE",
                        "BACK",
                    ]:
                        power_name = line_clean
                        break

        # If still no power name, try to extract from first substantial line
        if not power_name:
            for line in lines[:15]:
                line_clean = line.strip()
                if not line_clean or len(line_clean) <= 3 or line_clean.isdigit():
                    continue
                # Skip garbage patterns
                if any(re.match(pattern, line_clean, re.I) for pattern in garbage_patterns):
                    continue
                words = line_clean.split()
                if len(words) >= 2 and words[0][0].isupper():
                    # Make sure it's not just common phrases
                    if line_clean.upper() not in ["INSTEAD, GAIN", "GAIN @", "WHILE YOUR"]:
                        power_name = line_clean
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

            level_text = extract_text_from_region_with_strategy(
                image_path, level_region, power_strategy
            )
            if level_text:
                # Clean the text with advanced NLP post-processing
                cleaned_level_text = clean_ocr_text(level_text, preserve_newlines=False)
                cleaned_level_text = cleaned_level_text.strip()

                # Apply OCR corrections for common power description errors
                cleaned_level_text = _fix_power_description_ocr_errors(cleaned_level_text)
                # Fix "you:" -> "you" (apply here too for consistency)
                cleaned_level_text = re.sub(r"\byou:\b", "you", cleaned_level_text, flags=re.I)
                # Remove trailing "ee" (OCR garbage) - apply here too
                cleaned_level_text = re.sub(r"\s+ee\s*$", "", cleaned_level_text, flags=re.I)

                # Apply advanced NLP post-processing for better OCR error correction
                try:
                    from scripts.core.parsing.nlp_postprocessing import advanced_nlp_postprocess

                    cleaned_level_text = advanced_nlp_postprocess(cleaned_level_text)
                except ImportError:
                    # Fallback if NLP post-processing not available
                    pass

                # Apply OCR corrections again AFTER NLP post-processing (in case NLP undid them)
                cleaned_level_text = _fix_power_description_ocr_errors(cleaned_level_text)

                # Remove power name if it appears in the level text (handle partial matches)
                # Remove full power name
                cleaned_level_text = re.sub(
                    rf"\b{re.escape(power_name)}\b", "", cleaned_level_text, flags=re.I
                )

                # Remove partial power name matches (e.g., "GATE MANIPUI" or "ATION")
                # Split power name into words and remove each word if it appears alone
                power_words = power_name.split()
                for word in power_words:
                    if len(word) > 3:  # Only remove substantial words
                        # Remove word if it appears as a standalone word
                        cleaned_level_text = re.sub(
                            rf"\b{re.escape(word)}\b", "", cleaned_level_text, flags=re.I
                        )

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
                            or (
                                len(first_word) >= 4
                                and len(word_upper) >= 4
                                and first_word[:4] == word_upper[:4]
                            )
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
                cleaned_level_text = re.sub(
                    r"^\d+\s*", "", cleaned_level_text
                )  # Remove leading digits
                cleaned_level_text = re.sub(r"\s+", " ", cleaned_level_text)  # Normalize whitespace
                cleaned_level_text = cleaned_level_text.strip()

                # Final fix for "space of a ." -> "space of a Gate" (apply one more time after all cleaning)
                cleaned_level_text = cleaned_level_text.replace("space of a .", "space of a Gate")
                cleaned_level_text = cleaned_level_text.replace("space of a ,", "space of a Gate")

                # Remove OCR garbage at the start of level descriptions
                # Patterns like "PS 1", "po STRUNG", "iy es BY MA", "fa venceance fe", etc.
                cleaned_level_text = re.sub(
                    r"^[a-z]{1,2}\s+[A-Z]{1,6}\s*[:\-]?\s*", "", cleaned_level_text, flags=re.I
                )
                cleaned_level_text = re.sub(
                    r"^[A-Z]{1,3}\s+[A-Z]{1,3}\s+[A-Z]{1,3}\s*[:\-]?\s*", "", cleaned_level_text
                )
                # Remove patterns like "PS 1", "fo", "ww", "ae", etc. at start
                cleaned_level_text = re.sub(r"^[a-z]{1,2}\s+", "", cleaned_level_text, flags=re.I)
                cleaned_level_text = re.sub(r"^[A-Z]{1,2}\s+", "", cleaned_level_text)
                # Remove single/double letter + space at start
                cleaned_level_text = re.sub(r"^[a-zA-Z]{1,2}\s+", "", cleaned_level_text)
                # Remove patterns like "PS 1 free death:" -> "1 free death:"
                cleaned_level_text = re.sub(r"^[A-Z]{1,2}\s+\d+\s+", "", cleaned_level_text)

                # Remove OCR garbage at the end of level descriptions
                # Patterns like "er", "ae", "wt", "oo. (Y", "t", etc.
                cleaned_level_text = re.sub(r"\s+[a-z]{1,2}\s*$", "", cleaned_level_text, flags=re.I)
                cleaned_level_text = re.sub(r"\s+[A-Z]{1,2}\s*$", "", cleaned_level_text)
                # Remove trailing punctuation garbage like "._", "._.", "--", etc.
                cleaned_level_text = re.sub(r"\s+[._\-]{1,3}\s*$", "", cleaned_level_text)
                # Remove trailing single characters with punctuation
                cleaned_level_text = re.sub(r"\s+[a-zA-Z][._\-)]\s*$", "", cleaned_level_text)
                # Remove trailing patterns like "13 total). _" -> "13 total)."
                cleaned_level_text = re.sub(r"\s+[._\-]\s*$", "", cleaned_level_text)
                # Remove trailing ")." or ")."
                cleaned_level_text = re.sub(r"\)\.\s*$", ")", cleaned_level_text)
                # Remove trailing "." if it's not part of a sentence (like "(2 total.")
                cleaned_level_text = re.sub(r"\((\d+)\s+total\)\.\s*$", r"(\1 total)", cleaned_level_text)
                # Also handle cases without parentheses: "2 total." -> "2 total"
                cleaned_level_text = re.sub(r"(\d+)\s+total\.\s*$", r"\1 total", cleaned_level_text)
                # Fix missing closing parenthesis: "(2 total" -> "(2 total)"
                cleaned_level_text = re.sub(r"\((\d+)\s+total\s*$", r"(\1 total)", cleaned_level_text)
                # Remove trailing "ee" or similar single/double letter OCR garbage
                cleaned_level_text = re.sub(r"\s+ee\s*$", "", cleaned_level_text, flags=re.I)
                # Remove trailing single letter + space (like "a")
                cleaned_level_text = re.sub(r"\s+[a-zA-Z]\s*$", "", cleaned_level_text)
                # Remove trailing "ee a" or similar (two letters)
                cleaned_level_text = re.sub(r"\s+[a-z]{1,2}\s+[a-z]\s*$", "", cleaned_level_text, flags=re.I)
                # Remove trailing comma
                cleaned_level_text = re.sub(r",\s*$", "", cleaned_level_text)
                # Fix "and" -> "die" when in context of "count any number of and as"
                cleaned_level_text = re.sub(r"\bcount\s+any\s+number\s+of\s+and\s+as\b", "count any number of die as", cleaned_level_text, flags=re.I)
                # Remove leading ";"
                cleaned_level_text = re.sub(r"^;\s*", "", cleaned_level_text)
                # Remove leading "d,"
                cleaned_level_text = re.sub(r"^d,\s*", "", cleaned_level_text, flags=re.I)
                # Remove leading "."
                cleaned_level_text = re.sub(r"^\.\s+", "", cleaned_level_text)

                # Clean up any remaining whitespace
                cleaned_level_text = re.sub(r"\s+", " ", cleaned_level_text)
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
        # Clean story text with advanced NLP post-processing
        if story:
            from scripts.core.parsing.text import clean_ocr_text
            from scripts.models.character_parsing_helpers import fix_story_ocr_errors

            story = clean_ocr_text(story, preserve_newlines=True)
            story = fix_story_ocr_errors(story)
            # Try advanced NLP post-processing for better correction
            try:
                from scripts.core.parsing.nlp_postprocessing import advanced_nlp_postprocess

                story = advanced_nlp_postprocess(story)
            except ImportError:
                # Fallback if NLP post-processing not available
                pass

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
