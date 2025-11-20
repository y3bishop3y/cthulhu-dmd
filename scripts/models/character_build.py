#!/usr/bin/env python3
"""
Character Build Models

Models for building complete character builds with all powers combined.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from scripts.models.character import (
    CharacterData,
    CommonPowerLevelData,
)
from scripts.models.game_mechanics import HealthTrack, InsanityTrack, StressTrack
from scripts.models.power_combination import (
    PowerCombination,
    PowerCombinationCalculator,
    PowerEffect,
    create_power_effect_from_level,
)


class CharacterStatistics(BaseModel):
    """Complete statistics for a character build."""

    # Dice statistics
    total_black_dice: int = Field(default=3, ge=0, description="Total black dice")
    total_green_dice: int = Field(default=0, ge=0, description="Total green dice")
    total_dice: int = Field(default=3, ge=0, description="Total dice (black + green)")

    # Expected outcomes
    expected_successes: float = Field(
        default=0.0, ge=0.0, description="Expected successes per roll"
    )
    expected_tentacles: float = Field(
        default=0.0, ge=0.0, description="Expected tentacles per roll"
    )
    expected_elder_signs: float = Field(
        default=0.0, ge=0.0, description="Expected elder signs per roll"
    )

    # Probabilities
    prob_at_least_1_success: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of at least 1 success"
    )
    prob_at_least_1_tentacle: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of at least 1 tentacle"
    )
    prob_at_least_1_elder: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of at least 1 elder sign"
    )

    # Maximums
    max_possible_successes: int = Field(default=0, ge=0, description="Maximum possible successes")

    # Elder sign conversion
    elder_signs_converted_to_successes: float = Field(
        default=0.0, ge=0.0, description="Elder signs converted to successes"
    )

    # Healing capabilities
    wounds_healed_per_turn: int = Field(default=0, ge=0, description="Wounds healed per turn")
    stress_healed_per_turn: int = Field(default=0, ge=0, description="Stress healed per turn")

    # Rerolls
    rerolls_per_roll: int = Field(default=0, ge=0, description="Rerolls available per roll")

    # Free actions
    free_actions_per_turn: int = Field(default=0, ge=0, description="Free actions per turn")

    # Defensive capabilities
    wound_reduction: int = Field(default=0, ge=0, description="Wound damage reduction")
    sanity_reduction: int = Field(default=0, ge=0, description="Sanity loss reduction")


class CharacterBuild(BaseModel):
    """Represents a complete character build with all powers combined."""

    character_name: str = Field(..., description="Character name")
    character_data: Optional[CharacterData] = Field(default=None, description="Full character data")

    # Power levels
    special_power_level: int = Field(default=1, ge=1, le=4, description="Special power level")
    common_power_1_name: Optional[str] = Field(default=None, description="First common power name")
    common_power_1_level: int = Field(default=1, ge=1, le=4, description="First common power level")
    common_power_2_name: Optional[str] = Field(default=None, description="Second common power name")
    common_power_2_level: int = Field(
        default=1, ge=1, le=4, description="Second common power level"
    )

    # Tracks
    insanity_track: InsanityTrack = Field(
        default_factory=InsanityTrack, description="Insanity track state"
    )
    health_track: HealthTrack = Field(default_factory=HealthTrack, description="Health track state")
    stress_track: StressTrack = Field(default_factory=StressTrack, description="Stress track state")

    # Power data (loaded from common_powers.json) - using PrivateAttr for internal storage
    _special_power_data: Optional[CommonPowerLevelData] = PrivateAttr(default=None)
    _common_power_1_data: Optional[CommonPowerLevelData] = PrivateAttr(default=None)
    _common_power_2_data: Optional[CommonPowerLevelData] = PrivateAttr(default=None)

    @computed_field
    @property
    def all_power_effects(self) -> List[PowerEffect]:
        """Get all power effects as PowerEffect objects."""
        effects: List[PowerEffect] = []

        # Add special power effect if available
        if self._special_power_data:
            effect = create_power_effect_from_level(
                f"{self.character_name} Special", self._special_power_data
            )
            effects.append(effect)

        # Add common power 1 effect if available
        if self._common_power_1_data and self.common_power_1_name:
            effect = create_power_effect_from_level(
                self.common_power_1_name, self._common_power_1_data
            )
            effects.append(effect)

        # Add common power 2 effect if available
        if self._common_power_2_data and self.common_power_2_name:
            effect = create_power_effect_from_level(
                self.common_power_2_name, self._common_power_2_data
            )
            effects.append(effect)

        return effects

    @computed_field
    @property
    def power_combination(self) -> PowerCombination:
        """Get PowerCombination with all active powers."""
        # Base dice: 3 black, 0 green
        # Add green dice from insanity track red swirls
        base_green = self.insanity_track.green_dice_bonus

        combination = PowerCombination(
            base_black_dice=3,
            base_green_dice=base_green,
            effects=self.all_power_effects,
        )

        return combination

    @computed_field
    @property
    def statistics(self) -> CharacterStatistics:
        """Calculate complete character statistics."""
        calculator = PowerCombinationCalculator()
        combination = self.power_combination

        # Calculate base dice statistics
        base_stats = calculator.calculate_combined_stats(combination)

        # Calculate with elder sign conversion
        enhanced_stats = calculator.calculate_with_elder_conversion(combination)

        # Sum up healing from all effects
        wounds_healed = sum(effect.wounds_healed for effect in combination.effects)
        stress_healed = sum(effect.stress_healed for effect in combination.effects)

        # Sum up rerolls
        rerolls = combination.total_rerolls

        # Sum up free actions (from action additions)
        free_actions = sum(
            1 for effect in combination.effects if effect.rerolls_added > 0
        )  # TODO: Track actual free actions

        # Sum up defensive capabilities
        wound_reduction = sum(
            effect.wounds_healed for effect in combination.effects
        )  # TODO: Track actual reductions
        sanity_reduction = sum(
            effect.stress_healed for effect in combination.effects
        )  # TODO: Track actual reductions

        return CharacterStatistics(
            total_black_dice=combination.total_black_dice,
            total_green_dice=combination.total_green_dice,
            total_dice=combination.total_black_dice + combination.total_green_dice,
            expected_successes=enhanced_stats.get(
                "expected_successes", base_stats.expected_successes
            ),
            expected_tentacles=enhanced_stats.get(
                "expected_tentacles", base_stats.expected_tentacles
            ),
            expected_elder_signs=enhanced_stats.get(
                "expected_elder_signs", base_stats.expected_elder_signs
            ),
            prob_at_least_1_success=enhanced_stats.get(
                "prob_at_least_1_success", base_stats.prob_at_least_1_success
            ),
            prob_at_least_1_tentacle=enhanced_stats.get(
                "prob_at_least_1_tentacle", base_stats.prob_at_least_1_tentacle
            ),
            prob_at_least_1_elder=enhanced_stats.get(
                "prob_at_least_1_elder", base_stats.prob_at_least_1_elder
            ),
            max_possible_successes=base_stats.max_possible_successes,
            elder_signs_converted_to_successes=enhanced_stats.get("elder_signs_converted", 0.0),
            wounds_healed_per_turn=wounds_healed,
            stress_healed_per_turn=stress_healed,
            rerolls_per_roll=rerolls,
            free_actions_per_turn=free_actions,
            wound_reduction=wound_reduction,
            sanity_reduction=sanity_reduction,
        )

    @classmethod
    def from_character_data(
        cls,
        character_data: CharacterData,
        special_power_level: int = 1,
        common_power_1_level: int = 1,
        common_power_2_level: int = 1,
        power_data: Optional[dict] = None,
    ) -> "CharacterBuild":
        """Create CharacterBuild from CharacterData.

        Args:
            character_data: Character data with power names
            special_power_level: Level of special power (default 1)
            common_power_1_level: Level of first common power (default 1)
            common_power_2_level: Level of second common power (default 1)
            power_data: Dictionary mapping power names to CommonPower objects

        Returns:
            CharacterBuild instance
        """
        build = cls(
            character_name=character_data.name,
            character_data=character_data,
            special_power_level=special_power_level,
            common_power_1_level=common_power_1_level,
            common_power_2_level=common_power_2_level,
        )

        # Set common power names from character data
        if character_data.common_powers:
            if len(character_data.common_powers) >= 1:
                build.common_power_1_name = character_data.common_powers[0]
            if len(character_data.common_powers) >= 2:
                build.common_power_2_name = character_data.common_powers[1]

        # Load power data if provided
        if power_data:
            # Load special power (if character has one)
            if character_data.special_power:
                # TODO: Load special power data from power_data
                pass

            # Load common power 1
            if build.common_power_1_name and build.common_power_1_name in power_data:
                power = power_data[build.common_power_1_name]
                for level_data in power.levels:
                    if level_data.level == common_power_1_level:
                        build._common_power_1_data = level_data
                        break

            # Load common power 2
            if build.common_power_2_name and build.common_power_2_name in power_data:
                power = power_data[build.common_power_2_name]
                for level_data in power.levels:
                    if level_data.level == common_power_2_level:
                        build._common_power_2_data = level_data
                        break

        return build
