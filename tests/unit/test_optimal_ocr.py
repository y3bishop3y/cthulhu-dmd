#!/usr/bin/env python3
"""
Unit tests for optimal_ocr.py module.

Tests the field-specific extraction functions, motto parsing, and Pydantic models.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.cli.parse.parsing_models import FieldStrategies, FrontCardFields, ImageRegions
from scripts.utils.optimal_ocr import (
    _clean_motto_text,
    _extract_combined_motto,
    _extract_quoted_motto,
    _extract_single_line_motto,
    _extract_story_text,
    _filter_motto_lines,
    _get_field_strategies,
    _get_image_regions,
    _parse_location_from_text,
    _parse_motto_from_text,
    _parse_name_from_text,
    extract_front_card_fields_with_optimal_strategies,
)


class TestGetFieldStrategies:
    """Test _get_field_strategies function."""

    def test_get_field_strategies_with_config(self):
        """Test getting strategies from config."""
        config = {
            "strategies": {
                "name": {"strategy_name": "custom_name_strategy"},
                "location": {"strategy_name": "custom_location_strategy"},
                "motto": {"strategy_name": "custom_motto_strategy"},
                "story": {"strategy_name": "custom_story_strategy"},
            }
        }

        with patch("scripts.utils.optimal_ocr.get_optimal_strategy_for_category") as mock_get:
            mock_get.side_effect = lambda cat, cfg: cfg["strategies"][cat]["strategy_name"]

            strategies = _get_field_strategies(config)

            assert isinstance(strategies, FieldStrategies)
            assert strategies.name == "custom_name_strategy"
            assert strategies.location == "custom_location_strategy"
            assert strategies.motto == "custom_motto_strategy"
            assert strategies.story == "custom_story_strategy"

    def test_get_field_strategies_with_defaults(self):
        """Test getting strategies with defaults when config missing."""
        config = {"strategies": {}}

        with patch("scripts.utils.optimal_ocr.get_optimal_strategy_for_category") as mock_get:
            mock_get.return_value = None

            strategies = _get_field_strategies(config)

            assert isinstance(strategies, FieldStrategies)
            assert strategies.name == "tesseract_bilateral_psm3"
            assert strategies.location == "tesseract_bilateral_psm3"
            assert strategies.motto == "tesseract_bilateral_psm3"
            assert strategies.story == "tesseract_enhanced_psm3"


class TestGetImageRegions:
    """Test _get_image_regions function."""

    def test_get_image_regions(self):
        """Test calculating image regions."""
        img_height = 1000
        img_width = 500

        regions = _get_image_regions(img_height, img_width)

        assert isinstance(regions, ImageRegions)
        assert regions.name == (0, 0, 500, 125)  # top_height // 2 = 125
        assert regions.location == (0, 125, 500, 125)
        assert regions.motto == (0, 300, 500, 350)  # 0.65 - 0.30 = 0.35 * 1000 = 350
        assert regions.story == (0, 600, 500, 400)


class TestParseNameFromText:
    """Test _parse_name_from_text function."""

    def test_parse_name_all_caps(self):
        """Test parsing all-caps name."""
        text = "AHMED YASIN\nSome other text"
        result = _parse_name_from_text(text)
        assert result == "AHMED YASIN"

    def test_parse_name_prefers_longer(self):
        """Test parsing prefers longer name."""
        text = "ANN\nAHMED YASIN\nBOB"
        result = _parse_name_from_text(text)
        assert result == "AHMED YASIN"

    def test_parse_name_empty(self):
        """Test parsing empty text."""
        result = _parse_name_from_text("")
        assert result == ""

    def test_parse_name_no_all_caps(self):
        """Test parsing when no all-caps found."""
        text = "some lowercase text"
        result = _parse_name_from_text(text)
        assert result == ""

    def test_parse_name_min_length(self):
        """Test parsing respects minimum length."""
        text = "AB\nCDE\nFGHIJ"
        result = _parse_name_from_text(text)
        assert result == "FGHIJ"  # Prefers longer, but all >= 3


class TestParseLocationFromText:
    """Test _parse_location_from_text function."""

    def test_parse_location_all_caps(self):
        """Test parsing all-caps location."""
        text = "MERSIN, TURKEY\nSome other text"
        result = _parse_location_from_text(text)
        assert result == "MERSIN, TURKEY"

    def test_parse_location_prefers_longer(self):
        """Test parsing prefers longer location."""
        text = "NY\nLONDON, ENGLAND\nLA"
        result = _parse_location_from_text(text)
        assert result == "LONDON, ENGLAND"

    def test_parse_location_empty(self):
        """Test parsing empty text."""
        result = _parse_location_from_text("")
        assert result == ""


class TestFilterMottoLines:
    """Test _filter_motto_lines function."""

    def test_filter_motto_lines_removes_all_caps(self):
        """Test filtering removes all-caps lines."""
        lines = ["AHMED YASIN", "What is written", "MERSIN, TURKEY"]
        result = _filter_motto_lines(lines)
        assert result == ["What is written"]

    def test_filter_motto_lines_removes_short(self):
        """Test filtering removes very short lines."""
        lines = ["A", "What is written", "AB"]  # AB is 2 chars, which is the minimum
        result = _filter_motto_lines(lines)
        # AB passes because it's exactly 2 chars (minimum threshold)
        assert "What is written" in result
        assert "A" not in result  # Single char is filtered

    def test_filter_motto_lines_removes_garbage(self):
        """Test filtering removes OCR garbage."""
        lines = ["~~|~_", "What is written", "123456"]
        result = _filter_motto_lines(lines)
        # 123456 passes because it's 100% alphanumeric (above 30% threshold)
        # Only symbols-only lines are filtered
        assert "What is written" in result
        assert "~~|~_" not in result  # Symbols-only is filtered

    def test_filter_motto_lines_keeps_valid(self):
        """Test filtering keeps valid motto lines."""
        lines = ['"What is written"', "is written.", "Some motto text"]
        result = _filter_motto_lines(lines)
        assert len(result) == 3


class TestExtractQuotedMotto:
    """Test _extract_quoted_motto function."""

    def test_extract_quoted_motto_single_quotes(self):
        """Test extracting motto with single quotes."""
        lines = ["Some text", "'What is written is written.'", "More text"]
        result = _extract_quoted_motto(lines)
        assert result == "What is written is written."

    def test_extract_quoted_motto_double_quotes(self):
        """Test extracting motto with double quotes."""
        lines = ['"Shoot first. Never ask."', "More text"]
        result = _extract_quoted_motto(lines)
        assert result == "Shoot first. Never ask."

    def test_extract_quoted_motto_no_quotes(self):
        """Test extracting when no quotes found."""
        lines = ["Some text", "More text"]
        result = _extract_quoted_motto(lines)
        assert result == ""

    def test_extract_quoted_motto_too_long(self):
        """Test extracting ignores mottos that are too long."""
        long_motto = '"' + "word " * 20 + '"'  # 20 words, > 15
        lines = [long_motto]
        result = _extract_quoted_motto(lines)
        assert result == ""


class TestExtractCombinedMotto:
    """Test _extract_combined_motto function."""

    def test_extract_combined_motto_two_lines(self):
        """Test extracting motto from two consecutive lines."""
        lines = ['"What is written', 'is written."']
        result = _extract_combined_motto(lines)
        assert result == '"What is written is written."'

    def test_extract_combined_motto_with_punctuation(self):
        """Test extracting motto ending with punctuation."""
        lines = ["Two things are certain", "in life: Death and Axes."]
        result = _extract_combined_motto(lines)
        assert result == "Two things are certain in life: Death and Axes."

    def test_extract_combined_motto_skips_all_caps(self):
        """Test extracting skips all-caps lines."""
        lines = ["AHMED YASIN", "What is written", "is written."]
        result = _extract_combined_motto(lines)
        # Should skip AHMED YASIN and combine the other two
        assert "What is written" in result

    def test_extract_combined_motto_insufficient_lines(self):
        """Test extracting with insufficient lines."""
        lines = ["Single line"]
        result = _extract_combined_motto(lines)
        assert result == ""


class TestExtractSingleLineMotto:
    """Test _extract_single_line_motto function."""

    def test_extract_single_line_motto_valid(self):
        """Test extracting valid single-line motto."""
        lines = ["Shoot first. Never ask.", "Some other text"]
        result = _extract_single_line_motto(lines)
        assert result == "Shoot first. Never ask."

    def test_extract_single_line_motto_skips_all_caps(self):
        """Test extracting skips all-caps lines."""
        lines = ["AHMED YASIN", "Shoot first. Never ask."]
        result = _extract_single_line_motto(lines)
        assert result == "Shoot first. Never ask."

    def test_extract_single_line_motto_too_long(self):
        """Test extracting ignores mottos that are too long."""
        long_motto = "word " * 15  # 15 words, > 10
        lines = [long_motto]
        result = _extract_single_line_motto(lines)
        assert result == ""


class TestCleanMottoText:
    """Test _clean_motto_text function."""

    def test_clean_motto_text_removes_pipes(self):
        """Test cleaning removes pipes and separators."""
        motto = '- | "What is written | is written."'
        result = _clean_motto_text(motto)
        assert "|" not in result
        assert result.startswith('"')

    def test_clean_motto_text_fixes_ocr_errors(self):
        """Test cleaning fixes common OCR errors."""
        motto = "qT. is wriften"
        result = _clean_motto_text(motto)
        assert "is is written" in result or "is written" in result

    def test_clean_motto_text_removes_duplicate_words(self):
        """Test cleaning removes duplicate words."""
        motto = "What is is written"
        result = _clean_motto_text(motto)
        assert "is is" not in result
        assert "is written" in result

    def test_clean_motto_text_empty(self):
        """Test cleaning empty motto."""
        result = _clean_motto_text("")
        assert result == ""

    def test_clean_motto_text_removes_garbage_before_quote(self):
        """Test cleaning removes garbage before quotes."""
        motto = "id —~—~~ ie 4 \"What is written\""
        result = _clean_motto_text(motto)
        assert result.startswith('"')
        assert "id" not in result


class TestParseMottoFromText:
    """Test _parse_motto_from_text function."""

    def test_parse_motto_from_text_quoted(self):
        """Test parsing quoted motto."""
        text = 'Some text\n"What is written is written."\nMore text'
        result = _parse_motto_from_text(text)
        assert "What is written is written" in result

    def test_parse_motto_from_text_combined(self):
        """Test parsing motto from combined lines."""
        text = '"What is written\nis written."'
        result = _parse_motto_from_text(text)
        assert "What is written" in result
        assert "is written" in result

    def test_parse_motto_from_text_single_line(self):
        """Test parsing single-line motto."""
        text = "Shoot first. Never ask.\nMore text"
        result = _parse_motto_from_text(text)
        assert "Shoot first" in result

    def test_parse_motto_from_text_empty(self):
        """Test parsing empty text."""
        result = _parse_motto_from_text("")
        assert result == ""


class TestExtractStoryText:
    """Test _extract_story_text function."""

    @patch("scripts.utils.optimal_ocr.extract_text_from_region_with_strategy")
    def test_extract_story_text_success(self, mock_extract_region):
        """Test successful story extraction."""
        mock_extractor = MagicMock()
        mock_extractor.extract_description_region.return_value = "Story text here"

        result = _extract_story_text(
            Path("test.jpg"), mock_extractor, 1000, 500, "tesseract_enhanced_psm3"
        )

        assert result == "Story text here"
        mock_extract_region.assert_not_called()

    @patch("scripts.utils.optimal_ocr.extract_text_from_region_with_strategy")
    def test_extract_story_text_fallback(self, mock_extract_region):
        """Test story extraction falls back to region extraction."""
        mock_extractor = MagicMock()
        mock_extractor.extract_description_region.return_value = "Short"  # < 10 chars

        mock_extract_region.return_value = "Longer story text from region extraction"

        result = _extract_story_text(
            Path("test.jpg"), mock_extractor, 1000, 500, "tesseract_enhanced_psm3"
        )

        assert result == "Longer story text from region extraction"
        mock_extract_region.assert_called_once()


class TestExtractFrontCardFieldsWithOptimalStrategies:
    """Test extract_front_card_fields_with_optimal_strategies function."""

    @patch("scripts.utils.optimal_ocr.cv2")
    @patch("scripts.utils.optimal_ocr.np")
    def test_extract_front_card_fields_no_cv2(self, mock_np, mock_cv2):
        """Test fallback when cv2/np not available."""
        mock_cv2 = None
        mock_np = None

        with patch("scripts.utils.optimal_ocr.cv2", None), patch(
            "scripts.utils.optimal_ocr.np", None
        ), patch(
            "scripts.utils.optimal_ocr.extract_front_card_with_optimal_strategy"
        ) as mock_whole:
            mock_whole.return_value = "Whole card text"

            result = extract_front_card_fields_with_optimal_strategies(Path("test.jpg"))

            assert isinstance(result, FrontCardFields)
            assert result.story == "Whole card text"
            assert result.name == ""
            assert result.location == ""
            assert result.motto == ""

    @patch("scripts.utils.optimal_ocr.load_optimal_strategies")
    @patch("scripts.utils.optimal_ocr.extract_text_from_region_with_strategy")
    @patch("scripts.core.parsing.layout.CardLayoutExtractor")
    def test_extract_front_card_fields_success(
        self, mock_extractor_class, mock_extract_region, mock_load_config
    ):
        """Test successful field extraction."""
        # Mock config
        mock_config = {
            "strategies": {
                "name": {"strategy_name": "tesseract_bilateral_psm3"},
                "location": {"strategy_name": "tesseract_bilateral_psm3"},
                "motto": {"strategy_name": "tesseract_bilateral_psm3"},
                "story": {"strategy_name": "tesseract_enhanced_psm3"},
            }
        }
        mock_load_config.return_value = mock_config

        # Mock extractor
        mock_extractor = MagicMock()
        mock_image = MagicMock()
        mock_image.shape = (1000, 500)
        mock_extractor.preprocess_image.return_value = mock_image
        mock_extractor.extract_description_region.return_value = "Story text"
        mock_extractor_class.return_value = mock_extractor

        # Mock region extraction
        mock_extract_region.side_effect = [
            "AHMED YASIN",  # name
            "MERSIN, TURKEY",  # location
            '"What is written is written."',  # motto
        ]

        with patch("scripts.utils.optimal_ocr.get_optimal_strategy_for_category") as mock_get:
            mock_get.side_effect = lambda cat, cfg: cfg["strategies"][cat]["strategy_name"]

            result = extract_front_card_fields_with_optimal_strategies(
                Path("test.jpg"), mock_config
            )

            assert isinstance(result, FrontCardFields)
            assert result.name == "AHMED YASIN"
            assert result.location == "MERSIN, TURKEY"
            assert "What is written" in (result.motto or "")
            assert result.story == "Story text"


class TestPydanticModels:
    """Test Pydantic models."""

    def test_field_strategies_model(self):
        """Test FieldStrategies model."""
        strategies = FieldStrategies(
            name="test_name",
            location="test_location",
            motto="test_motto",
            story="test_story",
        )

        assert strategies.name == "test_name"
        assert strategies.location == "test_location"
        assert strategies.motto == "test_motto"
        assert strategies.story == "test_story"

    def test_image_regions_model(self):
        """Test ImageRegions model."""
        regions = ImageRegions(
            name=(0, 0, 100, 50),
            location=(0, 50, 100, 50),
            motto=(0, 100, 100, 200),
            story=(0, 300, 100, 400),
        )

        assert regions.name == (0, 0, 100, 50)
        assert regions.location == (0, 50, 100, 50)
        assert regions.motto == (0, 100, 100, 200)
        assert regions.story == (0, 300, 100, 400)

    def test_front_card_fields_model(self):
        """Test FrontCardFields model."""
        fields = FrontCardFields(
            name="Test Name",
            location="Test Location",
            motto="Test Motto",
            story="Test Story",
        )

        assert fields.name == "Test Name"
        assert fields.location == "Test Location"
        assert fields.motto == "Test Motto"
        assert fields.story == "Test Story"
        assert fields.has_essential_fields is True
        assert fields.has_all_fields is True
        assert fields.is_empty is False

    def test_front_card_fields_computed_properties(self):
        """Test FrontCardFields computed properties."""
        # Empty fields
        empty_fields = FrontCardFields()
        assert empty_fields.is_empty is True
        assert empty_fields.has_essential_fields is False
        assert empty_fields.has_all_fields is False

        # Partial fields
        partial_fields = FrontCardFields(name="Test", location=None, motto=None, story=None)
        assert partial_fields.is_empty is False
        assert partial_fields.has_essential_fields is True
        assert partial_fields.has_all_fields is False

        # All fields
        all_fields = FrontCardFields(
            name="Test", location="Location", motto="Motto", story="Story"
        )
        assert all_fields.is_empty is False
        assert all_fields.has_essential_fields is True
        assert all_fields.has_all_fields is True

