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

    # Remove OCR garbage: lines with too many special characters or random patterns
    lines = fixed.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip lines that are mostly OCR garbage
        # Check for patterns like "q so ee ee ee" or "i ii ale" or single characters repeated
        if len(line) < 3:
            continue

        # Count alphanumeric vs special characters
        alnum_count = sum(1 for c in line if c.isalnum())
        special_count = sum(1 for c in line if not c.isalnum() and c not in " .,!?\"'-:;")

        # Skip if more than 40% special characters (likely OCR garbage)
        if len(line) > 0 and special_count / len(line) > 0.4:
            continue

        # Skip if less than 30% alphanumeric (likely garbage)
        if len(line) > 0 and alnum_count / len(line) < 0.3:
            continue

        # Skip lines that are just random characters (like "i ii ale" or "q so ee ee")
        words = line.split()
        if len(words) > 0:
            # Check if most words are very short (1-2 chars) - likely OCR garbage
            short_words = sum(1 for w in words if len(w) <= 2)
            if len(words) > 3 and short_words / len(words) > 0.7:
                continue

        cleaned_lines.append(line)

    fixed = " ".join(cleaned_lines)

    # Remove common OCR garbage patterns
    # Remove standalone special characters and symbols
    fixed = re.sub(r"\s+[™©®°±²³´µ¶·¸¹º»¼½¾¿§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿]\s+", " ", fixed)
    fixed = re.sub(r"\s+[|\\/{}[\]()]\s+", " ", fixed)

    # Remove patterns like "é" at start of words (OCR error)
    fixed = re.sub(r"\bé\s+", "", fixed)

    # Remove random character sequences (like "nn ISS", "PSS", "WN", etc.)
    fixed = re.sub(r"\b[A-Z]{1,3}\s+[A-Z]{1,3}\s+[A-Z]{1,3}\b", "", fixed)

    # Remove trailing OCR garbage (common pattern: random chars at end)
    # Look for patterns like "f Z ere\na LJ {" or "q so ee ee ee SS Se ee"
    # Try to find where the actual story ends
    # Find all potential sentence endings
    endings = []
    for i, char in enumerate(fixed):
        if char in ".!?":
            endings.append(i)

    # Find the last "good" ending - one that's not followed by garbage
    garbage_patterns = [
        r"[a-z]\s+[A-Z]\s+[a-z]",  # "f Z ere"
        r"q\s+so\s+ee",  # "q so ee"
        r"SS\s+Se\s+ee",  # "SS Se ee"
        r"[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}",  # "et BY atenn bl"
        r"[A-Z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}",  # "HI ih WN"
    ]

    # Work backwards from the end to find the last good ending
    last_good_ending = -1
    for ending_pos in reversed(endings):
        text_after = fixed[ending_pos + 1:]
        if not text_after:
            # End of string - this is a good ending
            last_good_ending = ending_pos
            break

        # Check if text after ending looks like garbage
        alnum_after = sum(1 for c in text_after if c.isalnum())
        has_garbage = any(re.search(pattern, text_after) for pattern in garbage_patterns)

        # Also check if ending itself is garbage (single char + punctuation)
        text_before = fixed[max(0, ending_pos - 10):ending_pos]
        words_before = text_before.strip().split()
        ending_is_garbage = (
            words_before and len(words_before[-1]) <= 2 and fixed[ending_pos] in "!?"
        )

        # If text after is mostly good (>= 30% alphanumeric) and no garbage patterns, this is good
        if not ending_is_garbage and not has_garbage and alnum_after / len(text_after) >= 0.3:
            last_good_ending = ending_pos
            break

    # Truncate at the last good ending
    if last_good_ending >= 0:
        fixed = fixed[:last_good_ending + 1]

    # Additional aggressive cleanup: remove patterns that look like OCR garbage
    # Remove sequences of single letters followed by spaces (like "f Z ere")
    fixed = re.sub(r"\b[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\s*$", "", fixed)
    # Remove patterns like "q so ee ee ee"
    fixed = re.sub(r"\b[a-z]\s+[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s*$", "", fixed)
    # Remove trailing garbage like "SS Se ee g pa ne Pul"
    fixed = re.sub(r"\s+[A-Z]{1,2}\s+[A-Z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}\s*$", "", fixed)

    # Remove double/triple letters that are OCR errors
    fixed = re.sub(r"([a-zA-Z])\1{2,}", r"\1", fixed)  # "crosss" -> "cross"

    # Fix common word boundary issues
    fixed = re.sub(r"\bhs\b", "his", fixed, flags=re.I)
    fixed = re.sub(r"\bks\b", "his", fixed, flags=re.I)

    # Detect and remove duplicate paragraphs/sentences
    # First, try to detect if the story appears to be duplicated by checking for repeated key phrases
    key_phrases = ["lord benchley", "eye-twitch", "quite mad", "battled the cults", "stiff upper lip"]
    phrase_counts = {}
    for phrase in key_phrases:
        count = fixed.lower().count(phrase)
        phrase_counts[phrase] = count

    # If key phrases appear multiple times, likely duplicates
    max_count = max(phrase_counts.values()) if phrase_counts else 0
    if max_count > 1:
        # Try to find where the duplicate starts by looking for the second occurrence of a key phrase
        # Find the second occurrence of "Lord Benchley" (or similar key phrase)
        second_key_pos = -1
        for phrase in key_phrases:
            positions = [m.start() for m in re.finditer(re.escape(phrase), fixed.lower())]
            if len(positions) >= 2:
                second_key_pos = positions[1]
                break

        # If we found a second occurrence, check if the text after it is similar to the beginning
        if second_key_pos > len(fixed) * 0.4:  # Second occurrence is in second half
            # Compare first half with second half
            first_half = fixed[:second_key_pos].lower()
            second_half = fixed[second_key_pos:].lower()
            # Normalize for comparison
            first_norm = re.sub(r'[^\w\s]', '', first_half)
            second_norm = re.sub(r'[^\w\s]', '', second_half)
            # Check if they share many words
            words1 = set(first_norm.split())
            words2 = set(second_norm.split())
            if len(words1) > 0 and len(words2) > 0:
                similarity = len(words1 & words2) / max(len(words1), len(words2))
                # If second half is very similar to first half, it's likely a duplicate
                if similarity >= 0.4:  # 40% word overlap suggests duplication
                    # Truncate at the start of the duplicate
                    fixed = fixed[:second_key_pos].strip()
                    # Find the last sentence ending before the duplicate
                    last_period = fixed.rfind(".")
                    if last_period > len(fixed) * 0.8:  # If period is in last 20%, use it
                        fixed = fixed[:last_period + 1]
                    # Re-run duplicate detection on the truncated text
                    max_count = 0  # Reset to skip duplicate detection below
        # Split into sentences (preserve punctuation)
        sentence_parts = re.split(r'([.!?]\s+)', fixed)
        sentences = []
        for i in range(0, len(sentence_parts) - 1, 2):
            if i + 1 < len(sentence_parts):
                sentence = (sentence_parts[i] + sentence_parts[i + 1]).strip()
            else:
                sentence = sentence_parts[i].strip()
            if sentence:
                sentences.append(sentence)

        if len(sentences) > 2:
            # Remove duplicates (case-insensitive, allowing for minor OCR differences)
            unique_sentences = []
            seen_normalized = set()
            for sentence in sentences:
                if not sentence:
                    continue
                # Normalize for comparison (remove extra spaces, lowercase, remove punctuation variations)
                normalized = re.sub(r'\s+', ' ', sentence.lower().strip())
                normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation for comparison

                # Check if this sentence is similar to one we've seen
                is_duplicate = False
                for seen in seen_normalized:
                    if len(normalized) > 10 and len(seen) > 10:
                        # Simple similarity check: count common words
                        words1 = set(normalized.split())
                        words2 = set(seen.split())
                        if len(words1) > 0 and len(words2) > 0:
                            similarity = len(words1 & words2) / max(len(words1), len(words2))
                            # Also check if they share key phrases
                            shared_key_phrases = sum(1 for phrase in key_phrases if phrase in normalized and phrase in seen)
                            # If high similarity OR many shared key phrases, it's likely a duplicate
                            # Lower threshold for stories with many key phrases (like Adam's story)
                            threshold = 0.5 if shared_key_phrases >= 2 else 0.6
                            if similarity >= threshold or (shared_key_phrases >= 2 and similarity >= 0.35):
                                is_duplicate = True
                                break
                    elif normalized == seen:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    unique_sentences.append(sentence)
                    seen_normalized.add(normalized)

            # Only use deduplicated version if we actually removed duplicates
            if len(unique_sentences) < len(sentences):
                fixed = " ".join(unique_sentences)

    # Final cleanup
    fixed = re.sub(r"\s+", " ", fixed)
    fixed = fixed.strip()

    return fixed


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
