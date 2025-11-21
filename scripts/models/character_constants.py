#!/usr/bin/env python3
"""
Constants for character parsing and OCR.

Centralizes keyword lists, patterns, and thresholds used throughout
character data parsing and OCR text processing.
"""

from typing import Final, List

# Motto detection keywords
MOTTO_KEYWORDS: Final[List[str]] = [
    "first",
    "never",
    "always",
    "shoot",
    "ask",
    "trust",
    "certain",
    "life",
]

MOTTO_START_KEYWORDS: Final[List[str]] = [
    "shoot",
    "never",
    "always",
    "first",
    "trust",
    "certain",
]

MOTTO_END_KEYWORDS: Final[List[str]] = [
    "ask",
    "never",
    "always",
    "trust",
    "certain",
    "life",
    "things",
]

# Quote patterns for motto extraction
MOTTO_QUOTE_PATTERNS: Final[List[str]] = [
    r'"([^"]+)"',  # Standard quotes
    r"'([^']+)'",  # Single quotes
    r'["\']([^"\']+)["\']',  # Any quote type
]

# Story detection keywords
STORY_COMMON_WORDS: Final[List[str]] = [
    "the",
    "and",
    "of",
    "to",
    "a",
    "in",
    "is",
    "it",
    "that",
    "for",
    "his",
    "but",
    "most",
]

STORY_KEYWORDS: Final[List[str]] = [
    "signature",
    "warning",
    "thoughts",
    "demeanor",
    "investigators",
    "reserve",
    "fellow",
    "glare",
    "battled",
    "cults",
    "decades",
    "maintaining",
]

# Game rules keywords (to filter out from story)
GAME_RULES_KEYWORDS: Final[List[str]] = [
    "YOUR",
    "TURN",
    "TAKE",
    "ACTIONS",
    "DRAW",
    "MYTHOS",
    "INVESTIGATE",
    "FIGHT",
]

GAME_RULES_LINE_KEYWORDS: Final[List[str]] = [
    "YOUR TURN",
    "TAKE",
    "DRAW MYTHOS",
    "INVESTIGATE",
    "FIGHT",
    "RESOLVE",
    "OR FIGHT!",
    "INVESTIGATE OR FIGHT!",
]

# Power parsing keywords
POWER_ACTION_PATTERNS: Final[List[str]] = [
    "when you run",
    "when attacking",
    "when you attack",
    "when attacked",
    "during a run",
    "you may",
    "deal",
    "wound",
    "heal",
    "stress",
    "move",
    "additional",
    "sneak",
    "free",
    "reroll",
]

POWER_DESCRIPTION_KEYWORDS: Final[List[str]] = [
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
]

# Story parsing thresholds
STORY_MIN_LENGTH: Final[int] = 80
STORY_MIN_WORD_COUNT: Final[int] = 2
MOTTO_MIN_LENGTH: Final[int] = 5
MOTTO_MAX_LENGTH: Final[int] = 150
MOTTO_REASONABLE_MIN: Final[int] = 10
MOTTO_REASONABLE_MAX: Final[int] = 100
MOTTO_MAX_WORDS_SINGLE_LINE: Final[int] = 5
MOTTO_MAX_WORDS_MULTI_LINE: Final[int] = 8
MOTTO_CHECK_LINES: Final[int] = 15
MOTTO_CHECK_LINES_SINGLE: Final[int] = 20

# Name/location parsing thresholds
NAME_MIN_LENGTH: Final[int] = 5
NAME_MAX_LENGTH: Final[int] = 60
LOCATION_MAX_LENGTH: Final[int] = 60

# Power level parsing
MAX_POWER_LEVELS: Final[int] = 4
MIN_POWER_DESCRIPTION_WORDS: Final[int] = 2

# Common power detection thresholds
COMMON_POWER_LINE_MAX_LENGTH: Final[int] = 60
COMMON_POWER_FUZZY_THRESHOLD: Final[float] = 85.0
COMMON_POWER_LENGTH_TOLERANCE: Final[int] = 10
