#!/usr/bin/env python3
"""
Unit tests for CharacterBuild and CharacterStatistics models.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from scripts.models.character import (
    CharacterData,
    CommonPowerLevelData,
    PowerLevelStatistics,
)
from scripts.models.character_build import CharacterBuild, CharacterStatistics


@pytest.fixture
def sample_power_statistics():
    """Create sample power statistics."""
    return PowerLevelStatistics(
        green_dice_added=2,
        black_dice_added=0,
        base_expected_successes=1.5,
        enhanced_expected_successes=2.5,
        expected_successes_increase=1.0,
        expected_successes_percent_increase=66.67,
        max_successes_increase=2,
        tentacle_risk=1.5,
        base_tentacle_risk=1.5,
        is_conditional=False,
        conditions=[],
        rerolls_added=0,
        reroll_type=None,
        has_reroll=False,
        wounds_healed=0,
        stress_healed=0,
        has_healing=False,
        wound_reduction=0,
        sanity_reduction=0,
        has_defensive=False,
    )


@pytest.fixture
def sample_common_power_level(sample_power_statistics):
    """Create sample common power level."""
    return CommonPowerLevelData(
        level=2,
        description="Gain 2 green dice when attacking",
        statistics=sample_power_statistics,
        effect="Adds 2 green dice",
    )


@pytest.fixture
def sample_character_data():
    """Create sample character data."""
    return CharacterData(
        name="Test Character",
        location="Test Location",
        motto="Test Motto",
        story="Test Story",
        common_powers=["Marksman", "Arcane Mastery"],
    )


class TestCharacterStatistics:
    """Test CharacterStatistics model."""

    def test_create_statistics(self):
        """Test creating CharacterStatistics."""
        stats = CharacterStatistics(
            total_black_dice=3,
            total_green_dice=2,
            total_dice=5,
            expected_successes=2.5,
            expected_tentacles=1.5,
            expected_elder_signs=1.0,
            prob_at_least_1_success=0.95,
            prob_at_least_1_tentacle=0.7,
            prob_at_least_1_elder=0.5,
            max_possible_successes=5,
        )

        assert stats.total_black_dice == 3
        assert stats.total_green_dice == 2
        assert stats.total_dice == 5
        assert stats.expected_successes == 2.5

    def test_statistics_defaults(self):
        """Test CharacterStatistics with defaults."""
        stats = CharacterStatistics()

        assert stats.total_black_dice == 3
        assert stats.total_green_dice == 0
        assert stats.total_dice == 3
        assert stats.expected_successes == 0.0


class TestCharacterBuild:
    """Test CharacterBuild model."""

    def test_create_build(self):
        """Test creating CharacterBuild."""
        build = CharacterBuild(
            character_name="Test Character",
            common_power_1_name="Marksman",
            common_power_1_level=2,
            common_power_2_name="Arcane Mastery",
            common_power_2_level=1,
        )

        assert build.character_name == "Test Character"
        assert build.common_power_1_name == "Marksman"
        assert build.common_power_1_level == 2
        assert build.common_power_2_name == "Arcane Mastery"
        assert build.common_power_2_level == 1

    def test_build_defaults(self):
        """Test CharacterBuild with defaults."""
        build = CharacterBuild(character_name="Test")

        assert build.character_name == "Test"
        assert build.special_power_level == 1
        assert build.common_power_1_level == 1
        assert build.common_power_2_level == 1
        assert build.common_power_1_name is None
        assert build.common_power_2_name is None

    def test_power_combination_base(self):
        """Test power combination with no powers."""
        build = CharacterBuild(character_name="Test")

        combination = build.power_combination

        assert combination.base_black_dice == 3
        assert combination.base_green_dice == 0  # No red swirls reached
        assert len(combination.effects) == 0

    def test_power_combination_with_insanity_track(self):
        """Test power combination includes insanity track green dice."""
        build = CharacterBuild(character_name="Test")
        # Advance to red swirl 2 (slot 9) which grants green dice
        build.insanity_track.current_insanity = 9

        combination = build.power_combination

        assert combination.base_black_dice == 3
        assert combination.base_green_dice == 1  # Red swirl 2 grants green dice
        assert build.insanity_track.green_dice_bonus == 1

    def test_all_power_effects_empty(self):
        """Test all_power_effects with no powers loaded."""
        build = CharacterBuild(character_name="Test")

        effects = build.all_power_effects

        assert len(effects) == 0

    def test_statistics_calculation(self):
        """Test statistics calculation."""
        build = CharacterBuild(character_name="Test")

        stats = build.statistics

        assert stats.total_black_dice == 3
        assert stats.total_green_dice == 0
        assert stats.total_dice == 3
        assert stats.expected_successes > 0  # Base dice should have expected successes

    def test_from_character_data(self, sample_character_data):
        """Test creating build from character data."""
        build = CharacterBuild.from_character_data(
            sample_character_data,
            common_power_1_level=2,
            common_power_2_level=1,
        )

        assert build.character_name == "Test Character"
        assert build.common_power_1_name == "Marksman"
        assert build.common_power_1_level == 2
        assert build.common_power_2_name == "Arcane Mastery"
        assert build.common_power_2_level == 1

    def test_insanity_track_integration(self):
        """Test insanity track integration."""
        build = CharacterBuild(character_name="Test")

        # Test initial state
        assert build.insanity_track.current_insanity == 1
        assert build.insanity_track.green_dice_bonus == 0

        # Advance to first red swirl (slot 5)
        build.insanity_track.current_insanity = 5
        assert build.insanity_track.level_ups_available == 1
        assert build.insanity_track.green_dice_bonus == 0  # Red swirl 1 doesn't grant green dice

        # Advance to second red swirl (slot 9)
        build.insanity_track.current_insanity = 9
        assert build.insanity_track.level_ups_available == 2
        assert build.insanity_track.green_dice_bonus == 1  # Red swirl 2 grants green dice

        # Check power combination includes green dice
        combination = build.power_combination
        assert combination.base_green_dice == 1

    def test_health_stress_tracks(self):
        """Test health and stress tracks."""
        build = CharacterBuild(character_name="Test")

        # Test initial state
        assert build.health_track.current_health == 5
        assert build.stress_track.current_stress == 0

        # Test damage
        build.health_track.take_damage(2)
        assert build.health_track.current_health == 3

        # Test stress
        build.stress_track.take_stress(3)
        assert build.stress_track.current_stress == 3
