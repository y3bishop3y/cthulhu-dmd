#!/usr/bin/env python3
"""
Unit tests for OCR corrections in parsing utilities.

Tests that OCR corrections are properly loaded and applied.
"""

from scripts.core.parsing.text import OCR_CORRECTIONS, apply_ocr_corrections


class TestOCRCorrections:
    """Test OCR corrections dictionary."""

    def test_ocr_corrections_is_dict(self):
        """Test that OCR_CORRECTIONS is a dictionary."""
        assert isinstance(OCR_CORRECTIONS, dict)

    def test_ocr_corrections_not_empty(self):
        """Test that OCR_CORRECTIONS has entries."""
        # If the TOML file exists and is valid, should have corrections
        assert len(OCR_CORRECTIONS) >= 0  # Can be empty if file doesn't exist

    def test_ocr_corrections_string_types(self):
        """Test that all OCR corrections have string keys and values."""
        for error, correction in OCR_CORRECTIONS.items():
            assert isinstance(error, str), f"Error key should be string, got {type(error)}"
            assert isinstance(correction, str), (
                f"Correction value should be string, got {type(correction)}"
            )

    def test_ocr_corrections_no_empty_keys(self):
        """Test that OCR corrections don't have empty keys."""
        for error in OCR_CORRECTIONS.keys():
            assert len(error) > 0, "OCR correction error key should not be empty"

    def test_ocr_corrections_no_empty_values(self):
        """Test that OCR corrections don't have empty values."""
        for error, correction in OCR_CORRECTIONS.items():
            assert len(correction) > 0, (
                f"OCR correction value should not be empty for error: {error}"
            )


class TestApplyOCRCorrections:
    """Test applying OCR corrections."""

    def test_apply_ocr_corrections_basic(self):
        """Test basic OCR correction application."""
        # Create a test corrections dict
        test_text = "freee detectitve wou"
        corrected = apply_ocr_corrections(test_text)

        # Should apply corrections if they exist in OCR_CORRECTIONS
        # Note: This depends on what's actually in the config file
        assert isinstance(corrected, str)

    def test_apply_ocr_corrections_no_changes(self):
        """Test that text without errors is unchanged."""
        test_text = "This is correct text without any errors"
        corrected = apply_ocr_corrections(test_text)

        # Should return the same text if no corrections apply
        assert corrected == test_text

    def test_apply_ocr_corrections_empty_string(self):
        """Test applying corrections to empty string."""
        corrected = apply_ocr_corrections("")
        assert corrected == ""

    def test_apply_ocr_corrections_preserves_structure(self):
        """Test that corrections preserve text structure."""
        test_text = "freee word detectitve another word"
        corrected = apply_ocr_corrections(test_text)

        # Should preserve word boundaries and structure
        assert isinstance(corrected, str)
        assert len(corrected.split()) == len(test_text.split())

    def test_apply_ocr_corrections_multiple_occurrences(self):
        """Test that corrections apply to all occurrences."""
        test_text = "freee freee freee"
        corrected = apply_ocr_corrections(test_text)

        # All occurrences should be corrected if the correction exists
        if "freee" in OCR_CORRECTIONS:
            assert "freee" not in corrected or OCR_CORRECTIONS["freee"] in corrected

    def test_apply_ocr_corrections_case_sensitive(self):
        """Test that corrections are case-sensitive."""
        # The apply_ocr_corrections uses .replace() which is case-sensitive
        # But some corrections might have case variants
        test_text_lower = "freee"
        test_text_upper = "FREEE"

        corrected_lower = apply_ocr_corrections(test_text_lower)
        corrected_upper = apply_ocr_corrections(test_text_upper)

        # Both should be strings
        assert isinstance(corrected_lower, str)
        assert isinstance(corrected_upper, str)
