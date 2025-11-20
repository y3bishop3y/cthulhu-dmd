#!/usr/bin/env python3
"""
Shared constants and enums for Cthulhu: Death May Die data processing.

This module provides centralized constants and enums used across multiple scripts.
"""

from enum import Enum
from typing import Final, List


class CommonPower(str, Enum):
    """Common power names in the game."""

    ARCANE_MASTERY = "Arcane Mastery"
    BRAWLING = "Brawling"
    MARKSMAN = "Marksman"
    STEALTH = "Stealth"
    SWIFTNESS = "Swiftness"
    TOUGHNESS = "Toughness"


class ImageType(str, Enum):
    """Types of character card images."""

    FRONT = "front"
    BACK = "back"


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"


class FileExtension(str, Enum):
    """Common file extensions used in the project."""

    JPG = ".jpg"
    JPEG = ".jpeg"
    WEBP = ".webp"
    PNG = ".png"
    PDF = ".pdf"
    JSON = ".json"
    TXT = ".txt"
    YAML = ".yaml"
    YML = ".yml"
    WAV = ".wav"
    MD = ".md"


class Season(str, Enum):
    """Season/box identifiers."""

    SEASON1 = "season1"
    SEASON2 = "season2"
    SEASON3 = "season3"
    SEASON4 = "season4"
    UNSpeakABLE_BOX = "unknowable-box"
    COMIC_BOOK_V2 = "comic-book-v2"


# Constants for file names
class Filename:
    """File name constants used across scripts."""

    FRONT: Final[str] = "front.jpg"
    BACK: Final[str] = "back.jpg"
    CHARACTER_JSON: Final[str] = "character.json"
    STORY_TXT: Final[str] = "story.txt"
    COMMON_POWERS: Final[str] = "common_powers.json"
    TRAITS_BOOKLET: Final[str] = "traits_booklet.pdf"
    CHARACTER_BOOK: Final[str] = "character-book.pdf"
    RULEBOOK: Final[str] = "DMD_Rulebook_web.pdf"
    RULEBOOK_MD: Final[str] = "rulebook.md"
    RULEBOOK_TXT: Final[str] = "rulebook.txt"


# Constants for directory names
class Directory:
    """Directory name constants."""

    DATA: Final[str] = "data"


# Helper functions
def get_common_power_names() -> List[str]:
    """Get list of all common power names as strings."""
    return [power.value for power in CommonPower]


def get_season_names() -> List[str]:
    """Get list of all season names as strings."""
    return [season.value for season in Season]
