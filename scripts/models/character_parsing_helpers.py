#!/usr/bin/env python3
"""
Helper functions for character parsing.

Extracted helper methods from character.py to improve maintainability
and testability.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from scripts.models.character_constants import (
    COMMON_POWER_LINE_MAX_LENGTH,
    GAME_RULES_LINE_KEYWORDS,
    MOTTO_END_KEYWORDS,
    MOTTO_KEYWORDS,
    MOTTO_MAX_LENGTH,
    MOTTO_MIN_LENGTH,
    MOTTO_QUOTE_PATTERNS,
    MOTTO_REASONABLE_MAX,
    MOTTO_REASONABLE_MIN,
    MOTTO_START_KEYWORDS,
    POWER_DESCRIPTION_KEYWORDS,
    STORY_COMMON_WORDS,
    STORY_KEYWORDS,
)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def load_ocr_story_corrections() -> Dict[str, Dict]:
    """Load OCR story corrections from JSON file.

    Returns:
        Dictionary with 'corrections' and 'priority_order' keys
    """
    corrections_file = project_root / "scripts" / "data" / "ocr_story_corrections.json"
    if not corrections_file.exists():
        return {"corrections": {}, "priority_order": []}

    with open(corrections_file, encoding="utf-8") as f:
        return json.load(f)


def fix_story_ocr_errors(story: str) -> str:
    """Fix common OCR errors in story text.

    Args:
        story: Story text with potential OCR errors

    Returns:
        Corrected story text
    """
    corrections_data = load_ocr_story_corrections()
    corrections = corrections_data.get("corrections", {})
    priority_order = corrections_data.get("priority_order", [])

    fixed = story

    # First apply priority corrections (case-insensitive)
    for error in priority_order:
        if error in corrections:
            pattern = re.compile(re.escape(error), re.IGNORECASE)
            fixed = pattern.sub(corrections[error], fixed)

    # Then apply remaining corrections sorted by length (longest first)
    remaining_corrections = {k: v for k, v in corrections.items() if k not in priority_order}
    sorted_corrections = sorted(
        remaining_corrections.items(), key=lambda x: len(x[0]), reverse=True
    )
    for error, correction in sorted_corrections:
        pattern = re.compile(re.escape(error), re.IGNORECASE)
        fixed = pattern.sub(correction, fixed)

    # Fix spacing issues
    fixed = re.sub(r"\s+", " ", fixed)
    fixed = re.sub(r"([a-z])([A-Z])", r"\1 \2", fixed)  # Add space between words

    # Fix double letters that are OCR errors
    fixed = re.sub(r"Benchleyy+", "Benchley", fixed, flags=re.I)

    # Fix "rereserve" -> "reserve" (must happen AFTER whitespace normalization)
    fixed = re.sub(r"\brereserve\b", "reserve", fixed, flags=re.I)

    # Fix punctuation issues
    fixed = re.sub(r"([a-z])-([A-Z])", r"\1. \2", fixed)  # "word-Word" -> "word. Word"
    fixed = re.sub(r"([a-z])-([a-z])", r"\1-\2", fixed)  # Keep hyphens in compound words

    return fixed.strip()


def is_game_rules_line(line: str) -> bool:
    """Check if a line is a game rules section that should be skipped.

    Args:
        line: Line to check

    Returns:
        True if line should be skipped
    """
    line_upper = line.upper()
    return any(keyword in line_upper for keyword in GAME_RULES_LINE_KEYWORDS)


def extract_motto_from_quotes(text: str) -> Optional[str]:
    """Extract motto from quoted text.

    Args:
        text: Text to search for quotes

    Returns:
        Extracted motto or None
    """
    for pattern in MOTTO_QUOTE_PATTERNS:
        quotes = re.findall(pattern, text)
        if quotes:
            for quote in quotes:
                quote_clean = quote.strip()
                # Check if it looks like a motto
                if MOTTO_MIN_LENGTH < len(quote_clean) < MOTTO_MAX_LENGTH and any(
                    word in quote_clean.lower() for word in MOTTO_KEYWORDS
                ):
                    return quote_clean
    return None


def extract_motto_from_multiline(lines: List[str]) -> Optional[str]:
    """Extract motto from multi-line pattern.

    Args:
        lines: List of text lines

    Returns:
        Extracted motto or None
    """
    # Look in first 15 lines (motto is usually near the top)
    for i in range(min(15, len(lines))):
        line = lines[i]
        line_lower = line.lower().strip()

        # Check if this line starts a motto
        if (
            any(keyword in line_lower for keyword in MOTTO_START_KEYWORDS)
            and len(line.split()) <= 5  # Short line
            and not line.isupper()  # Not all caps
            and i > 0  # Not the first line
        ):
            # Check if next line completes it
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_lower = next_line.lower()

                if (
                    any(keyword in next_lower for keyword in MOTTO_END_KEYWORDS)
                    and len(next_line.split()) <= 5
                    and not next_line.isupper()
                ):
                    combined = f"{line} {next_line}".strip()
                    combined = re.sub(r"\s+", " ", combined)
                    if MOTTO_REASONABLE_MIN < len(combined) < MOTTO_REASONABLE_MAX:
                        return combined
    return None


def extract_motto_from_single_line(
    lines: List[str], name: Optional[str], location: Optional[str]
) -> Optional[str]:
    """Extract motto from single line.

    Args:
        lines: List of text lines
        name: Character name (to skip)
        location: Character location (to skip)

    Returns:
        Extracted motto or None
    """
    for line in lines[:20]:  # Check first 20 lines
        line_lower = line.lower().strip()
        # Skip if it's the name or location
        if (name and name.lower() in line_lower) or (location and location.lower() in line_lower):
            continue

        # Check if it looks like a motto
        if (
            len(line.split()) >= 2
            and len(line.split()) <= 8  # Short phrase
            and not line.isupper()
            and not line.isdigit()
            and any(word in line_lower for word in MOTTO_KEYWORDS)
            and len(line) < 100
        ):
            return line.strip()
    return None


def score_story_paragraph(
    paragraph: str, name: Optional[str], location: Optional[str], motto: Optional[str]
) -> int:
    """Score a paragraph for story quality.

    Args:
        paragraph: Paragraph text to score
        name: Character name (to exclude)
        location: Character location (to exclude)
        motto: Character motto (to exclude)

    Returns:
        Quality score (higher is better)
    """
    para_stripped = paragraph.strip()
    if (
        len(para_stripped) <= 80
        or para_stripped.isupper()
        or (name and name.lower() in para_stripped.lower())
        or (location and location.lower() in para_stripped.lower())
        or (motto and motto.lower() in para_stripped.lower())
    ):
        return -1000  # Very low score for invalid paragraphs

    score = len(para_stripped)
    word_count = len(para_stripped.split())
    score += word_count * 5  # Prefer paragraphs with more words

    # Penalize OCR errors
    error_chars = sum(para_stripped.count(c) for c in "@#$%^&*|~`")
    score -= error_chars * 5

    # Prefer paragraphs that look like prose
    para_lower = para_stripped.lower()
    common_word_count = sum(1 for word in para_lower.split() if word in STORY_COMMON_WORDS)
    score += common_word_count * 3

    # Bonus for story-like words
    story_word_count = sum(1 for word in STORY_KEYWORDS if word in para_lower)
    score += story_word_count * 10

    # Penalize if it looks like game rules
    from scripts.models.character_constants import GAME_RULES_KEYWORDS

    if any(keyword in para_stripped.upper() for keyword in GAME_RULES_KEYWORDS):
        score -= 100

    return score


def is_common_power_description_line(line: str) -> bool:
    """Check if a line looks like a power description (not a power name).

    Args:
        line: Line to check

    Returns:
        True if line looks like a description
    """
    line_upper = line.upper()
    line_len = len(line.strip())

    # Skip very long lines (likely descriptions)
    if line_len > COMMON_POWER_LINE_MAX_LENGTH:
        return True

    # Skip lines that look like descriptions
    if any(keyword in line_upper for keyword in POWER_DESCRIPTION_KEYWORDS):
        return True

    return False
