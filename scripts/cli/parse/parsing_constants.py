#!/usr/bin/env python3
"""
Constants for OCR parsing and pattern matching.

Provides regex patterns and constants used for OCR text analysis and dice/swirl detection.
"""

from typing import Final, List

# Dice symbols commonly used in OCR text
DICE_SYMBOLS: Final[List[str]] = ["@", "#", "®"]

# Regex patterns for green dice detection (handles OCR errors)
GREEN_DICE_PATTERNS: Final[List[str]] = [
    r"green\s+dice",
    r"gain\s+.*?green",
    r"goin\s+.*?green",  # OCR error: "goin" = "gain"
    r"psone",  # OCR error: "PSOne" = "Green"
    r"green\s+die",
    r"\d+\s+green",  # "2 green dice" or "2 green"
    r"gain\s+\d+\s+green",  # "gain 2 green"
    r"goin\s+\d+\s+green",  # OCR error
]

# Regex patterns for black dice detection (handles OCR errors)
BLACK_DICE_PATTERNS: Final[List[str]] = [
    r"black\s+dice",
    r"gain\s+.*?black",
    r"goin\s+.*?black",  # OCR error
    r"black\s+die",
    r"\d+\s+black",
    r"gain\s+\d+\s+black",
]

# Regex patterns for dice symbol detection in context
DICE_SYMBOL_CONTEXT_PATTERNS: Final[List[str]] = [
    r"gain\s+[@#®]",
    r"goin\s+[@#®]",  # OCR error
    r"@\s+dice",
    r"#\s+dice",
    r"@\s+while",  # "gain @ while your sanity"
    r"#\s+while",
    r"@\s+per",  # "gain @ per turn"
    r"@\s+when",
]

# Regex patterns for red swirl detection (handles OCR errors)
RED_SWIRL_PATTERNS: Final[List[str]] = [
    r"red\s+swirl",
    r"red\s+swir",  # OCR might cut off
    r"or\s+swirl",  # OCR error: "oR" = "Red"
    r"sanity.*?red",
    r"red.*?sanity",
    r"sanity.*?on.*?red",  # "sanity is on a Red Swirl"
    r"red\s+swirl.*?sanity",
    r"sanity.*?red\s+swirl",
    r"sanity.*?on\s+a\s+red",  # "sanity is on a Red Swirl"
    r"sanity.*?ison\s+a\s+red",  # OCR error: "ison" = "is on"
    r"sanity.*?on\s+a\s+or",  # OCR error: "oR" = "Red"
]

# Pattern for sanity + "on a" detection
SANITY_ON_A_PATTERN: Final[str] = r"sanity.*?on\s+a\s+"

# Distance thresholds for word proximity detection
WORD_PROXIMITY_THRESHOLD_CLOSE: Final[int] = 50  # Characters
WORD_PROXIMITY_THRESHOLD_FAR: Final[int] = 100  # Characters

# Minimum symbol count to consider as dice mentions
MIN_DICE_SYMBOL_COUNT: Final[int] = 2

# Minimum sanity mention count to consider red swirl discussion
MIN_SANITY_MENTION_COUNT: Final[int] = 2
