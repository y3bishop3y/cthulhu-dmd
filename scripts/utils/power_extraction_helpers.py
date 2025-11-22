#!/usr/bin/env python3
"""
Helper functions for extracting and validating common power names from OCR text.

This module provides utilities for:
- Extracting power names from multi-word lines
- Fuzzy matching against known power names
- Validating detected power matches
"""

from typing import Any, List, Optional, Tuple

from scripts.cli.parse.parsing_constants import (
    COMMON_POWER_PREV_LINE_ENDINGS,
    COMMON_POWER_PREV_LINE_LENGTH_THRESHOLD,
    PUNCTUATION_CONTINUATION_CHARS,
)
from scripts.models.character import BackCardData


def extract_power_candidate_from_words(
    line: str, all_common_powers: List[str]
) -> Optional[str]:
    """Extract power name candidate from a short multi-word line.

    Handles cases like "ps sss" where "sss" is part of "Swiftness".
    Only processes short lines (<=15 chars) to avoid false positives from
    long description text.

    Args:
        line: Line text to process
        all_common_powers: List of all known common power names

    Returns:
        Extracted power candidate line, or None if not found
    """
    line_stripped = line.strip()
    words = line_stripped.split()

    # Only process short lines with multiple words
    if len(words) <= 1 or len(line_stripped) > 15:
        return None

    # First check if the full line matches (prefer exact matches)
    full_line_power = BackCardData._detect_common_power(line_stripped)
    if full_line_power:
        return None  # Full line already matches, no need to extract

    # Try to find a word or word combination that matches a power name
    # Prefer longer words (more likely to be power names)
    words_by_length = sorted(
        words, key=lambda w: len(w.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()), reverse=True
    )

    for word in words_by_length:
        word_clean = word.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
        if len(word_clean) >= 3:  # At least 3 chars (reject 2-char words entirely)
            detected = BackCardData._detect_common_power(word_clean)
            if detected:
                # Found a power name in this word, use just this word
                return word_clean

    # If no single word matched, try 2-word combinations (for "Arcane Mastery" etc)
    if len(words) >= 2:
        for j in range(len(words) - 1):
            two_words = f"{words[j]} {words[j+1]}"
            two_words_clean = two_words.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
            detected = BackCardData._detect_common_power(two_words_clean)
            if detected:
                return two_words_clean

    return None


def calculate_fuzzy_thresholds(line_length: int) -> Tuple[float, float, float]:
    """Calculate fuzzy matching thresholds based on line length.

    Args:
        line_length: Length of the line being matched

    Returns:
        Tuple of (threshold, final_threshold, max_length_multiplier)
        - threshold: Minimum score to consider during matching
        - final_threshold: Minimum score to accept the match
        - max_length_multiplier: Maximum allowed length multiplier
    """
    is_very_short = line_length <= 5
    is_short = line_length <= 10
    is_long = line_length > 30

    if is_very_short:
        return (60.0, 65.0, 2.0)
    elif is_short:
        return (65.0, 70.0, 1.8)
    elif is_long:
        return (75.0, 75.0, 1.3)
    else:
        return (70.0, 75.0, 1.5)


def find_power_via_fuzzy_matching(
    line: str, all_common_powers: List[str], rapidfuzz_fuzz: Optional[Any]
) -> Optional[str]:
    """Find power name using fuzzy matching against all known powers.

    Args:
        line: Line text to match
        all_common_powers: List of all known common power names
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        Best matching power name, or None if no good match found
    """
    if not rapidfuzz_fuzz:
        return None

    line_clean = line.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
    line_length = len(line_clean)

    # Determine thresholds based on line length
    threshold, final_threshold, max_length_multiplier = calculate_fuzzy_thresholds(line_length)
    is_very_short = line_length <= 5

    best_match = None
    best_score = 0.0
    best_partial_score = 0.0

    for known_power in all_common_powers:
        # Try exact match first
        if known_power.upper() == line_clean.upper():
            return known_power

        # Try fuzzy matching
        ratio = rapidfuzz_fuzz.ratio(line_clean.upper(), known_power.upper())
        partial_ratio = rapidfuzz_fuzz.partial_ratio(line_clean.upper(), known_power.upper())
        score = max(ratio, partial_ratio)

        # Check if score meets threshold and length is reasonable
        if score > best_score and (
            score >= threshold or (is_very_short and partial_ratio >= 75.0)
        ):
            # Additional validation: reject if line is too long (likely description)
            if len(line_clean) <= len(known_power) * max_length_multiplier:
                best_score = score
                best_partial_score = partial_ratio
                best_match = known_power

    # Accept the best match if it's good enough
    if best_match:
        if is_very_short:
            # Very short lines: require at least 65% OR 75%+ partial match
            if best_score >= 65.0 or best_partial_score >= 75.0:
                return best_match
        elif line_length <= 10:
            # Short lines: require at least 70%
            if best_score >= 70.0:
                return best_match
        else:
            # Medium/long lines: require at least 75%
            if best_score >= 75.0:
                return best_match

    return None


def check_fuzzy_match_quality(
    line: str, power_name: str, rapidfuzz_fuzz: Optional[Any]
) -> Tuple[bool, bool]:
    """Check if a detected power was found via fuzzy matching and has high partial match.

    Args:
        line: Line that matched the power
        power_name: Detected power name
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        Tuple of (found_via_fuzzy, has_high_partial_match)
    """
    if not rapidfuzz_fuzz:
        return (False, False)

    line_clean = line.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
    ratio = rapidfuzz_fuzz.ratio(line_clean.upper(), power_name.upper())
    partial = rapidfuzz_fuzz.partial_ratio(line_clean.upper(), power_name.upper())
    score = max(ratio, partial)

    found_via_fuzzy = score >= 60.0 and power_name.upper() != line_clean.upper()
    has_high_partial_match = partial >= 75.0

    return (found_via_fuzzy, has_high_partial_match)


def validate_power_length(
    line: str,
    power_name: str,
    found_via_fuzzy: bool,
    has_high_partial_match: bool,
    rapidfuzz_fuzz: Optional[Any],
) -> Tuple[bool, str]:
    """Validate that line length is acceptable for the detected power.

    Args:
        line: Line text
        power_name: Detected power name
        found_via_fuzzy: Whether power was found via fuzzy matching
        has_high_partial_match: Whether partial match score is high (>=75%)
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        Tuple of (is_valid, cleaned_line)
    """
    line_stripped = line.strip()

    # Reject 2-character lines entirely unless exact match
    if len(line_stripped) == 2 and power_name.upper() != line_stripped.upper():
        return (False, line_stripped)

    # Reject very short lines that are likely OCR garbage
    if len(line_stripped) < 4 and power_name.upper() != line_stripped.upper() and not found_via_fuzzy:
        return (False, line_stripped)

    # Check minimum length threshold (50% of power name length)
    min_length_threshold = len(power_name) * 0.5
    if len(line_stripped) < min_length_threshold:
        # Exception: Allow very short lines if found via fuzzy matching OR has high partial match
        if found_via_fuzzy or has_high_partial_match:
            if rapidfuzz_fuzz:
                partial = rapidfuzz_fuzz.partial_ratio(line_stripped.upper(), power_name.upper())
                if partial >= 75.0:
                    # High partial match, trust it even if short
                    return (True, line_stripped)
                elif len(line_stripped) >= 3:
                    # Lower partial match but at least 3 chars, allow it
                    return (True, line_stripped)
                else:
                    return (False, line_stripped)
            elif len(line_stripped) >= 3:
                return (True, line_stripped)
            else:
                return (False, line_stripped)
        elif len(line_stripped) >= 3:
            # Check if removing punctuation makes it match better
            line_no_punct = line_stripped.rstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
            if line_no_punct and BackCardData._detect_common_power(line_no_punct) == power_name:
                return (True, line_no_punct)
            elif rapidfuzz_fuzz:
                ratio = rapidfuzz_fuzz.ratio(line_stripped.upper(), power_name.upper())
                if ratio >= 60.0:
                    return (True, line_stripped)
                else:
                    return (False, line_stripped)
            else:
                return (False, line_stripped)
        else:
            return (False, line_stripped)

    return (True, line_stripped)


def validate_power_partial_match(
    line: str, power_name: str, found_via_fuzzy: bool, rapidfuzz_fuzz: Optional[Any]
) -> Tuple[bool, str]:
    """Validate that partial matches are acceptable.

    Args:
        line: Line text
        power_name: Detected power name
        found_via_fuzzy: Whether power was found via fuzzy matching
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module

    Returns:
        Tuple of (is_valid, cleaned_line)
    """
    # Skip this check if found via fuzzy matching (already validated)
    if found_via_fuzzy:
        return (True, line)

    from scripts.utils.optimal_ocr import _reject_partial_match

    if _reject_partial_match(line, power_name, rapidfuzz_fuzz):
        # Check if removing leading punctuation makes it a better match
        line_no_punct = line.lstrip(PUNCTUATION_CONTINUATION_CHARS).strip()
        if line_no_punct and BackCardData._detect_common_power(line_no_punct) == power_name:
            return (True, line_no_punct)
        else:
            return (False, line)

    return (True, line)


def validate_power_quality(
    line: str,
    power_name: str,
    found_via_fuzzy: bool,
    rapidfuzz_fuzz: Optional[Any],
    prev_line: Optional[str] = None,
) -> bool:
    """Perform comprehensive quality validation on detected power.

    Args:
        line: Line text
        power_name: Detected power name
        found_via_fuzzy: Whether power was found via fuzzy matching
        rapidfuzz_fuzz: Optional rapidfuzz.fuzz module
        prev_line: Optional previous line for context

    Returns:
        True if power match is of good quality, False otherwise
    """
    from scripts.utils.optimal_ocr import (
        _check_line_has_description_keywords,
        _validate_power_match_quality,
    )

    # Validate match quality - skip if found via fuzzy matching (already validated)
    if found_via_fuzzy:
        is_good_match = True
    else:
        is_good_match = _validate_power_match_quality(line, power_name, rapidfuzz_fuzz)

    # Additional validation for non-exact matches
    if is_good_match and power_name.upper() != line.upper():
        # Check if line contains description keywords
        if _check_line_has_description_keywords(line):
            return False

        # Check if previous line suggests this is part of a description
        if prev_line and len(prev_line) > COMMON_POWER_PREV_LINE_LENGTH_THRESHOLD:
            prev_line_upper = prev_line.upper()
            if any(prev_line_upper.endswith(kw) for kw in COMMON_POWER_PREV_LINE_ENDINGS):
                return False

    return is_good_match

