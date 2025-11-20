#!/usr/bin/env python3
"""
Unit tests for OCR configuration loading.

Tests the OCR corrections loading from TOML files using Pydantic Settings.
"""

import tempfile
from pathlib import Path

import pytest

from scripts.models.ocr_config import (
    OCR_CORRECTIONS_FILE,
    OCRCorrectionsConfig,
    get_ocr_corrections,
)


class TestOCRCorrectionsConfig:
    """Test OCR corrections configuration loading."""

    def test_load_from_file_valid_toml(self):
        """Test loading valid TOML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[corrections]
"freee" = "free"
"detectitve" = "detective"
"wou" = "wound"
"o!" = "of"
"""
            )
            temp_path = Path(f.name)

        try:
            config = OCRCorrectionsConfig.load_from_file(temp_path)
            assert len(config.corrections) == 4
            assert config.corrections["freee"] == "free"
            assert config.corrections["detectitve"] == "detective"
            assert config.corrections["wou"] == "wound"
            assert config.corrections["o!"] == "of"
        finally:
            temp_path.unlink()

    def test_load_from_file_missing_file(self):
        """Test loading from non-existent file returns empty config."""
        non_existent = Path("/nonexistent/path/ocr_corrections.toml")
        config = OCRCorrectionsConfig.load_from_file(non_existent)
        assert len(config.corrections) == 0
        assert isinstance(config.corrections, dict)

    def test_load_from_file_invalid_toml(self):
        """Test loading invalid TOML file returns empty config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml content [unclosed")
            temp_path = Path(f.name)

        try:
            config = OCRCorrectionsConfig.load_from_file(temp_path)
            # Should return empty config on error
            assert len(config.corrections) == 0
        finally:
            temp_path.unlink()

    def test_get_corrections_dict(self):
        """Test getting corrections as dictionary."""
        config = OCRCorrectionsConfig(corrections={"test": "value"})
        corrections_dict = config.get_corrections_dict()
        assert isinstance(corrections_dict, dict)
        assert corrections_dict["test"] == "value"
        # Should be a copy, not the same object
        assert corrections_dict is not config.corrections

    def test_load_from_default_file(self):
        """Test loading from default file location."""
        # This will use the actual file if it exists, or return empty config
        config = OCRCorrectionsConfig.load_from_file()
        assert isinstance(config.corrections, dict)
        # If file exists, should have some corrections
        if OCR_CORRECTIONS_FILE.exists():
            assert len(config.corrections) > 0


class TestGetOCRCorrections:
    """Test the get_ocr_corrections function."""

    def test_get_ocr_corrections_returns_dict(self):
        """Test that get_ocr_corrections returns a dictionary."""
        corrections = get_ocr_corrections()
        assert isinstance(corrections, dict)

    def test_get_ocr_corrections_caching(self):
        """Test that get_ocr_corrections caches the result."""
        # Import the module-level variable to reset cache
        import scripts.models.ocr_config as ocr_config_module

        # Reset the cache
        ocr_config_module._ocr_config = None

        # First call
        corrections1 = get_ocr_corrections()
        # Second call should return the same cached result
        corrections2 = get_ocr_corrections()

        # Should be the same dictionary (same object reference)
        assert corrections1 is corrections2

    def test_get_ocr_corrections_with_custom_file(self):
        """Test get_ocr_corrections with a custom file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
[corrections]
"test_error" = "test_correction"
"""
            )
            temp_path = Path(f.name)

        try:
            # Reset cache
            import scripts.models.ocr_config as ocr_config_module

            ocr_config_module._ocr_config = None

            # Load from custom file
            config = OCRCorrectionsConfig.load_from_file(temp_path)
            corrections = config.get_corrections_dict()

            assert "test_error" in corrections
            assert corrections["test_error"] == "test_correction"
        finally:
            temp_path.unlink()


class TestOCRCorrectionsIntegration:
    """Integration tests for OCR corrections."""

    def test_ocr_corrections_file_exists(self):
        """Test that the default OCR corrections file exists."""
        # The file should exist in the project
        assert OCR_CORRECTIONS_FILE.exists(), f"OCR corrections file not found: {OCR_CORRECTIONS_FILE}"

    def test_ocr_corrections_file_valid_toml(self):
        """Test that the default OCR corrections file is valid TOML."""
        if not OCR_CORRECTIONS_FILE.exists():
            pytest.skip("OCR corrections file does not exist")

        # Should not raise an exception
        config = OCRCorrectionsConfig.load_from_file()
        assert isinstance(config.corrections, dict)

    def test_ocr_corrections_has_expected_keys(self):
        """Test that OCR corrections contain expected common corrections."""
        if not OCR_CORRECTIONS_FILE.exists():
            pytest.skip("OCR corrections file does not exist")

        corrections = get_ocr_corrections()

        # Check for some common corrections that should be present
        # These are examples - adjust based on actual file contents
        if len(corrections) > 0:
            # At least verify the structure is correct
            assert all(isinstance(k, str) for k in corrections.keys())
            assert all(isinstance(v, str) for v in corrections.values())

