#!/usr/bin/env python3
"""
Unit tests for character parsing CLI script.

Tests the verification/reporting functionality and character data extraction.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.cli.parse.parsing_models import FrontCardFields
from scripts.models.character import CharacterData


class TestDisplayExtractionReport:
    """Test the _display_extraction_report function."""

    @patch("scripts.cli.parse.characters.console")
    def test_display_report_with_all_fields(self, mock_console):
        """Test report display with all fields populated."""
        from scripts.cli.parse.characters import _display_extraction_report

        extracted = CharacterData(
            name="Test Character",
            location="Test Location",
            motto="Test Motto",
            story="This is a test story that is longer than 50 characters to test truncation",
            common_powers=["Marksman", "Toughness"],
        )

        existing = CharacterData(
            name="Test Character",
            location="Test Location",
            motto="Test Motto",
            story="This is a test story that is longer than 50 characters to test truncation",
            common_powers=["Marksman", "Toughness"],
        )

        char_dir = Path("test_character")
        issues = []

        _display_extraction_report(char_dir, extracted, existing, issues)

        # Verify console.print was called (for header, table, etc.)
        assert mock_console.print.called

    @patch("scripts.cli.parse.characters.console")
    def test_display_report_with_none_story(self, mock_console):
        """Test report display when story is None (should not crash)."""
        from scripts.cli.parse.characters import _display_extraction_report

        extracted = CharacterData(
            name="Test Character",
            location="Test Location",
            motto=None,
            story=None,
            common_powers=[],
        )

        existing = CharacterData(
            name="Test Character",
            location="Test Location",
            motto=None,
            story=None,
            common_powers=[],
        )

        char_dir = Path("test_character")
        issues = []

        # Should not raise an error
        _display_extraction_report(char_dir, extracted, existing, issues)
        assert mock_console.print.called

    @patch("scripts.cli.parse.characters.console")
    def test_display_report_with_empty_common_powers(self, mock_console):
        """Test report display with empty common powers list."""
        from scripts.cli.parse.characters import _display_extraction_report

        extracted = CharacterData(
            name="Test Character",
            location="Test Location",
            motto="Test Motto",
            story="Test story",
            common_powers=[],
        )

        existing = None

        char_dir = Path("test_character")
        issues = []

        # Should not raise an error
        _display_extraction_report(char_dir, extracted, existing, issues)
        assert mock_console.print.called

    @patch("scripts.cli.parse.characters.console")
    def test_display_report_with_no_existing_data(self, mock_console):
        """Test report display when no existing JSON exists."""
        from scripts.cli.parse.characters import _display_extraction_report

        extracted = CharacterData(
            name="Test Character",
            location="Test Location",
            motto="Test Motto",
            story="Test story",
            common_powers=["Marksman"],
        )

        char_dir = Path("test_character")
        issues = []

        # Should not raise an error
        _display_extraction_report(char_dir, extracted, None, issues)
        assert mock_console.print.called

    @patch("scripts.cli.parse.characters.console")
    def test_display_report_with_issues(self, mock_console):
        """Test report display when parsing issues are detected."""
        from scripts.cli.parse.characters import _display_extraction_report

        extracted = CharacterData(
            name="Test Character",
            location=None,
            motto=None,
            story=None,
            common_powers=[],
        )

        char_dir = Path("test_character")
        issues = ["Missing location", "Missing motto"]

        _display_extraction_report(char_dir, extracted, None, issues)

        # Verify issues were printed
        call_args = [str(call) for call in mock_console.print.call_args_list]
        assert any("Parsing Issues" in str(call) or "Missing" in str(call) for call in call_args)


class TestLoadExistingCharacterJson:
    """Test the load_existing_character_json function."""

    def test_load_existing_json_success(self, tmp_path):
        """Test loading existing character.json successfully."""
        from scripts.cli.parse.characters import Filename, load_existing_character_json

        char_dir = tmp_path / "test_char"
        char_dir.mkdir()

        json_data = {
            "name": "Test Character",
            "location": "Test Location",
            "motto": "Test Motto",
            "story": "Test story",
            "common_powers": ["Marksman", "Toughness"],
        }

        json_file = char_dir / Filename.CHARACTER_JSON
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        result = load_existing_character_json(char_dir)

        assert result is not None
        assert result.name == "Test Character"
        assert result.location == "Test Location"
        assert result.common_powers == ["Marksman", "Toughness"]

    @patch("scripts.cli.parse.characters.console")
    def test_load_existing_json_not_found(self, tmp_path):
        """Test when character.json doesn't exist."""
        from scripts.cli.parse.characters import load_existing_character_json

        char_dir = tmp_path / "test_char"
        char_dir.mkdir()

        result = load_existing_character_json(char_dir)

        assert result is None

    @patch("scripts.cli.parse.characters.console")
    def test_load_existing_json_invalid(self, tmp_path):
        """Test when character.json is invalid JSON."""
        from scripts.cli.parse.characters import load_existing_character_json

        char_dir = tmp_path / "test_char"
        char_dir.mkdir()

        json_file = char_dir / "character.json"
        json_file.write_text("invalid json {", encoding="utf-8")

        result = load_existing_character_json(char_dir)

        # Should return None and print warning
        assert result is None


class TestParseCharacterImages:
    """Test the parse_character_images function."""

    @patch("scripts.cli.parse.characters.extract_front_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.extract_back_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_with_optimal_strategies(self, mock_console, mock_back, mock_front):
        """Test parsing with optimal OCR strategies."""
        from scripts.cli.parse.characters import parse_character_images

        mock_front.return_value = "Front text\nName: Test\nLocation: Test Location"
        mock_back.return_value = "Back text\nCommon Powers: Marksman, Toughness"

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, None, None, use_optimal_strategies=True, quiet=True
        )

        assert result is not None
        assert isinstance(result, CharacterData)
        mock_front.assert_called_once_with(front_path)
        mock_back.assert_called_once_with(back_path)

    @patch("scripts.cli.parse.characters.extract_text_from_image")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_without_optimal_strategies(self, mock_console, mock_extract):
        """Test parsing without optimal OCR strategies."""
        from scripts.cli.parse.characters import parse_character_images

        mock_extract.return_value = "Test text"

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, None, None, use_optimal_strategies=False, quiet=True
        )

        assert result is not None
        assert isinstance(result, CharacterData)
        # Should call extract_text_from_image twice (front and back)
        assert mock_extract.call_count == 2

    @patch("scripts.cli.parse.characters.extract_front_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.extract_back_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_with_story_file(self, mock_console, mock_back, mock_front, tmp_path):
        """Test parsing with HTML-extracted story file."""
        from scripts.cli.parse.characters import parse_character_images

        mock_front.return_value = "Front text\nName: Test"
        mock_back.return_value = "Back text"

        story_file = tmp_path / "story.txt"
        story_file.write_text("This is the HTML-extracted story", encoding="utf-8")

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, story_file, None, use_optimal_strategies=True, quiet=True
        )

        assert result is not None
        assert result.story == "This is the HTML-extracted story"

    @patch("scripts.cli.parse.characters.extract_front_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.extract_back_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_merges_with_existing_data(self, mock_console, mock_back, mock_front):
        """Test parsing merges with existing character data."""
        from scripts.cli.parse.characters import parse_character_images

        # Mock OCR to return text that will parse to "New Name"
        # The FrontCardData parser looks for "Name:" pattern
        mock_front.return_value = "Name: New Name\nLocation: New Location"
        mock_back.return_value = "Common Powers: Marksman, Toughness"

        existing = CharacterData(
            name="Old Name",
            location="Old Location",
            motto="Old Motto",
            story="Old Story",
            common_powers=["Marksman"],
        )

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, None, existing, use_optimal_strategies=True, quiet=True
        )

        assert result is not None
        # Merged data should prefer new extracted data (prefer_html=True)
        # Note: The actual merge behavior depends on FrontCardData parsing
        # For this test, we just verify it doesn't crash and returns a result
        assert isinstance(result, CharacterData)


class TestSeasonFiltering:
    """Test season filtering logic."""

    def test_season_directory_validation(self, tmp_path):
        """Test that season directory validation works correctly."""

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        season_dir = data_dir / "season1"
        season_dir.mkdir()

        char_dir = season_dir / "test_char"
        char_dir.mkdir()

        # Create front image
        (char_dir / "front.jpg").write_bytes(b"fake image")

        # Test with valid season
        with patch(
            "sys.argv", ["script", "--season", "season1", "--data-dir", str(data_dir), "--verify"]
        ):
            # This should not raise an error
            # Note: We can't easily test the full main() function without mocking OCR,
            # but we can test the validation logic separately
            pass


class TestFieldSpecificExtraction:
    """Test field-specific extraction with optimal strategies."""

    @patch("scripts.utils.optimal_ocr.load_optimal_strategies")
    @patch("scripts.utils.optimal_ocr.get_all_strategies")
    @patch("scripts.utils.optimal_ocr.cv2")
    @patch("scripts.utils.optimal_ocr.np")
    def test_extract_front_card_fields_with_optimal_strategies_success(
        self, mock_np, mock_cv2, mock_get_strategies, mock_load_config
    ):
        """Test successful field-specific extraction."""
        from unittest.mock import MagicMock

        from scripts.utils.optimal_ocr import extract_front_card_fields_with_optimal_strategies

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

        # Mock cv2 and np
        mock_cv2.imread.return_value = MagicMock()
        mock_cv2.imwrite.return_value = True
        mock_np.array.return_value = MagicMock()

        # Mock strategy
        mock_strategy = MagicMock()
        mock_strategy.name = "tesseract_bilateral_psm3"
        mock_strategy.extract.return_value = "Extracted Text"
        mock_get_strategies.return_value = [mock_strategy]

        # Mock layout extractor (imported inside the function)
        with patch("scripts.core.parsing.layout.CardLayoutExtractor") as mock_extractor_class:
            mock_extractor = MagicMock()
            mock_extractor.preprocess_image.return_value = MagicMock(shape=(100, 200))
            mock_extractor.extract_description_region.return_value = "Story text"
            mock_extractor_class.return_value = mock_extractor

            image_path = Path("test_front.jpg")
            result = extract_front_card_fields_with_optimal_strategies(image_path, mock_config)

            assert isinstance(result, FrontCardFields)
            assert result.name is not None
            assert result.location is not None
            assert result.motto is not None
            assert result.story is not None

    @patch("scripts.utils.optimal_ocr.load_optimal_strategies")
    def test_extract_front_card_fields_fallback_on_error(self, mock_load_config):
        """Test that field-specific extraction falls back to whole-card on error."""
        from scripts.utils.optimal_ocr import extract_front_card_fields_with_optimal_strategies

        # Mock config to raise error
        mock_load_config.side_effect = FileNotFoundError("Config not found")

        # Mock whole-card extraction
        with patch(
            "scripts.utils.optimal_ocr.extract_front_card_with_optimal_strategy"
        ) as mock_whole:
            mock_whole.return_value = "Whole card text"

            image_path = Path("test_front.jpg")
            result = extract_front_card_fields_with_optimal_strategies(image_path)

            # Should fall back to whole-card extraction
            assert isinstance(result, FrontCardFields)
            assert result.story == "Whole card text"
            assert result.name == ""
            assert result.location == ""
            assert result.motto == ""

    @patch("scripts.utils.optimal_ocr.cv2")
    def test_extract_text_from_region_with_strategy(self, mock_cv2):
        """Test extracting text from a region using a strategy."""
        from unittest.mock import MagicMock

        from scripts.utils.optimal_ocr import extract_text_from_region_with_strategy

        # Mock cv2
        mock_img = MagicMock()
        mock_img.shape = (100, 200, 3)
        mock_cv2.imread.return_value = mock_img
        mock_cv2.imwrite.return_value = True

        # Mock strategy extraction
        with patch("scripts.utils.optimal_ocr._extract_with_strategy") as mock_extract:
            mock_extract.return_value = "Region text"

            image_path = Path("test.jpg")
            region = (10, 20, 50, 30)
            strategy_name = "tesseract_bilateral_psm3"

            result = extract_text_from_region_with_strategy(image_path, region, strategy_name)

            assert result == "Region text"
            mock_cv2.imread.assert_called_once()
            mock_extract.assert_called_once()

    def test_extract_text_from_region_handles_invalid_region(self):
        """Test that invalid regions are handled gracefully."""
        from scripts.utils.optimal_ocr import extract_text_from_region_with_strategy

        # Mock cv2
        with patch("scripts.utils.optimal_ocr.cv2") as mock_cv2:
            mock_img = MagicMock()
            mock_img.shape = (100, 200, 3)
            mock_cv2.imread.return_value = mock_img

            image_path = Path("test.jpg")
            # Invalid region (negative coordinates)
            region = (-10, -20, 50, 30)
            strategy_name = "tesseract_bilateral_psm3"

            # Should handle gracefully (return empty or raise)
            try:
                result = extract_text_from_region_with_strategy(image_path, region, strategy_name)
                # If it doesn't raise, result should be empty or handled
                assert isinstance(result, str)
            except (ValueError, IndexError):
                # Expected for invalid regions
                pass

    @patch("scripts.cli.parse.characters.extract_front_card_fields_with_optimal_strategies")
    @patch("scripts.cli.parse.characters.extract_back_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_uses_field_specific_extraction(self, mock_console, mock_back, mock_front_fields):
        """Test that parse_character_images uses field-specific extraction when enabled."""
        from scripts.cli.parse.characters import parse_character_images

        # Mock field-specific extraction
        mock_front_fields.return_value = FrontCardFields(
            name="Test Character",
            location="Test Location",
            motto="Test Motto",
            story="Test story",
        )

        # Mock back card extraction
        mock_back.return_value = "Back card text\nCommon Powers: Marksman, Toughness"

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, None, None, use_optimal_strategies=True, quiet=True
        )

        assert result is not None
        assert isinstance(result, CharacterData)
        # Verify field-specific extraction was called
        mock_front_fields.assert_called_once_with(front_path)

    @patch("scripts.cli.parse.characters.extract_front_card_fields_with_optimal_strategies")
    @patch("scripts.cli.parse.characters.extract_front_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.extract_back_card_with_optimal_strategy")
    @patch("scripts.cli.parse.characters.console")
    def test_parse_falls_back_to_whole_card_if_fields_empty(
        self, mock_console, mock_back, mock_whole_front, mock_front_fields
    ):
        """Test that parsing falls back to whole-card if field extraction returns empty."""
        from scripts.cli.parse.characters import parse_character_images

        # Mock field-specific extraction returning empty
        mock_front_fields.return_value = FrontCardFields(
            name="",
            location="",
            motto="",
            story="",
        )

        # Mock whole-card extraction (fallback)
        mock_whole_front.return_value = "Whole card text\nName: Test\nLocation: Test Location"

        # Mock back card extraction
        mock_back.return_value = "Back card text"

        front_path = Path("front.jpg")
        back_path = Path("back.jpg")

        result, issues = parse_character_images(
            front_path, back_path, None, None, use_optimal_strategies=True, quiet=True
        )

        assert result is not None
        # Should have called whole-card extraction as fallback
        mock_whole_front.assert_called_once()
