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

    symbols: List[DiceFaceSymbol] = Field(
        ..., description="The symbols on this face (can be multiple, e.g., Success+Tentacle)"
    )
    icon: str = Field(..., description="Icon name for the symbol(s)")
    description: str = Field(..., description="What this face means")
    effect: str = Field(..., description="The effect of rolling this face")
    probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of rolling this face (out of 6 faces)"
    )
    image_path: Optional[str] = Field(
        None,
        description="Path to image/PDF showing this dice face (relative to data directory)",
    )
    rulebook_reference: Optional[str] = Field(
        None,
        description="Reference to rulebook PDF page/section where this dice face is documented",
    )


class Dice(BaseModel):
    """Represents a die or set of dice."""

    type: DiceType = Field(..., description="Type of dice (black or green)")
    count: int = Field(1, ge=1, description="Number of dice")
    faces: List[DiceFace] = Field(
        ..., description="The 6 faces of this die with their probabilities"
    )
    description: Optional[str] = Field(None, description="Description of these dice")


class StandardDice(BaseModel):
    """Standard dice configuration for investigator rolls.
    
    Black dice have 6 faces:
    - 1 Success (1/6 = 16.67%)
    - 1 Tentacle (1/6 = 16.67%)
    - 1 Success + Tentacle (1/6 = 16.67%)
    - 1 Success (1/6 = 16.67%)
    - 1 Elder Sign (1/6 = 16.67%)
    - 1 Blank (1/6 = 16.67%)
    
    So: 2 pure Successes, 1 Success+Tentacle, 1 Tentacle, 1 Elder Sign, 1 Blank
    
    Dice face images are documented in: data/DMD_Rulebook_web.pdf (page 11-12)
    """

    type: DiceType = Field(DiceType.BLACK, description="Standard dice are black")
    count: int = Field(3, description="Always roll 3 standard black dice")
    rulebook_reference: str = Field(
        default="data/DMD_Rulebook_web.pdf (pages 11-12)",
        description="Reference to rulebook where dice faces are documented",
    )
    faces: List[DiceFace] = Field(
        default_factory=lambda: [
            DiceFace(
                symbols=[DiceFaceSymbol.SUCCESS],
                icon="star",
                description="Success - you succeeded at your attempt",
                effect="success",
                probability=1.0 / 6.0,  # 1 out of 6 faces
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.TENTACLE],
                icon="tentacle",
                description="Tentacle - lose 1 sanity",
                effect="lose_1_sanity",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.SUCCESS, DiceFaceSymbol.TENTACLE],
                icon="star_tentacle",
                description="Success + Tentacle - you succeeded but lose 1 sanity",
                effect="success_and_lose_1_sanity",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.SUCCESS],
                icon="star",
                description="Success - you succeeded at your attempt",
                effect="success",
                probability=1.0 / 6.0,  # Second success face
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.ELDER_SIGN],
                icon="elder_sign",
                description="Elder Sign - means nothing unless you have a skill or card that uses them",
                effect="none_unless_skill_or_card",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.BLANK],
                icon="blank",
                description="Blank - no effect",
                effect="none",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
        ],
        description="The 6 faces of a black die",
    )
    description: str = Field(
        default="Standard black dice that are always rolled when making a roll. "
        "Each die has 6 faces: 2 Success, 1 Success+Tentacle, 1 Tentacle, 1 Elder Sign, 1 Blank.",
        description="Description of standard dice",
    )


class BonusDice(BaseModel):
    """Bonus dice configuration.
    
    Green dice have 6 faces:
    - 2 Blank (2/6 = 33.33%)
    - 1 Elder Sign (1/6 = 16.67%)
    - 2 Success (2/6 = 33.33%)
    - 1 Elder Sign + Success (1/6 = 16.67%)
    
    So: 2 Blank, 1 Elder Sign, 2 Success, 1 Elder Sign+Success
    
    Dice face images are documented in: data/DMD_Rulebook_web.pdf (page 11-12)
    """

    type: DiceType = Field(DiceType.GREEN, description="Bonus dice are green")
    rulebook_reference: str = Field(
        default="data/DMD_Rulebook_web.pdf (pages 11-12)",
        description="Reference to rulebook where dice faces are documented",
    )
    faces: List[DiceFace] = Field(
        default_factory=lambda: [
            # 2 Blank faces
            DiceFace(
                symbols=[DiceFaceSymbol.BLANK],
                icon="blank",
                description="Blank - no effect",
                effect="none",
                probability=1.0 / 6.0,  # First blank face
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.BLANK],
                icon="blank",
                description="Blank - no effect",
                effect="none",
                probability=1.0 / 6.0,  # Second blank face
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            # 1 Elder Sign face
            DiceFace(
                symbols=[DiceFaceSymbol.ELDER_SIGN],
                icon="elder_sign",
                description="Elder Sign - means nothing unless you have a skill or card that uses them",
                effect="none_unless_skill_or_card",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            # 2 Success faces
            DiceFace(
                symbols=[DiceFaceSymbol.SUCCESS],
                icon="star",
                description="Success - you succeeded at your attempt",
                effect="success",
                probability=1.0 / 6.0,  # First success face
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            DiceFace(
                symbols=[DiceFaceSymbol.SUCCESS],
                icon="star",
                description="Success - you succeeded at your attempt",
                effect="success",
                probability=1.0 / 6.0,  # Second success face
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
            # 1 Elder Sign + Success face
            DiceFace(
                symbols=[DiceFaceSymbol.ELDER_SIGN, DiceFaceSymbol.SUCCESS],
                icon="elder_sign_star",
                description="Elder Sign + Success - you succeeded, and elder sign may be used by skills/cards",
                effect="success_and_elder_sign",
                probability=1.0 / 6.0,
                rulebook_reference="DMD_Rulebook_web.pdf page 11",
            ),
        ],
        description="The 6 faces of a green die: 2 Blank, 1 Elder Sign, 2 Success, 1 Elder Sign+Success",
    )
    description: str = Field(
        default="Bonus green dice added by skills, cards, or insanity thresholds. "
        "There is no limit to the number of bonus dice that may be added to a roll. "
        "Each die has 6 faces: 2 Blank, 1 Elder Sign, 2 Success, 1 Elder Sign+Success.",
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

    standard_dice: StandardDice = Field(
        default_factory=StandardDice,
        description="Standard dice configuration (black dice)",
    )
    bonus_dice: BonusDice = Field(
        default_factory=BonusDice,
        description="Bonus dice configuration (green dice)",
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

# Paths to game mechanics documentation
RULEBOOK_PDF_PATH: Final[str] = "data/DMD_Rulebook_web.pdf"
RULEBOOK_DICE_PAGES: Final[List[int]] = [11, 12]  # Pages where dice faces are documented


def get_rulebook_path() -> str:
    """Get the path to the rulebook PDF."""
    return RULEBOOK_PDF_PATH


def get_dice_reference_pages() -> List[int]:
    """Get the page numbers where dice faces are documented."""
    return RULEBOOK_DICE_PAGES.copy()

