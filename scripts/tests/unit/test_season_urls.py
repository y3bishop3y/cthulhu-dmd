#!/usr/bin/env python3
"""
Unit tests for season URLs loading.

Tests the season URLs loading from JSON files.
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.download_characters import load_season_urls


class TestLoadSeasonURLs:
    """Test season URLs loading functionality."""

    def test_load_season_urls_valid_json(self):
        """Test loading valid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "season_urls": {
                        "season1": "https://example.com/season1",
                        "season2": "https://example.com/season2",
                    },
                    "season_pdf_urls": {
                        "season1": "https://example.com/season1.pdf",
                    },
                },
                f,
            )
            temp_path = Path(f.name)

        try:
            # Temporarily patch the file path
            import scripts.download_characters as download_module

            original_path = download_module.SEASON_URLS_FILE
            download_module.SEASON_URLS_FILE = temp_path

            season_urls, season_pdf_urls = load_season_urls()

            assert len(season_urls) == 2
            assert season_urls["season1"] == "https://example.com/season1"
            assert season_urls["season2"] == "https://example.com/season2"

            assert len(season_pdf_urls) == 1
            assert season_pdf_urls["season1"] == "https://example.com/season1.pdf"

            # Restore original path
            download_module.SEASON_URLS_FILE = original_path
        finally:
            temp_path.unlink()

    def test_load_season_urls_missing_file(self):
        """Test loading from non-existent file returns empty dicts."""
        import scripts.download_characters as download_module

        original_path = download_module.SEASON_URLS_FILE
        non_existent = Path("/nonexistent/path/season_urls.json")
        download_module.SEASON_URLS_FILE = non_existent

        try:
            season_urls, season_pdf_urls = load_season_urls()
            assert isinstance(season_urls, dict)
            assert isinstance(season_pdf_urls, dict)
            assert len(season_urls) == 0
            assert len(season_pdf_urls) == 0
        finally:
            download_module.SEASON_URLS_FILE = original_path

    def test_load_season_urls_invalid_json(self):
        """Test loading invalid JSON file returns empty dicts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {unclosed")
            temp_path = Path(f.name)

        try:
            import scripts.download_characters as download_module

            original_path = download_module.SEASON_URLS_FILE
            download_module.SEASON_URLS_FILE = temp_path

            season_urls, season_pdf_urls = load_season_urls()
            # Should return empty dicts on error
            assert isinstance(season_urls, dict)
            assert isinstance(season_pdf_urls, dict)
            assert len(season_urls) == 0
            assert len(season_pdf_urls) == 0

            download_module.SEASON_URLS_FILE = original_path
        finally:
            temp_path.unlink()

    def test_load_season_urls_missing_keys(self):
        """Test loading JSON with missing keys."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"season_urls": {"season1": "https://example.com"}}, f)
            temp_path = Path(f.name)

        try:
            import scripts.download_characters as download_module

            original_path = download_module.SEASON_URLS_FILE
            download_module.SEASON_URLS_FILE = temp_path

            season_urls, season_pdf_urls = load_season_urls()

            assert len(season_urls) == 1
            assert len(season_pdf_urls) == 0  # Missing key should default to empty dict

            download_module.SEASON_URLS_FILE = original_path
        finally:
            temp_path.unlink()

    def test_load_season_urls_default_file_exists(self):
        """Test that the default season URLs file exists."""
        from scripts.download_characters import SEASON_URLS_FILE

        assert SEASON_URLS_FILE.exists(), f"Season URLs file not found: {SEASON_URLS_FILE}"

    def test_load_season_urls_default_file_valid(self):
        """Test that the default season URLs file is valid JSON."""
        from scripts.download_characters import SEASON_URLS_FILE

        if not SEASON_URLS_FILE.exists():
            pytest.skip("Season URLs file does not exist")

        season_urls, season_pdf_urls = load_season_urls()

        assert isinstance(season_urls, dict)
        assert isinstance(season_pdf_urls, dict)

        # If file exists, should have some URLs
        if SEASON_URLS_FILE.exists():
            assert len(season_urls) > 0

    def test_load_season_urls_structure(self):
        """Test that loaded URLs have correct structure."""
        from scripts.download_characters import SEASON_URLS_FILE

        if not SEASON_URLS_FILE.exists():
            pytest.skip("Season URLs file does not exist")

        season_urls, season_pdf_urls = load_season_urls()

        # All values should be strings (URLs)
        assert all(isinstance(url, str) for url in season_urls.values())
        assert all(isinstance(url, str) for url in season_pdf_urls.values())

        # URLs should start with http:// or https://
        assert all(url.startswith(("http://", "https://")) for url in season_urls.values())
        assert all(url.startswith(("http://", "https://")) for url in season_pdf_urls.values())

