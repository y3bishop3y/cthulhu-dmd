#!/usr/bin/env python3
"""
Power Combination Models

Models for combining multiple powers and calculating their combined effects.
"""

from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, computed_field

from scripts.models.character import CommonPowerLevelData
from scripts.models.dice_probabilities import (
    CombinedRollStats,
    DiceProbabilityCalculator,
    SingleDieStats,
)
from scripts.models.game_mechanics import BonusDice, DiceType, StandardDice


class PowerEffect(BaseModel):
    """Represents a single power effect."""

    power_name: str = Field(..., description="Name of the power")
    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    green_dice_added: int = Field(default=0, ge=0, description="Green dice added")
    black_dice_added: int = Field(default=0, ge=0, description="Black dice added")
    elder_signs_as_successes: Optional[int] = Field(
        default=None,
        description="Number of elder signs that count as successes (None = any number)",
    )
    rerolls_added: int = Field(default=0, ge=0, description="Rerolls added")
    wounds_healed: int = Field(default=0, ge=0, description="Wounds healed")
    stress_healed: int = Field(default=0, ge=0, description="Stress healed")
    is_conditional: bool = Field(default=False, description="Whether effect has conditions")
    conditions: List[str] = Field(default_factory=list, description="Condition descriptions")
    replaces_previous: bool = Field(
        default=False, description="Whether this effect replaces previous effects (instead clause)"
    )


class PowerCombination(BaseModel):
    """Represents a combination of multiple active powers."""

    effects: List[PowerEffect] = Field(default_factory=list, description="List of power effects")
    base_black_dice: int = Field(default=3, ge=0, description="Base black dice count")
    base_green_dice: int = Field(default=0, ge=0, description="Base green dice count")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_green_dice(self) -> int:
        """Calculate total green dice from all effects."""
        total = self.base_green_dice
        for effect in self.effects:
            if not effect.replaces_previous:
                total += effect.green_dice_added
        return total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_black_dice(self) -> int:
        """Calculate total black dice from all effects."""
        total = self.base_black_dice
        for effect in self.effects:
            if not effect.replaces_previous:
                total += effect.black_dice_added
        return total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_rerolls(self) -> int:
        """Calculate total rerolls from all effects."""
        total = 0
        for effect in self.effects:
            if not effect.replaces_previous:
                total += effect.rerolls_added
        return total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_healing(self) -> tuple[int, int]:
        """Calculate total healing (wounds, stress) from all effects."""
        wounds = 0
        stress = 0
        for effect in self.effects:
            if not effect.replaces_previous:
                wounds += effect.wounds_healed
                stress += effect.stress_healed
        return (wounds, stress)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def elder_sign_conversion(self) -> Optional[int]:
        """Get elder sign to success conversion (None = any number)."""
        # Find the highest level conversion (later levels replace earlier)
        conversion = None
        for effect in sorted(self.effects, key=lambda e: e.level, reverse=True):
            if effect.elder_signs_as_successes is not None:
                conversion = effect.elder_signs_as_successes
                break
        return conversion

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_conditional_effects(self) -> bool:
        """Check if any effects have conditions."""
        return any(effect.is_conditional for effect in self.effects)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_conditions(self) -> Set[str]:
        """Get all unique conditions from effects."""
        conditions: Set[str] = set()
        for effect in self.effects:
            conditions.update(effect.conditions)
        return conditions


class PowerCombinationCalculator:
    """Calculates combined statistics for power combinations."""

    def __init__(self):
        """Initialize calculator with dice statistics."""
        self.calculator = DiceProbabilityCalculator()
        self.black_stats = SingleDieStats.from_dice(DiceType.BLACK, StandardDice())  # type: ignore[call-arg]
        self.green_stats = SingleDieStats.from_dice(DiceType.GREEN, BonusDice())  # type: ignore[call-arg]

    def calculate_combined_stats(self, combination: PowerCombination) -> CombinedRollStats:
        """Calculate combined roll statistics for a power combination.

        Args:
            combination: Power combination to analyze

        Returns:
            CombinedRollStats with calculated probabilities
        """
        black_count = combination.total_black_dice
        green_count = combination.total_green_dice

        return CombinedRollStats.from_counts(
            black_count=black_count,
            green_count=green_count,
            black_stats=self.black_stats,
            green_stats=self.green_stats,
        )

    def calculate_with_elder_conversion(self, combination: PowerCombination) -> Dict[str, float]:
        """Calculate statistics including elder sign to success conversion.

        Args:
            combination: Power combination to analyze

        Returns:
            Dictionary with enhanced statistics
        """
        base_stats = self.calculate_combined_stats(combination)
        conversion = combination.elder_sign_conversion

        stats = {
            "expected_successes": base_stats.expected_successes,
            "expected_tentacles": base_stats.expected_tentacles,
            "expected_elder_signs": base_stats.expected_elder_signs,
            "prob_at_least_1_success": base_stats.prob_at_least_1_success,
            "prob_at_least_1_tentacle": base_stats.prob_at_least_1_tentacle,
        }

        # Apply elder sign conversion
        if conversion is not None:
            # Each elder sign counts as success
            # Expected successes increase by expected elder signs
            stats["expected_successes"] += base_stats.expected_elder_signs
            stats["elder_signs_converted"] = base_stats.expected_elder_signs
        elif conversion is None and base_stats.expected_elder_signs > 0:
            # "Any number" conversion - all elder signs become successes
            stats["expected_successes"] += base_stats.expected_elder_signs
            stats["elder_signs_converted"] = base_stats.expected_elder_signs

        return stats

    def compare_combinations(
        self, base: PowerCombination, enhanced: PowerCombination
    ) -> Dict[str, float]:
        """Compare two power combinations and calculate improvement.

        Args:
            base: Base power combination
            enhanced: Enhanced power combination

        Returns:
            Dictionary with improvement metrics
        """
        base_stats = self.calculate_with_elder_conversion(base)
        enhanced_stats = self.calculate_with_elder_conversion(enhanced)

        return {
            "expected_successes_increase": enhanced_stats["expected_successes"]
            - base_stats["expected_successes"],
            "expected_successes_percent_increase": (
                (enhanced_stats["expected_successes"] - base_stats["expected_successes"])
                / base_stats["expected_successes"]
                * 100
                if base_stats["expected_successes"] > 0
                else 0.0
            ),
            "tentacle_risk_change": enhanced_stats["expected_tentacles"]
            - base_stats["expected_tentacles"],
            "elder_signs_increase": enhanced_stats.get("elder_signs_converted", 0)
            - base_stats.get("elder_signs_converted", 0),
        }


def create_power_effect_from_level(
    power_name: str, level_data: CommonPowerLevelData
) -> PowerEffect:
    """Create a PowerEffect from a CommonPowerLevelData.

    Args:
        power_name: Name of the power
        level_data: Power level data with statistics

    Returns:
        PowerEffect representing this power level
    """
    stats = level_data.statistics

    # Determine elder sign conversion from effect description
    elder_conversion = None
    if "count" in level_data.effect.lower() and "elder sign" in level_data.effect.lower():
        if "any number" in level_data.effect.lower():
            elder_conversion = None  # Any number
        else:
            # Try to extract number (e.g., "count 1 elder sign")
            import re

            match = re.search(r"count\s+(\d+)\s+elder", level_data.effect.lower())
            if match:
                elder_conversion = int(match.group(1))

    return PowerEffect(
        power_name=power_name,
        level=level_data.level,
        green_dice_added=stats.green_dice_added,
        black_dice_added=stats.black_dice_added,
        elder_signs_as_successes=elder_conversion,
        rerolls_added=stats.rerolls_added,
        wounds_healed=stats.wounds_healed,
        stress_healed=stats.stress_healed,
        is_conditional=stats.is_conditional,
        conditions=stats.conditions,
        replaces_previous="instead" in level_data.effect.lower(),
    )
