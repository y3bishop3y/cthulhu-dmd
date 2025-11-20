#!/usr/bin/env python3
"""
Pydantic models for Cthulhu: Death May Die game mechanics.

This module defines the core game mechanics elements including dice,
dice faces, rolls, sanity, and insanity thresholds.
"""

from enum import Enum
from typing import Dict, Final, List, Optional

from pydantic import BaseModel, Field


class DiceType(str, Enum):
    """Type of dice."""

    BLACK = "black"
    GREEN = "green"


class DiceFaceSymbol(str, Enum):
    """Symbols that can appear on dice faces."""

    SUCCESS = "success"  # Star icon
    ELDER_SIGN = "elder_sign"  # Elder Sign icon
    TENTACLE = "tentacle"  # Tentacle icon (madness)
    BLANK = "blank"  # No symbol


class DiceFace(BaseModel):
    """Represents a single face of a die."""

    symbol: DiceFaceSymbol = Field(..., description="The symbol on this face")
    icon: str = Field(..., description="Icon name for the symbol")
    description: str = Field(..., description="What this face means")
    effect: str = Field(..., description="The effect of rolling this face")


class Dice(BaseModel):
    """Represents a die or set of dice."""

    type: DiceType = Field(..., description="Type of dice (black or green)")
    count: int = Field(1, ge=1, description="Number of dice")
    description: Optional[str] = Field(None, description="Description of these dice")


class StandardDice(BaseModel):
    """Standard dice configuration for investigator rolls."""

    type: DiceType = Field(DiceType.BLACK, description="Standard dice are black")
    count: int = Field(3, description="Always roll 3 standard black dice")
    description: str = Field(
        default="Standard black dice that are always rolled when making a roll",
        description="Description of standard dice",
    )


class BonusDice(BaseModel):
    """Bonus dice configuration."""

    type: DiceType = Field(DiceType.GREEN, description="Bonus dice are green")
    description: str = Field(
        default="Bonus green dice added by skills, cards, or insanity thresholds. "
        "There is no limit to the number of bonus dice that may be added to a roll.",
        description="Description of bonus dice",
    )


class InvestigatorRoll(BaseModel):
    """Configuration for investigator rolls."""

    standard_dice_count: int = Field(3, description="Always roll 3 standard black dice")
    standard_dice_type: DiceType = Field(DiceType.BLACK, description="Standard dice type")
    bonus_dice_type: DiceType = Field(DiceType.GREEN, description="Bonus dice type")
    description: str = Field(
        default="When investigators make a roll, you always roll 3 standard black dice "
        "(and may also be allowed to add bonus green dice).",
        description="How investigator rolls work",
    )


class SanityCost(BaseModel):
    """Sanity cost for tentacle symbols."""

    per_tentacle: int = Field(1, description="Sanity lost per tentacle symbol")
    description: str = Field(
        default="For each tentacle rolled, you lose 1 sanity, moving your tracker 1 space to the right. "
        "This applies to EVERY roll - attacking, being attacked, or just making a roll.",
        description="How tentacles affect sanity",
    )


class InsanityThreshold(BaseModel):
    """Represents an insanity threshold (red sanity marker)."""

    symbol: str = Field("red_swirl", description="Symbol representing the threshold")
    description: str = Field(
        default="Reaching certain Insanity Thresholds will add permanent bonus dice to all your rolls. "
        "The red swirl symbol indicates when sanity reaches a threshold where powers activate or bonus dice are gained.",
        description="What insanity thresholds mean",
    )


class GameMechanics(BaseModel):
    """Complete game mechanics configuration."""

    dice_faces: List[DiceFace] = Field(
        default_factory=lambda: [
            DiceFace(
                symbol=DiceFaceSymbol.SUCCESS,
                icon="star",
                description="This means that you (or the enemy) succeeded at your attempt (or partially succeeded). "
                "If you were attacking, it means you hit. If an enemy is attacking, it means they hit you. "
                "In some cases, you need to reach a target amount of successes in a single roll.",
                effect="success",
            ),
            DiceFace(
                symbol=DiceFaceSymbol.ELDER_SIGN,
                icon="elder_sign",
                description="These mean nothing unless you have a skill or card that uses them.",
                effect="none_unless_skill_or_card",
            ),
            DiceFace(
                symbol=DiceFaceSymbol.TENTACLE,
                icon="tentacle",
                description="Madness! For each tentacle, you lose 1 sanity, moving your tracker 1 space to the right. "
                "IMPORTANT: Tentacles on EVERY roll cost you sanity, whether you're attacking, being attacked, "
                "or just \"making a roll\".",
                effect="lose_1_sanity",
            ),
            DiceFace(
                symbol=DiceFaceSymbol.BLANK,
                icon="blank",
                description="No effect",
                effect="none",
            ),
        ],
        description="All possible dice face symbols",
    )
    standard_dice: StandardDice = Field(
        default_factory=StandardDice,
        description="Standard dice configuration",
    )
    bonus_dice: BonusDice = Field(
        default_factory=BonusDice,
        description="Bonus dice configuration",
    )
    investigator_rolls: InvestigatorRoll = Field(
        default_factory=InvestigatorRoll,
        description="How investigator rolls work",
    )
    sanity_cost: SanityCost = Field(
        default_factory=SanityCost,
        description="Sanity cost for tentacles",
    )
    insanity_threshold: InsanityThreshold = Field(
        default_factory=InsanityThreshold,
        description="Insanity threshold (red sanity marker)",
    )


# Constants for use in parsing
DICE_FACE_SYMBOLS: Final[Dict[str, DiceFaceSymbol]] = {
    "success": DiceFaceSymbol.SUCCESS,
    "star": DiceFaceSymbol.SUCCESS,
    "elder_sign": DiceFaceSymbol.ELDER_SIGN,
    "tentacle": DiceFaceSymbol.TENTACLE,
    "blank": DiceFaceSymbol.BLANK,
}

DICE_TYPE_NAMES: Final[Dict[str, DiceType]] = {
    "black": DiceType.BLACK,
    "green": DiceType.GREEN,
}

