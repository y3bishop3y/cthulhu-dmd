#!/usr/bin/env python3
"""
Unit tests for character parsing helper functions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from scripts.models.character_parsing_helpers import (
    extract_motto_from_multiline,
    extract_motto_from_quotes,
    extract_motto_from_single_line,
    fix_story_ocr_errors,
    is_common_power_description_line,
    is_game_rules_line,
    score_story_paragraph,
)


class TestFixStoryOCRErrors:
    """Test fix_story_ocr_errors function."""

    def test_fixes_benchley_variations(self):
        """Test that Benchley name variations are fixed."""
        text = "Benchle's signature eye-twitch"
        result = fix_story_ocr_errors(text)
        assert "Benchley" in result

    def test_fixes_double_y_error(self):
        """Test that double 'y' errors are fixed."""
        text = "Benchleyy's signature"
        result = fix_story_ocr_errors(text)
        assert "Benchley" in result
        assert "Benchleyy" not in result

    def test_fixes_rereserve(self):
        """Test that 'rereserve' is fixed to 'reserve'."""
        text = "He had a rereserve of strength"
        result = fix_story_ocr_errors(text)
        assert "reserve" in result
        assert "rereserve" not in result

    def test_fixes_common_words(self):
        """Test that common OCR word errors are fixed."""
        text = "word ond fallow"
        result = fix_story_ocr_errors(text)
        assert "and" in result
        assert "fellow" in result

    def test_fixes_spacing(self):
        """Test that spacing issues are fixed."""
        text = "word  word"
        result = fix_story_ocr_errors(text)
        assert "  " not in result

    def test_preserves_valid_text(self):
        """Test that valid text is preserved."""
        text = "Lord Benchley's signature eye-twitch is both worrisome and impressive."
        result = fix_story_ocr_errors(text)
        assert "Benchley" in result
        assert "eye-twitch" in result


class TestIsGameRulesLine:
    """Test is_game_rules_line function."""

    def test_detects_your_turn(self):
        """Test detection of 'YOUR TURN'."""
        assert is_game_rules_line("YOUR TURN")
        assert is_game_rules_line("your turn")

    def test_detects_take(self):
        """Test detection of 'TAKE'."""
        assert is_game_rules_line("TAKE ACTIONS")
        assert is_game_rules_line("take actions")

    def test_detects_investigate(self):
        """Test detection of 'INVESTIGATE'."""
        assert is_game_rules_line("INVESTIGATE OR FIGHT!")
        assert is_game_rules_line("investigate or fight")

    def test_rejects_story_text(self):
        """Test that story text is not detected as game rules."""
        assert not is_game_rules_line("Lord Benchley's signature eye-twitch")
        assert not is_game_rules_line("The investigator battled cults for decades")


class TestExtractMottoFromQuotes:
    """Test extract_motto_from_quotes function."""

    def test_extracts_double_quotes(self):
        """Test extraction from double quotes."""
        text = 'The motto is "Shoot first. Never ask."'
        result = extract_motto_from_quotes(text)
        assert result == "Shoot first. Never ask."

    def test_extracts_single_quotes(self):
        """Test extraction from single quotes."""
        text = "The motto is 'Shoot first. Never ask.'"
        result = extract_motto_from_quotes(text)
        assert result == "Shoot first. Never ask."

    def test_requires_motto_keywords(self):
        """Test that mottos must contain keywords."""
        text = 'Some random quote "Hello world"'
        result = extract_motto_from_quotes(text)
        assert result is None

    def test_returns_none_if_no_quotes(self):
        """Test that None is returned if no quotes found."""
        text = "No quotes here"
        result = extract_motto_from_quotes(text)
        assert result is None


class TestExtractMottoFromMultiline:
    """Test extract_motto_from_multiline function."""

    def test_extracts_two_line_motto(self):
        """Test extraction of two-line motto."""
        lines = [
            "CHARACTER NAME",
            "LOCATION",
            "Shoot first.",
            "Never ask.",
            "Story text here...",
        ]
        result = extract_motto_from_multiline(lines)
        assert result is not None
        assert "Shoot" in result
        assert "ask" in result

    def test_requires_keywords(self):
        """Test that keywords are required."""
        lines = ["CHARACTER NAME", "LOCATION", "Some text", "More text"]
        result = extract_motto_from_multiline(lines)
        assert result is None

    def test_skips_all_caps(self):
        """Test that all-caps lines are skipped."""
        lines = ["CHARACTER NAME", "LOCATION", "ALL CAPS TEXT", "MORE TEXT"]
        result = extract_motto_from_multiline(lines)
        assert result is None


class TestExtractMottoFromSingleLine:
    """Test extract_motto_from_single_line function."""

    def test_extracts_single_line_motto(self):
        """Test extraction of single-line motto."""
        lines = [
            "CHARACTER NAME",
            "LOCATION",
            "Shoot first. Never ask.",
            "Story text here...",
        ]
        result = extract_motto_from_single_line(lines, "Character Name", "Location")
        assert result is not None
        assert "Shoot" in result

    def test_skips_name_and_location(self):
        """Test that name and location are skipped."""
        lines = ["CHARACTER NAME", "LOCATION", "Story text"]
        result = extract_motto_from_single_line(lines, "Character Name", "Location")
        assert result is None

    def test_requires_keywords(self):
        """Test that keywords are required."""
        lines = ["CHARACTER NAME", "LOCATION", "Some random text"]
        result = extract_motto_from_single_line(lines, None, None)
        assert result is None


class TestScoreStoryParagraph:
    """Test score_story_paragraph function."""

    def test_scores_long_paragraphs_higher(self):
        """Test that longer paragraphs score higher."""
        para1 = "Short text."
        para2 = "This is a much longer paragraph with many words that should score higher than the short one."
        score1 = score_story_paragraph(para1, None, None, None)
        score2 = score_story_paragraph(para2, None, None, None)
        assert score2 > score1

    def test_penalizes_ocr_errors(self):
        """Test that OCR errors reduce score."""
        para1 = "This is a longer paragraph with clean text without errors that should score well."
        para2 = "This is a longer paragraph with text containing @#$%^&*|~` OCR errors that should score lower."
        score1 = score_story_paragraph(para1, None, None, None)
        score2 = score_story_paragraph(para2, None, None, None)
        assert score1 > score2

    def test_bonuses_story_keywords(self):
        """Test that story keywords increase score."""
        para1 = "This is a longer paragraph with some text that should score reasonably well."
        para2 = "This is a longer paragraph about the investigator's signature warning thoughts demeanor and how they battled cults for decades."
        score1 = score_story_paragraph(para1, None, None, None)
        score2 = score_story_paragraph(para2, None, None, None)
        assert score2 > score1

    def test_penalizes_game_rules(self):
        """Test that game rules are heavily penalized."""
        para = "YOUR TURN TAKE ACTIONS DRAW MYTHOS"
        score = score_story_paragraph(para, None, None, None)
        assert score < 0

    def test_excludes_name_location_motto(self):
        """Test that paragraphs containing name/location/motto are excluded."""
        para = "Character Name's story"
        score = score_story_paragraph(para, "Character Name", None, None)
        assert score < 0


class TestIsCommonPowerDescriptionLine:
    """Test is_common_power_description_line function."""

    def test_detects_long_lines(self):
        """Test that long lines are detected as descriptions."""
        line = "A" * 100  # Very long line
        assert is_common_power_description_line(line)

    def test_detects_description_keywords(self):
        """Test that lines with description keywords are detected."""
        assert is_common_power_description_line("LEVEL 1: Gain dice")
        assert is_common_power_description_line("WHEN YOU ATTACK")

    def test_allows_short_power_names(self):
        """Test that short power names are not detected as descriptions."""
        assert not is_common_power_description_line("Brawling")
        assert not is_common_power_description_line("Swiftness")

