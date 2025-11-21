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

# Common power region coordinates
# Format: (x_start_percent, y_start_percent, width_percent, height_percent)
COMMON_POWER_REGIONS: Final[List[Tuple[float, float, float, float]]] = [
    # Region 1: Right side, upper-middle (most common layout)
    (0.55, 0.20, 0.40, 0.55),
    # Region 2: Middle-right, slightly lower
    (0.50, 0.25, 0.45, 0.60),
    # Region 3: Right side, broader coverage
    (0.60, 0.15, 0.35, 0.65),
]

# Front card region percentages
FRONT_CARD_TOP_PERCENT: Final[float] = 0.25
FRONT_CARD_MOTTO_START_PERCENT: Final[float] = 0.26  # Start slightly below name/location (25%)
FRONT_CARD_MOTTO_END_PERCENT: Final[float] = (
    0.48  # End before story starts (60%), allows for multi-line mottos
)
FRONT_CARD_STORY_START_PERCENT: Final[float] = 0.60
FRONT_CARD_STORY_HEIGHT_PERCENT: Final[float] = 0.40

# Punctuation characters that indicate continuation
PUNCTUATION_CONTINUATION_CHARS: Final[str] = ":,;.-"
