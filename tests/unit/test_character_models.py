#!/usr/bin/env python3
"""
Unit tests for character Pydantic models.

Tests CommonPower, CommonPowerLevelData, and PowerLevelStatistics models.
"""

import pytest

from scripts.cli.analyze.powers import PowerLevelAnalysis
from scripts.models.character import (
    CommonPower,
    CommonPowerLevelData,
    PowerLevelStatistics,
)


class TestPowerLevelStatistics:
    """Test PowerLevelStatistics model and its methods."""

    def test_has_any_improvements_false(self):
        """Test has_any_improvements returns False when no improvements."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
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
        assert stats.has_any_improvements is False

    def test_has_any_improvements_conditional(self):
        """Test has_any_improvements returns True for conditional effects."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
            tentacle_risk=1.5,
            base_tentacle_risk=1.5,
            is_conditional=True,
            conditions=["when attacking"],
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
        assert stats.has_any_improvements is True

    def test_has_any_improvements_reroll(self):
        """Test has_any_improvements returns True for reroll effects."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
            tentacle_risk=1.5,
            base_tentacle_risk=1.5,
            is_conditional=False,
            conditions=[],
            rerolls_added=1,
            reroll_type="free",
            has_reroll=True,
            wounds_healed=0,
            stress_healed=0,
            has_healing=False,
            wound_reduction=0,
            sanity_reduction=0,
            has_defensive=False,
        )
        assert stats.has_any_improvements is True

    def test_has_any_improvements_healing(self):
        """Test has_any_improvements returns True for healing effects."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
            tentacle_risk=1.5,
            base_tentacle_risk=1.5,
            is_conditional=False,
            conditions=[],
            rerolls_added=0,
            reroll_type=None,
            has_reroll=False,
            wounds_healed=1,
            stress_healed=0,
            has_healing=True,
            wound_reduction=0,
            sanity_reduction=0,
            has_defensive=False,
        )
        assert stats.has_any_improvements is True

    def test_has_any_improvements_defensive(self):
        """Test has_any_improvements returns True for defensive effects."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
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
            wound_reduction=1,
            sanity_reduction=0,
            has_defensive=True,
        )
        assert stats.has_any_improvements is True

    def test_get_improvements_list_empty(self):
        """Test get_improvements_list returns empty list when no improvements."""
        stats = PowerLevelStatistics(
            green_dice_added=0,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=1.5,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
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
        assert stats.get_improvements_list() == []

    def test_get_improvements_list_all_types(self):
        """Test get_improvements_list includes all improvement types."""
        stats = PowerLevelStatistics(
            green_dice_added=1,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=2.0,
            expected_successes_increase=0.5,
            expected_successes_percent_increase=33.33,
            max_successes_increase=1,
            tentacle_risk=2.0,
            base_tentacle_risk=1.5,
            is_conditional=True,
            conditions=["when attacking"],
            rerolls_added=1,
            reroll_type="free",
            has_reroll=True,
            wounds_healed=1,
            stress_healed=1,
            has_healing=True,
            wound_reduction=1,
            sanity_reduction=1,
            has_defensive=True,
        )
        improvements = stats.get_improvements_list()
        assert len(improvements) == 4
        assert any("Conditional" in imp for imp in improvements)
        assert any("Rerolls" in imp for imp in improvements)
        assert any("Healing" in imp for imp in improvements)
        assert any("Defensive" in imp for imp in improvements)

    def test_from_analysis(self):
        """Test from_analysis creates PowerLevelStatistics correctly."""
        # Create mock analysis
        from scripts.cli.analyze.powers import (
            ActionAddition,
            DiceAddition,
            ElderSignConversion,
        )

        analysis = PowerLevelAnalysis(
            power_name="Test Power",
            level=1,
            description="Test description",
            effect="Adds 1 green dice",
            dice_addition=DiceAddition(green_dice=1, black_dice=0),
            elder_sign_conversion=ElderSignConversion(
                elder_signs_as_successes=0,
                converts_any_number=False,
                successes_per_elder_sign=1,
            ),
            action_addition=ActionAddition(actions_added=0),
            base_expected_successes=1.5,
            enhanced_expected_successes=2.0,
            expected_successes_increase=0.5,
            expected_successes_percent_increase=33.33,
            max_successes_increase=1,
            tentacle_risk=2.0,
            base_tentacle_risk=1.5,
        )

        # Create mock effects (define inline to avoid import issues)
        from pydantic import BaseModel, Field

        class ConditionalEffects(BaseModel):
            conditions: list = Field(default_factory=list)

            @property
            def is_conditional(self) -> bool:
                return len(self.conditions) > 0

        class RerollEffects(BaseModel):
            rerolls_added: int = Field(default=0)
            reroll_type: str | None = Field(default=None)

            @property
            def has_reroll(self) -> bool:
                return self.rerolls_added > 0

        class HealingEffects(BaseModel):
            wounds_healed: int = Field(default=0)
            stress_healed: int = Field(default=0)

            @property
            def has_healing(self) -> bool:
                return self.wounds_healed > 0 or self.stress_healed > 0

        class DefensiveEffects(BaseModel):
            wound_reduction: int = Field(default=0)
            sanity_reduction: int = Field(default=0)

            @property
            def has_defensive(self) -> bool:
                return self.wound_reduction > 0 or self.sanity_reduction > 0

        conditional_effects = ConditionalEffects(conditions=["when attacking"])
        reroll_effects = RerollEffects(rerolls_added=1, reroll_type="free")
        healing_effects = HealingEffects(wounds_healed=1, stress_healed=0)
        defensive_effects = DefensiveEffects(wound_reduction=0, sanity_reduction=0)

        stats = PowerLevelStatistics.from_analysis(
            analysis,
            conditional_effects=conditional_effects,
            reroll_effects=reroll_effects,
            healing_effects=healing_effects,
            defensive_effects=defensive_effects,
        )

        assert stats.green_dice_added == 1
        assert stats.black_dice_added == 0
        assert stats.base_expected_successes == pytest.approx(1.5, rel=0.01)
        assert stats.enhanced_expected_successes == pytest.approx(2.0, rel=0.01)
        assert stats.is_conditional is True
        assert stats.has_reroll is True
        assert stats.has_healing is True
        assert stats.has_defensive is False


class TestCommonPowerLevelData:
    """Test CommonPowerLevelData model."""

    def test_create_common_power_level_data(self):
        """Test creating CommonPowerLevelData with all fields."""
        stats = PowerLevelStatistics(
            green_dice_added=1,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=2.0,
            expected_successes_increase=0.5,
            expected_successes_percent_increase=33.33,
            max_successes_increase=1,
            tentacle_risk=2.0,
            base_tentacle_risk=1.5,
        )

        level_data = CommonPowerLevelData(
            level=1,
            description="Test description",
            statistics=stats,
            effect="Adds 1 green dice",
        )

        assert level_data.level == 1
        assert level_data.description == "Test description"
        assert level_data.statistics == stats
        assert level_data.effect == "Adds 1 green dice"

    def test_level_validation(self):
        """Test level must be between 1 and 4."""
        stats = PowerLevelStatistics()

        # Valid levels
        CommonPowerLevelData(level=1, description="Test", statistics=stats, effect="")
        CommonPowerLevelData(level=4, description="Test", statistics=stats, effect="")

        # Invalid levels
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommonPowerLevelData(level=0, description="Test", statistics=stats, effect="")

        with pytest.raises(ValidationError):
            CommonPowerLevelData(level=5, description="Test", statistics=stats, effect="")


class TestCommonPower:
    """Test CommonPower model and its serialization methods."""

    def test_from_dict_minimal(self):
        """Test from_dict with minimal data."""
        data = {
            "name": "Test Power",
            "is_special": False,
            "levels": [],
        }

        power = CommonPower.from_dict(data)

        assert power.name == "Test Power"
        assert power.is_special is False
        assert len(power.levels) == 0

    def test_from_dict_with_levels(self):
        """Test from_dict with full level data."""
        data = {
            "name": "Arcane Mastery",
            "is_special": False,
            "levels": [
                {
                    "level": 1,
                    "description": "When making any roll, you may count 1 Arcane as a success.",
                    "statistics": {
                        "green_dice_added": 0,
                        "black_dice_added": 0,
                        "base_expected_successes": 1.5,
                        "enhanced_expected_successes": 2.0,
                        "expected_successes_increase": 0.5,
                        "expected_successes_percent_increase": 33.33,
                        "max_successes_increase": 0,
                        "tentacle_risk": 1.5,
                        "base_tentacle_risk": 1.5,
                        "is_conditional": False,
                        "conditions": [],
                        "rerolls_added": 0,
                        "reroll_type": None,
                        "has_reroll": False,
                        "wounds_healed": 0,
                        "stress_healed": 0,
                        "has_healing": False,
                        "wound_reduction": 0,
                        "sanity_reduction": 0,
                        "has_defensive": False,
                    },
                    "effect": "Counts 1 elder sign(s) as success(es)",
                },
            ],
        }

        power = CommonPower.from_dict(data)

        assert power.name == "Arcane Mastery"
        assert power.is_special is False
        assert len(power.levels) == 1
        assert power.levels[0].level == 1
        assert (
            power.levels[0].description
            == "When making any roll, you may count 1 Arcane as a success."
        )
        assert power.levels[0].effect == "Counts 1 elder sign(s) as success(es)"
        assert power.levels[0].statistics.green_dice_added == 0

    def test_to_dict_minimal(self):
        """Test to_dict with minimal data."""
        power = CommonPower(
            name="Test Power",
            is_special=False,
            levels=[],
        )

        data = power.to_dict()

        assert data["name"] == "Test Power"
        assert data["is_special"] is False
        assert data["levels"] == []

    def test_to_dict_with_levels(self):
        """Test to_dict with full level data."""
        stats = PowerLevelStatistics(
            green_dice_added=1,
            black_dice_added=0,
            base_expected_successes=1.5,
            enhanced_expected_successes=2.0,
            expected_successes_increase=0.5,
            expected_successes_percent_increase=33.33,
            max_successes_increase=1,
            tentacle_risk=2.0,
            base_tentacle_risk=1.5,
        )

        level_data = CommonPowerLevelData(
            level=1,
            description="Test description",
            statistics=stats,
            effect="Adds 1 green dice",
        )

        power = CommonPower(
            name="Test Power",
            is_special=False,
            levels=[level_data],
        )

        data = power.to_dict()

        assert data["name"] == "Test Power"
        assert data["is_special"] is False
        assert len(data["levels"]) == 1
        assert data["levels"][0]["level"] == 1
        assert data["levels"][0]["description"] == "Test description"
        assert data["levels"][0]["effect"] == "Adds 1 green dice"
        assert data["levels"][0]["statistics"]["green_dice_added"] == 1

    def test_round_trip_serialization(self):
        """Test that from_dict and to_dict are inverse operations."""
        original_data = {
            "name": "Test Power",
            "is_special": True,
            "levels": [
                {
                    "level": 1,
                    "description": "Level 1 description",
                    "statistics": {
                        "green_dice_added": 1,
                        "black_dice_added": 0,
                        "base_expected_successes": 1.5,
                        "enhanced_expected_successes": 2.0,
                        "expected_successes_increase": 0.5,
                        "expected_successes_percent_increase": 33.33,
                        "max_successes_increase": 1,
                        "tentacle_risk": 2.0,
                        "base_tentacle_risk": 1.5,
                        "is_conditional": False,
                        "conditions": [],
                        "rerolls_added": 0,
                        "reroll_type": None,
                        "has_reroll": False,
                        "wounds_healed": 0,
                        "stress_healed": 0,
                        "has_healing": False,
                        "wound_reduction": 0,
                        "sanity_reduction": 0,
                        "has_defensive": False,
                    },
                    "effect": "Adds 1 green dice",
                },
            ],
        }

        # Convert to model and back
        power = CommonPower.from_dict(original_data)
        round_trip_data = power.to_dict()

        # Compare key fields (statistics dict may have slight differences due to rounding)
        assert round_trip_data["name"] == original_data["name"]
        assert round_trip_data["is_special"] == original_data["is_special"]
        assert len(round_trip_data["levels"]) == len(original_data["levels"])
        assert round_trip_data["levels"][0]["level"] == original_data["levels"][0]["level"]
        assert (
            round_trip_data["levels"][0]["description"] == original_data["levels"][0]["description"]
        )
        assert round_trip_data["levels"][0]["effect"] == original_data["levels"][0]["effect"]
        assert (
            round_trip_data["levels"][0]["statistics"]["green_dice_added"]
            == original_data["levels"][0]["statistics"]["green_dice_added"]
        )
