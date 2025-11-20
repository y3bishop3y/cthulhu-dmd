#!/usr/bin/env python3
"""
Probability calculations for Cthulhu: Death May Die dice mechanics.

Calculates probabilities for success, tentacle, elder sign outcomes
when rolling combinations of black and green dice.
"""

from collections import defaultdict
from typing import Dict, Final

from pydantic import BaseModel, Field, computed_field

from scripts.models.game_mechanics import (
    BonusDice,
    DiceFaceSymbol,
    DiceType,
    StandardDice,
)

# Constants
FACES_PER_DIE: Final[int] = 6
PROBABILITY_PER_FACE: Final[float] = 1.0 / FACES_PER_DIE
BASE_BLACK_DICE_COUNT: Final[int] = 3  # Standard starting dice
BASE_GREEN_DICE_COUNT: Final[int] = 0  # No green dice at start

# Constants for black dice face counts
BLACK_PURE_SUCCESS_FACES: Final[int] = 2
BLACK_SUCCESS_TENTACLE_FACES: Final[int] = 1
BLACK_TENTACLE_FACES: Final[int] = 1
BLACK_ELDER_SIGN_FACES: Final[int] = 1
BLACK_BLANK_FACES: Final[int] = 1

# Constants for green dice face counts
GREEN_BLANK_FACES: Final[int] = 2
GREEN_ELDER_SIGN_FACES: Final[int] = 1
GREEN_PURE_SUCCESS_FACES: Final[int] = 2
GREEN_ELDER_SUCCESS_FACES: Final[int] = 1


class SingleDieStats(BaseModel):
    """Statistics for a single die.

    Encapsulates all probability calculations for a single die.
    """

    dice_type: DiceType = Field(..., description="Type of dice (black or green)")
    face_probabilities: Dict[str, float] = Field(..., description="Probability of each symbol type")

    @classmethod
    def from_dice(cls, dice_type: DiceType, dice: StandardDice | BonusDice) -> "SingleDieStats":
        """Create SingleDieStats from a dice model by computing probabilities.

        Args:
            dice_type: Type of dice
            dice: Dice model with faces

        Returns:
            SingleDieStats with computed probabilities
        """
        probs: Dict[str, float] = defaultdict(float)

        for face in dice.faces:
            # Count each symbol on this face
            for symbol in face.symbols:
                probs[symbol.value] += face.probability

            # Also track combinations
            if len(face.symbols) > 1:
                combo_key = "+".join(sorted([s.value for s in face.symbols]))
                probs[combo_key] = face.probability

        return cls(dice_type=dice_type, face_probabilities=dict(probs))

    @computed_field
    @property
    def success_prob(self) -> float:
        """Probability of at least 1 success."""
        if self.dice_type == DiceType.BLACK:
            success_tentacle_key = f"{DiceFaceSymbol.SUCCESS.value}+{DiceFaceSymbol.TENTACLE.value}"
            pure_success = self.face_probabilities.get(DiceFaceSymbol.SUCCESS.value, 0.0)
            combo_success = self.face_probabilities.get(success_tentacle_key, 0.0)
            return (pure_success - combo_success) + combo_success
        else:  # GREEN
            elder_success_key = f"{DiceFaceSymbol.ELDER_SIGN.value}+{DiceFaceSymbol.SUCCESS.value}"
            pure_success = self.face_probabilities.get(DiceFaceSymbol.SUCCESS.value, 0.0)
            combo_success = self.face_probabilities.get(elder_success_key, 0.0)
            return (pure_success - combo_success) + combo_success

    @computed_field
    @property
    def pure_success_prob(self) -> float:
        """Probability of pure success (no tentacle/elder sign)."""
        if self.dice_type == DiceType.BLACK:
            success_tentacle_key = f"{DiceFaceSymbol.SUCCESS.value}+{DiceFaceSymbol.TENTACLE.value}"
            return self.face_probabilities.get(
                DiceFaceSymbol.SUCCESS.value, 0.0
            ) - self.face_probabilities.get(success_tentacle_key, 0.0)
        else:  # GREEN
            elder_success_key = f"{DiceFaceSymbol.ELDER_SIGN.value}+{DiceFaceSymbol.SUCCESS.value}"
            return self.face_probabilities.get(
                DiceFaceSymbol.SUCCESS.value, 0.0
            ) - self.face_probabilities.get(elder_success_key, 0.0)

    @computed_field
    @property
    def tentacle_prob(self) -> float:
        """Probability of getting at least 1 tentacle."""
        if self.dice_type == DiceType.BLACK:
            success_tentacle_key = f"{DiceFaceSymbol.SUCCESS.value}+{DiceFaceSymbol.TENTACLE.value}"
            return self.face_probabilities.get(
                DiceFaceSymbol.TENTACLE.value, 0.0
            ) + self.face_probabilities.get(success_tentacle_key, 0.0)
        return 0.0  # Green dice have no tentacles

    @computed_field
    @property
    def elder_sign_prob(self) -> float:
        """Probability of getting at least 1 elder sign."""
        if self.dice_type == DiceType.BLACK:
            return self.face_probabilities.get(DiceFaceSymbol.ELDER_SIGN.value, 0.0)
        else:  # GREEN
            elder_success_key = f"{DiceFaceSymbol.ELDER_SIGN.value}+{DiceFaceSymbol.SUCCESS.value}"
            return self.face_probabilities.get(
                DiceFaceSymbol.ELDER_SIGN.value, 0.0
            ) + self.face_probabilities.get(elder_success_key, 0.0)

    @computed_field
    @property
    def blank_prob(self) -> float:
        """Probability of blank."""
        return self.face_probabilities.get(DiceFaceSymbol.BLANK.value, 0.0)

    @computed_field
    @property
    def expected_successes(self) -> float:
        """Expected number of successes per die."""
        if self.dice_type == DiceType.BLACK:
            # Black: 2 pure success + 1 success+tentacle = 3/6 = 0.5
            return (
                BLACK_PURE_SUCCESS_FACES * PROBABILITY_PER_FACE
                + BLACK_SUCCESS_TENTACLE_FACES * PROBABILITY_PER_FACE
            )
        else:  # GREEN
            # Green: 2 pure success + 1 elder+success = 3/6 = 0.5
            return (
                GREEN_PURE_SUCCESS_FACES * PROBABILITY_PER_FACE
                + GREEN_ELDER_SUCCESS_FACES * PROBABILITY_PER_FACE
            )

    @computed_field
    @property
    def success_percentage(self) -> float:
        """Success probability as a percentage."""
        return self.success_prob * 100.0

    @computed_field
    @property
    def tentacle_percentage(self) -> float:
        """Tentacle probability as a percentage."""
        return self.tentacle_prob * 100.0

    @computed_field
    @property
    def elder_sign_percentage(self) -> float:
        """Elder sign probability as a percentage."""
        return self.elder_sign_prob * 100.0


class CombinedRollStats(BaseModel):
    """Statistics for rolling multiple dice together.

    Encapsulates all probability calculations for combined dice rolls.
    """

    black_dice: int = Field(..., ge=0, description="Number of black dice")
    green_dice: int = Field(..., ge=0, description="Number of green dice")
    black_stats: SingleDieStats = Field(..., description="Statistics for black dice")
    green_stats: SingleDieStats = Field(..., description="Statistics for green dice")

    @classmethod
    def from_counts(
        cls,
        black_count: int,
        green_count: int,
        black_stats: SingleDieStats,
        green_stats: SingleDieStats,
    ) -> "CombinedRollStats":
        """Create CombinedRollStats from dice counts and single die statistics.

        Args:
            black_count: Number of black dice
            green_count: Number of green dice
            black_stats: Statistics for a single black die
            green_stats: Statistics for a single green die

        Returns:
            CombinedRollStats with computed probabilities
        """
        return cls(
            black_dice=black_count,
            green_dice=green_count,
            black_stats=black_stats,
            green_stats=green_stats,
        )

    @computed_field
    @property
    def total_dice(self) -> int:
        """Total number of dice rolled."""
        return self.black_dice + self.green_dice

    @computed_field
    @property
    def expected_successes(self) -> float:
        """Expected number of successes."""
        return (
            self.black_stats.expected_successes * self.black_dice
            + self.green_stats.expected_successes * self.green_dice
        )

    @computed_field
    @property
    def expected_tentacles(self) -> float:
        """Expected number of tentacles."""
        return self.black_stats.tentacle_prob * self.black_dice

    @computed_field
    @property
    def expected_elder_signs(self) -> float:
        """Expected number of elder signs."""
        return (
            self.black_stats.elder_sign_prob * self.black_dice
            + self.green_stats.elder_sign_prob * self.green_dice
        )

    @computed_field
    @property
    def prob_at_least_1_success(self) -> float:
        """Probability of at least 1 success."""
        p_success_black = self.black_stats.success_prob
        p_success_green = self.green_stats.success_prob
        return 1.0 - (
            (1.0 - p_success_black) ** self.black_dice * (1.0 - p_success_green) ** self.green_dice
        )

    @computed_field
    @property
    def prob_at_least_1_tentacle(self) -> float:
        """Probability of at least 1 tentacle."""
        return 1.0 - (1.0 - self.black_stats.tentacle_prob) ** self.black_dice

    @computed_field
    @property
    def prob_at_least_1_elder(self) -> float:
        """Probability of at least 1 elder sign."""
        return 1.0 - (
            (1.0 - self.black_stats.elder_sign_prob) ** self.black_dice
            * (1.0 - self.green_stats.elder_sign_prob) ** self.green_dice
        )

    @computed_field
    @property
    def max_possible_successes(self) -> int:
        """Theoretical maximum successes (all dice succeed)."""
        return self.total_dice

    @computed_field
    @property
    def success_percentage(self) -> float:
        """Probability of at least 1 success as a percentage."""
        return self.prob_at_least_1_success * 100.0

    @computed_field
    @property
    def tentacle_percentage(self) -> float:
        """Probability of at least 1 tentacle as a percentage."""
        return self.prob_at_least_1_tentacle * 100.0

    @computed_field
    @property
    def elder_percentage(self) -> float:
        """Probability of at least 1 elder sign as a percentage."""
        return self.prob_at_least_1_elder * 100.0

    def get_summary(self) -> str:
        """Get a human-readable summary of the roll statistics."""
        return (
            f"{self.black_dice} black + {self.green_dice} green = {self.total_dice} dice: "
            f"Expected {self.expected_successes:.2f} successes, "
            f"{self.expected_tentacles:.2f} tentacles, "
            f"{self.expected_elder_signs:.2f} elder signs. "
            f"Max: {self.max_possible_successes} successes."
        )


class PowerImpactImprovement(BaseModel):
    """Improvement metrics when a power adds dice.

    Encapsulates calculation of improvement metrics.
    """

    base_stats: CombinedRollStats = Field(..., description="Base statistics")
    enhanced_stats: CombinedRollStats = Field(..., description="Enhanced statistics")

    @computed_field
    @property
    def expected_successes_increase(self) -> float:
        """Absolute increase in expected successes."""
        return self.enhanced_stats.expected_successes - self.base_stats.expected_successes

    @computed_field
    @property
    def expected_successes_percent_increase(self) -> float:
        """Percentage increase in expected successes."""
        if self.base_stats.expected_successes > 0:
            return (
                (self.enhanced_stats.expected_successes - self.base_stats.expected_successes)
                / self.base_stats.expected_successes
                * 100
            )
        return 0.0

    @computed_field
    @property
    def max_successes_increase(self) -> int:
        """Increase in maximum possible successes."""
        return self.enhanced_stats.max_possible_successes - self.base_stats.max_possible_successes

    @computed_field
    @property
    def tentacle_risk(self) -> float:
        """Expected tentacles (same as base, green dice have no tentacles)."""
        return self.enhanced_stats.expected_tentacles

    @computed_field
    @property
    def is_significant_improvement(self) -> bool:
        """Check if the improvement is significant (>10% increase)."""
        return self.expected_successes_percent_increase > 10.0


class PowerImpact(BaseModel):
    """Complete analysis of how a power impacts dice roll statistics.

    Encapsulates calculation of power impact analysis.
    """

    base: CombinedRollStats = Field(..., description="Statistics with base dice only")
    enhanced: CombinedRollStats = Field(..., description="Statistics with power enhancement")

    @computed_field
    @property
    def improvement(self) -> PowerImpactImprovement:
        """Improvement metrics computed from base and enhanced stats."""
        return PowerImpactImprovement(base_stats=self.base, enhanced_stats=self.enhanced)

    @computed_field
    @property
    def total_dice_increase(self) -> int:
        """Total number of additional dice added."""
        return self.enhanced.total_dice - self.base.total_dice

    def get_summary(self) -> str:
        """Get a human-readable summary of the power impact."""
        return (
            f"Base: {self.base.get_summary()}\n"
            f"Enhanced: {self.enhanced.get_summary()}\n"
            f"Improvement: +{self.improvement.expected_successes_increase:.2f} successes "
            f"({self.improvement.expected_successes_percent_increase:.1f}%), "
            f"+{self.improvement.max_successes_increase} max successes"
        )


class DiceProbabilityCalculator:
    """Calculate probabilities for dice roll outcomes."""

    def __init__(self):
        """Initialize with standard dice configurations."""
        self.black_dice = StandardDice()
        self.green_dice = BonusDice()

    def get_face_probabilities(self, dice_type: DiceType) -> Dict[str, float]:
        """Get probability of each symbol type for a single die.

        Args:
            dice_type: Type of dice (DiceType.BLACK or DiceType.GREEN)

        Returns:
            Dictionary with probabilities for each symbol type
        """
        if dice_type == DiceType.BLACK:
            dice = self.black_dice
        elif dice_type == DiceType.GREEN:
            dice = self.green_dice
        else:
            raise ValueError(f"Unknown dice type: {dice_type}")

        probs: Dict[str, float] = defaultdict(float)

        for face in dice.faces:
            # Count each symbol on this face
            for symbol in face.symbols:
                probs[symbol.value] += face.probability

            # Also track combinations
            if len(face.symbols) > 1:
                combo_key = "+".join(sorted([s.value for s in face.symbols]))
                probs[combo_key] = face.probability

        return dict(probs)

    def calculate_single_die_stats(self, dice_type: DiceType) -> SingleDieStats:
        """Calculate statistics for a single die.

        Args:
            dice_type: Type of dice (DiceType.BLACK or DiceType.GREEN)

        Returns:
            SingleDieStats model with all statistics computed
        """
        if dice_type == DiceType.BLACK:
            dice = self.black_dice
        elif dice_type == DiceType.GREEN:
            dice = self.green_dice
        else:
            raise ValueError(f"Unknown dice type: {dice_type}")

        return SingleDieStats.from_dice(dice_type, dice)

    def calculate_combined_stats(self, black_count: int, green_count: int) -> CombinedRollStats:
        """Calculate statistics for rolling multiple dice.

        Args:
            black_count: Number of black dice
            green_count: Number of green dice

        Returns:
            CombinedRollStats model with combined statistics computed
        """
        black_stats = self.calculate_single_die_stats(DiceType.BLACK)
        green_stats = self.calculate_single_die_stats(DiceType.GREEN)

        return CombinedRollStats.from_counts(black_count, green_count, black_stats, green_stats)

    def calculate_power_impact(
        self, base_black: int, base_green: int, power_adds_green: int
    ) -> PowerImpact:
        """Calculate how a power that adds green dice impacts roll statistics.

        Args:
            base_black: Base number of black dice (usually 3)
            base_green: Base number of green dice (usually 0)
            power_adds_green: Number of green dice the power adds

        Returns:
            PowerImpact model comparing base vs enhanced statistics
        """
        base_stats = self.calculate_combined_stats(base_black, base_green)
        enhanced_stats = self.calculate_combined_stats(base_black, base_green + power_adds_green)

        return PowerImpact(base=base_stats, enhanced=enhanced_stats)


# Convenience functions
def get_single_die_stats(dice_type: DiceType) -> SingleDieStats:
    """Get statistics for a single die.

    Args:
        dice_type: Type of dice (DiceType.BLACK or DiceType.GREEN)

    Returns:
        SingleDieStats model with statistics
    """
    calculator = DiceProbabilityCalculator()
    return calculator.calculate_single_die_stats(dice_type)


def get_combined_stats(black_count: int, green_count: int) -> CombinedRollStats:
    """Get statistics for rolling multiple dice.

    Args:
        black_count: Number of black dice
        green_count: Number of green dice

    Returns:
        CombinedRollStats model with statistics
    """
    calculator = DiceProbabilityCalculator()
    return calculator.calculate_combined_stats(black_count, green_count)


def analyze_power_dice_impact(
    base_black: int, base_green: int, power_adds_green: int
) -> PowerImpact:
    """Analyze how a power impacts dice roll statistics.

    Args:
        base_black: Base number of black dice (usually 3)
        base_green: Base number of green dice (usually 0)
        power_adds_green: Number of green dice the power adds

    Returns:
        PowerImpact model with complete analysis
    """
    calculator = DiceProbabilityCalculator()
    return calculator.calculate_power_impact(base_black, base_green, power_adds_green)
