#!/usr/bin/env python3
"""
Unit tests for CharacterPool model.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from scripts.models.character import CharacterData
from scripts.models.character_build import CharacterBuild
from scripts.models.character_pool import CharacterPool
from scripts.models.constants import Season


class TestCharacterPool:
    """Test CharacterPool model."""

    def test_create_pool(self):
        """Test creating CharacterPool."""
        pool = CharacterPool(season_filters=[Season.SEASON1])

        assert len(pool.season_filters) == 1
        assert pool.season_filters[0] == Season.SEASON1
        assert len(pool.characters) == 0

    def test_character_count(self):
        """Test character_count property."""
        pool = CharacterPool()

        assert pool.character_count == 0

        # Add a character
        build = CharacterBuild(character_name="Test")
        pool.characters.append(build)

        assert pool.character_count == 1

    def test_character_names(self):
        """Test character_names property."""
        pool = CharacterPool()

        build1 = CharacterBuild(character_name="Test1")
        build2 = CharacterBuild(character_name="Test2")

        pool.characters.extend([build1, build2])

        names = pool.character_names
        assert len(names) == 2
        assert "Test1" in names
        assert "Test2" in names

    def test_get_character(self):
        """Test get_character method."""
        pool = CharacterPool()

        build = CharacterBuild(character_name="Test")
        pool.characters.append(build)

        found = pool.get_character("Test")
        assert found is not None
        assert found.character_name == "Test"

        not_found = pool.get_character("Nonexistent")
        assert not_found is None

    def test_get_character_case_insensitive(self):
        """Test get_character is case insensitive."""
        pool = CharacterPool()

        build = CharacterBuild(character_name="Test")
        pool.characters.append(build)

        found = pool.get_character("test")
        assert found is not None
        assert found.character_name == "Test"

        found = pool.get_character("TEST")
        assert found is not None
        assert found.character_name == "Test"

