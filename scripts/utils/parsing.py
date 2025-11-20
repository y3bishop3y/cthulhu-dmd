#!/usr/bin/env python3
"""
Centralized parsing utilities for OCR text cleaning and pattern matching.

This module provides robust text cleaning, normalization, and pattern matching
functions that can be used across all parsing scripts.
"""

import re
from typing import Final, Dict, List, Optional, Tuple

# Comprehensive OCR error corrections
# Format: (incorrect_ocr_text, correct_text)
OCR_CORRECTIONS: Final[Dict[str, str]] = {
    # Common word errors
    "goin": "gain",
    "Goin": "Gain",
    "isone": "is on",
    "Isone": "Is on",
    "ison": "is on",
    "Is on": "Is on",
    "Yi": "elder signs",
    "Yx-": "elder signs",
    "elder sign": "elder sign",  # Keep for normalization
    "elder signs": "elder signs",
    # Number/letter confusions
    "0": "O",  # Context-dependent, but often O in text
    "1": "I",  # Context-dependent
    # Common OCR artifacts
    "|": " ",
    "~": " ",
    "—": "-",
    "–": "-",
}

# Dice symbol patterns that OCR might misinterpret
DICE_SYMBOL_PATTERNS: Final[List[Tuple[str, str]]] = [
    # Green dice patterns (various OCR interpretations)
    (r"[●○◉🟢🟩]", "green dice"),
    (r"green\s*dice", "green dice"),
    (r"Green\s*dice", "green dice"),
    (r"GREEN\s*DICE", "green dice"),
    # Black dice patterns
    (r"[■□⬛⬜]", "black dice"),
    (r"black\s*dice", "black dice"),
    (r"Black\s*dice", "black dice"),
    (r"BLACK\s*DICE", "black dice"),
    # Red swirl/sanity threshold patterns
    (r"[🌀🌀🌀🌀]", "red swirl"),
    (r"red\s*swirl", "red swirl"),
    (r"Red\s*swirl", "red swirl"),
    (r"RED\s*SWIRL", "red swirl"),
    (r"sanity\s*threshold", "red swirl"),
    (r"insanity\s*threshold", "red swirl"),
]

# Power description patterns for better extraction
POWER_LEVEL_PATTERNS: Final[List[str]] = [
    r"Level\s*(\d+)",
    r"L(\d+)",
    r"(\d+)\s*:",
    r"^(\d+)\s+",
]

# Common phrases that indicate power effects
EFFECT_INDICATORS: Final[List[str]] = [
    "gain",
    "add",
    "count",
    "may",
    "when",
    "instead",
    "also",
    "per turn",
    "free",
    "attack",
    "dice",
    "success",
    "elder sign",
    "tentacle",
    "sanity",
    "stress",
    "wound",
]


def normalize_dice_symbols(text: str) -> str:
    """Normalize dice symbol references in text.
    
    OCR often misinterprets dice symbols. This function normalizes
    various OCR interpretations to standard text.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Text with normalized dice symbol references
    """
    normalized = text
    
    # Normalize green dice references
    green_patterns = [
        r"[●○◉🟢🟩]",
        r"green\s*dice",
        r"Green\s*dice",
        r"GREEN\s*DICE",
    ]
    for pattern in green_patterns:
        normalized = re.sub(pattern, "green dice", normalized, flags=re.IGNORECASE)
    
    # Normalize black dice references
    black_patterns = [
        r"[■□⬛⬜]",
        r"black\s*dice",
        r"Black\s*dice",
        r"BLACK\s*DICE",
    ]
    for pattern in black_patterns:
        normalized = re.sub(pattern, "black dice", normalized, flags=re.IGNORECASE)
    
    return normalized


def normalize_red_swirl_symbols(text: str) -> str:
    """Normalize red swirl/sanity threshold references.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Text with normalized red swirl references
    """
    normalized = text
    
    # Red swirl patterns
    swirl_patterns = [
        r"[🌀🌀🌀🌀]",
        r"red\s*swirl",
        r"Red\s*swirl",
        r"RED\s*SWIRL",
        r"sanity\s*threshold",
        r"insanity\s*threshold",
        r"red\s*sanity\s*marker",
    ]
    for pattern in swirl_patterns:
        normalized = re.sub(pattern, "red swirl", normalized, flags=re.IGNORECASE)
    
    return normalized


def apply_ocr_corrections(text: str) -> str:
    """Apply comprehensive OCR error corrections.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Text with common OCR errors corrected
    """
    corrected = text
    
    # Apply dictionary-based corrections
    for error, correction in OCR_CORRECTIONS.items():
        corrected = corrected.replace(error, correction)
    
    return corrected


def clean_whitespace(text: str, preserve_newlines: bool = False) -> str:
    """Clean excessive whitespace from text.
    
    Args:
        text: Text to clean
        preserve_newlines: If True, preserve newlines and only clean within lines
        
    Returns:
        Text with cleaned whitespace
    """
    if preserve_newlines:
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove excessive whitespace within line
            line = re.sub(r"[ \t]+", " ", line)
            cleaned_lines.append(line.strip())
        return "\n".join(cleaned_lines)
    else:
        # Remove all whitespace including newlines
        return re.sub(r"\s+", " ", text).strip()


def remove_ocr_artifacts(text: str, preserve_symbols: bool = True) -> str:
    """Remove common OCR artifacts while preserving important symbols.
    
    Args:
        text: Text to clean
        preserve_symbols: If True, preserve dice/sanity-related symbols
        
    Returns:
        Text with OCR artifacts removed
    """
    cleaned = text
    
    # Remove vertical bars, tildes, etc.
    cleaned = re.sub(r"\s*[|]\s*", " ", cleaned)
    cleaned = re.sub(r"\s*[~]\s*", " ", cleaned)
    
    if preserve_symbols:
        # Keep letters, numbers, spaces, punctuation, and dice/sanity symbols
        cleaned = re.sub(r"[^\w\s\.,;:!?\-\(\)\[\]\/●○◉🌀■□⬛⬜]", "", cleaned)
    else:
        # More aggressive cleaning
        cleaned = re.sub(r"[^\w\s\.,;:!?\-\(\)\[\]\/]", "", cleaned)
    
    return cleaned


def clean_ocr_text(
    text: str,
    preserve_newlines: bool = False,
    preserve_symbols: bool = True,
    normalize_dice: bool = True,
    normalize_swirl: bool = True,
) -> str:
    """Comprehensive OCR text cleaning pipeline.
    
    This is the main function to use for cleaning OCR text. It applies
    all cleaning steps in the correct order.
    
    Args:
        text: Raw OCR text
        preserve_newlines: If True, preserve newlines for line-by-line parsing
        preserve_symbols: If True, preserve dice/sanity-related symbols
        normalize_dice: If True, normalize dice symbol references
        normalize_swirl: If True, normalize red swirl references
        
    Returns:
        Cleaned text ready for parsing
    """
    cleaned = text
    
    # Step 1: Apply basic OCR corrections (word-level fixes)
    cleaned = apply_ocr_corrections(cleaned)
    
    # Step 2: Normalize dice and red swirl symbols (before other cleaning)
    if normalize_dice:
        cleaned = normalize_dice_symbols(cleaned)
    if normalize_swirl:
        cleaned = normalize_red_swirl_symbols(cleaned)
    
    # Step 3: Clean whitespace
    cleaned = clean_whitespace(cleaned, preserve_newlines=preserve_newlines)
    
    # Step 4: Remove OCR artifacts
    cleaned = remove_ocr_artifacts(cleaned, preserve_symbols=preserve_symbols)
    
    return cleaned.strip()


def extract_power_level_number(text: str) -> Optional[int]:
    """Extract power level number from text.
    
    Looks for patterns like "Level 1", "L1", "1:", etc.
    
    Args:
        text: Text that may contain a level number
        
    Returns:
        Level number if found, None otherwise
    """
    for pattern in POWER_LEVEL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def is_likely_power_description(text: str, min_length: int = 10) -> bool:
    """Check if text is likely a power description.
    
    Uses heuristics to determine if text contains power description content.
    
    Args:
        text: Text to check
        min_length: Minimum length to consider
        
    Returns:
        True if text appears to be a power description
    """
    if len(text) < min_length:
        return False
    
    text_lower = text.lower()
    
    # Check for effect indicators
    effect_count = sum(1 for indicator in EFFECT_INDICATORS if indicator in text_lower)
    
    # If it has multiple effect indicators, it's likely a power description
    return effect_count >= 2


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text, handling OCR errors.
    
    Args:
        text: Text to extract sentences from
        
    Returns:
        List of sentences
    """
    # Split on sentence endings, but be lenient with OCR errors
    sentences = re.split(r"[.!?]\s+", text)
    
    # Clean each sentence
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Remove trailing punctuation artifacts
            sentence = re.sub(r"[.!?]+$", "", sentence)
            if sentence:
                cleaned_sentences.append(sentence)
    
    return cleaned_sentences


def find_power_section(text: str, power_name: str, context_lines: int = 5) -> Optional[str]:
    """Find the section of text related to a specific power.
    
    Args:
        text: Full text to search
        power_name: Name of the power to find
        context_lines: Number of lines of context to include
        
    Returns:
        Power section text if found, None otherwise
    """
    lines = text.split("\n")
    power_start = None
    
    # Find where the power is mentioned
    for i, line in enumerate(lines):
        if power_name.lower() in line.lower():
            power_start = i
            break
    
    if power_start is None:
        return None
    
    # Extract section with context
    start = max(0, power_start - context_lines)
    end = min(len(lines), power_start + 20)  # Look ahead more
    
    section_lines = lines[start:end]
    return "\n".join(section_lines)


def normalize_power_name(name: str) -> str:
    """Normalize power name for consistent matching.
    
    Args:
        name: Power name (may have OCR errors)
        
    Returns:
        Normalized power name
    """
    normalized = name.strip()
    
    # Common power name corrections
    corrections = {
        "Arcane Master": "Arcane Mastery",
        "Arcane": "Arcane Mastery",
        "Brawling": "Brawling",
        "Marksman": "Marksman",
        "Stealth": "Stealth",
        "Swiftness": "Swiftness",
        "Toughness": "Toughness",
    }
    
    # Try to match with corrections
    for key, value in corrections.items():
        if key.lower() in normalized.lower():
            return value
    
    return normalized


def extract_numbers_from_text(text: str) -> List[int]:
    """Extract all numbers from text.
    
    Useful for finding dice counts, levels, etc.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of numbers found
    """
    numbers = re.findall(r"\d+", text)
    return [int(n) for n in numbers]


def validate_power_description(description: str) -> Tuple[bool, List[str]]:
    """Validate a power description and return issues found.
    
    Args:
        description: Power description to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not description or len(description.strip()) < 5:
        issues.append("Description too short")
        return False, issues
    
    if len(description) > 500:
        issues.append("Description suspiciously long (possible OCR error)")
    
    # Check for common OCR error patterns
    if re.search(r"[|]{2,}", description):
        issues.append("Contains multiple vertical bars (OCR artifact)")
    
    if re.search(r"[~]{2,}", description):
        issues.append("Contains multiple tildes (OCR artifact)")
    
    # Check for suspicious character patterns
    if re.search(r"[^\w\s\.,;:!?\-\(\)\[\]\/]{3,}", description):
        issues.append("Contains suspicious character patterns")
    
    is_valid = len(issues) == 0
    return is_valid, issues

