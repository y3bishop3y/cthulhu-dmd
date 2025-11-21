#!/usr/bin/env python3
"""
Constants for OCR parsing and pattern matching.

Centralizes regex patterns, region coordinates, and related numerical constants
for dice/swirl detection and common power extraction.
"""

from typing import Final, List, Tuple

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

# Common power extraction constants
COMMON_POWER_MAX_LINE_LENGTH: Final[int] = 50
COMMON_POWER_MAX_WORDS: Final[int] = 3
COMMON_POWER_MAX_LENGTH_DIFF: Final[int] = 10
COMMON_POWER_PARTIAL_MATCH_THRESHOLD: Final[int] = 3
COMMON_POWER_FUZZY_MATCH_THRESHOLD: Final[float] = 75.0
COMMON_POWER_PARTIAL_FUZZY_THRESHOLD: Final[float] = 85.0
COMMON_POWER_PARTIAL_LENGTH_DIFF_THRESHOLD: Final[int] = 2
COMMON_POWER_MAX_POWERS: Final[int] = 2
COMMON_POWER_PREV_LINE_LENGTH_THRESHOLD: Final[int] = 50
COMMON_POWER_CLOSE_MATCH_LENGTH_DIFF: Final[int] = 5
COMMON_POWER_WITHOUT_FUZZY_LENGTH_DIFF: Final[int] = 4
COMMON_POWER_MULTIWORD_START_CHARS: Final[int] = 2
COMMON_POWER_SINGLEWORD_START_CHARS: Final[int] = 2

# Common power description keywords
COMMON_POWER_DESCRIPTION_KEYWORDS: Final[List[str]] = [
    "LEVEL",
    "DESCRIPTION",
    "GAIN",
    "ADD",
    "WHEN",
    "YOU",
    "MAY",
    "INSTEAD",
    "DICE",
    "SUCCESS",
    "ATTACK",
    "MOVE",
    "HEAL",
    "TARGET",
    "SPACE",
    "ROLL",
    "DEAL",
    "TAKE",
    "DRAW",
    "COUNT",
    "NUMBER",
    "EACH",
]

# Common power description keywords in line content
COMMON_POWER_LINE_KEYWORDS: Final[List[str]] = [
    "INSTEAD",
    "WHEN YOU",
    "GAIN",
    "ADD",
    "HEAL",
    "DEAL",
    "COUNT",
    "ATTACK",
]

# Common power previous line ending keywords
COMMON_POWER_PREV_LINE_ENDINGS: Final[List[str]] = [
    "STRESS",
    "WOUND",
    "DICE",
    "SUCCESS",
    "SPACE",
    "TARGET",
]

# Special power region coordinates
# Format: (x_start_percent, y_start_percent, width_percent, height_percent)
SPECIAL_POWER_REGION: Final[Tuple[float, float, float, float]] = (
    0.43,  # X start: 43%
    0.13,  # Y start: 13%
    0.55,  # Width: 55%
    0.25,  # Height: 25%
)

# Special power level widths (as percentage of special power region width)
# These define 4 vertical sub-regions within the special power region
SPECIAL_POWER_LEVEL_WIDTHS: Final[List[float]] = [
    0.32,    # Level 1: 32%
    0.2267,  # Level 2: 22.67%
    0.1987,  # Level 3: 19.87%
    0.2545,  # Level 4: 25.45%
]

# Common power region coordinates
# Format: (x_start_percent, y_start_percent, width_percent, height_percent)
COMMON_POWER_REGIONS: Final[List[Tuple[float, float, float, float]]] = [
    # Region 1: X start at 43%, Y start at 41%, width 55%, height 15%
    # Height increased from 10% to 15% to improve OCR accuracy while still focusing on power names
    (0.43, 0.41, 0.55, 0.15),
    # Region 2: X start at 43%, Y start at 68%, width 55%, height 15%
    # Height increased from 10% to 15% to improve OCR accuracy while still focusing on power names
    (0.43, 0.68, 0.55, 0.15),
]

# Front card region percentages
FRONT_CARD_TOP_PERCENT: Final[float] = 0.25
FRONT_CARD_LOCATION_END_PERCENT: Final[float] = 0.30  # Location region ends at 30%
FRONT_CARD_MOTTO_START_PERCENT: Final[float] = 0.39  # Start slightly below name/location (25%)
FRONT_CARD_MOTTO_END_PERCENT: Final[float] = (
    0.49  # End before story starts (50%), allows for multi-line mottos (height = 10%)
)
FRONT_CARD_STORY_START_PERCENT: Final[float] = 0.50
FRONT_CARD_STORY_HEIGHT_PERCENT: Final[float] = 0.45

# Punctuation characters that indicate continuation
PUNCTUATION_CONTINUATION_CHARS: Final[str] = ":,;.-"

# Quote characters (straight and curly quotes)
# Straight quotes: " (U+0022), ' (U+0027)
# Curly quotes: " (U+201C), " (U+201D), ' (U+2018), ' (U+2019)
QUOTE_CHARACTERS: Final[str] = '"\'\u201c\u201d\u2018\u2019'
