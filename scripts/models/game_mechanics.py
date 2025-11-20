#!/usr/bin/env python3
"""
Pydantic models for Cthulhu: Death May Die game mechanics.

This module defines the core game mechanics elements including dice,
dice faces, rolls, sanity, and insanity thresholds.
"""

from enum import Enum
from typing import Dict, Final, List, Optional

from pydantic import BaseModel, Field, computed_field


class DiceType(str, Enum):
    """Type of dice."""

    BLACK = "black"
    GREEN = "green"


class ActionType(str, Enum):
    """Type of action that can be added by powers."""

    ATTACK = "attack"
    MOVE = "move"
    RUN = "run"
    REST = "rest"
    INVESTIGATE = "investigate"
    TRADE = "trade"
    ACTION = "action"  # Generic action


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


class InsanityTrack(BaseModel):
    """Represents a character's insanity/madness track.

    Track has 20 slots (player starts at slot 1, dies at slot 21).
    Red swirls at slots: 5, 9, 13, 16, 19, 20 (6 total level-up opportunities).
    Green dice bonuses at red swirls: 2, 4, 5, 6 (slots 9, 16, 19, 20).
    """

    max_insanity: int = Field(default=20, ge=1, description="Maximum insanity slots (20)")
    current_insanity: int = Field(
        default=1, ge=1, description="Current insanity slot (1-21, 21 = death)"
    )
    death_threshold: int = Field(
        default=21, ge=1, description="Insanity value at which character dies (slot 21)"
    )

    # Red swirl positions (level-up opportunities)
    red_swirl_slots: List[int] = Field(
        default_factory=lambda: [5, 9, 13, 16, 19, 20],
        description="Slot positions of red swirls (level-up opportunities)",
    )

    # Green dice bonus positions (which red swirls grant green dice)
    green_dice_red_swirls: List[int] = Field(
        default_factory=lambda: [2, 4, 5, 6],
        description="Red swirl numbers (1-6) that grant green dice bonuses",
    )

    @computed_field
    @property
    def is_dead(self) -> bool:
        """Check if character is dead from madness (slot 21)."""
        return self.current_insanity >= self.death_threshold

    @computed_field
    @property
    def insanity_remaining(self) -> int:
        """Calculate remaining insanity slots before death."""
        return max(0, self.death_threshold - self.current_insanity)

    @computed_field
    @property
    def red_swirls_reached(self) -> int:
        """Count how many red swirls have been reached."""
        return sum(1 for slot in self.red_swirl_slots if self.current_insanity >= slot)

    @computed_field
    @property
    def level_ups_available(self) -> int:
        """Get number of level-ups available (red swirls reached)."""
        return self.red_swirls_reached

    @computed_field
    @property
    def level_ups_remaining(self) -> int:
        """Get number of level-ups remaining (max 6 total)."""
        return max(0, len(self.red_swirl_slots) - self.red_swirls_reached)

    @computed_field
    @property
    def green_dice_bonus(self) -> int:
        """Calculate total green dice bonus from red swirls reached."""
        bonus = 0
        for i, slot in enumerate(self.red_swirl_slots, start=1):
            if self.current_insanity >= slot and i in self.green_dice_red_swirls:
                bonus += 1
        return bonus

    @computed_field
    @property
    def next_red_swirl(self) -> Optional[int]:
        """Get the next red swirl slot, or None if all reached."""
        for slot in self.red_swirl_slots:
            if self.current_insanity < slot:
                return slot
        return None

    @computed_field
    @property
    def tentacles_until_death(self) -> int:
        """Calculate how many tentacles until death."""
        return max(0, self.death_threshold - self.current_insanity)

    @computed_field
    @property
    def tentacles_until_next_red_swirl(self) -> Optional[int]:
        """Calculate how many tentacles until next red swirl."""
        next_swirl = self.next_red_swirl
        if next_swirl is None:
            return None
        return max(0, next_swirl - self.current_insanity)

    def take_tentacle(self, count: int = 1, stop_at_red_swirl: bool = True) -> tuple[int, bool]:
        """Take tentacle(s) and advance insanity track.

        IMPORTANT: If stop_at_red_swirl is True, tentacles stop accumulating at the next red swirl.
        Example: At insanity 4, rolling 3 tentacles would normally go to 7, but stops at 5 (red swirl).

        Args:
            count: Number of tentacles taken (default 1)
            stop_at_red_swirl: If True, stop at next red swirl (default True)

        Returns:
            Tuple of (actual insanity gained, reached_red_swirl)
            - actual insanity gained: May be less if stopped at red swirl or death threshold
            - reached_red_swirl: True if stopped at a red swirl
        """
        if stop_at_red_swirl:
            # Check if there's a red swirl between current and target
            next_swirl = self.next_red_swirl
            if next_swirl is not None:
                # Calculate how many tentacles until next red swirl
                tentacles_to_swirl = next_swirl - self.current_insanity
                if count >= tentacles_to_swirl:
                    # Stop at red swirl
                    insanity_gained = tentacles_to_swirl
                    self.current_insanity = next_swirl
                    return (insanity_gained, True)

        # Normal progression (no red swirl in range, or stop_at_red_swirl=False)
        max_insanity = self.death_threshold - self.current_insanity
        insanity_gained = min(count, max_insanity)
        self.current_insanity += insanity_gained
        reached_swirl = self.reached_new_red_swirl()
        return (insanity_gained, reached_swirl)

    def reached_new_red_swirl(self) -> bool:
        """Check if current insanity just reached a new red swirl.

        Returns:
            True if current slot is exactly a red swirl position
        """
        return self.current_insanity in self.red_swirl_slots

    def take_tentacles_in_roll(self, tentacle_count: int) -> tuple[int, bool, Optional[int]]:
        """Take tentacles during a single roll/action, stopping at red swirls.

        This method implements the rule: when you hit a red swirl during a roll,
        you stop there and don't accumulate tentacles past it for that roll.

        Args:
            tentacle_count: Number of tentacles rolled

        Returns:
            Tuple of (insanity_gained, reached_red_swirl, red_swirl_number)
            - insanity_gained: Actual insanity gained (may be less if stopped at red swirl)
            - reached_red_swirl: True if stopped at a red swirl
            - red_swirl_number: Red swirl number (1-6) if reached, None otherwise
        """
        insanity_gained, reached_swirl = self.take_tentacle(tentacle_count, stop_at_red_swirl=True)
        red_swirl_num = None
        if reached_swirl:
            red_swirl_num = self.get_red_swirl_number(self.current_insanity)
        return (insanity_gained, reached_swirl, red_swirl_num)

    def get_red_swirl_number(self, slot: int) -> Optional[int]:
        """Get the red swirl number (1-6) for a given slot, or None if not a red swirl.

        Args:
            slot: Insanity slot number

        Returns:
            Red swirl number (1-6) or None
        """
        try:
            index = self.red_swirl_slots.index(slot)
            return index + 1  # Red swirls numbered 1-6
        except ValueError:
            return None


class HealthTrack(BaseModel):
    """Represents a character's health/wounds track.

    Health starts at 5 (all slots empty). Taking damage fills slots.
    6th hit (damage_taken = 6) = death.
    """

    max_health: int = Field(default=5, ge=1, description="Maximum health (5 slots)")
    damage_taken: int = Field(default=0, ge=0, description="Current damage taken (0-6, 6 = death)")
    death_threshold: int = Field(
        default=6, ge=1, description="Damage value at which character dies (6th hit)"
    )

    @computed_field
    @property
    def current_health(self) -> int:
        """Get current health value (max_health - damage_taken)."""
        return max(0, self.max_health - self.damage_taken)

    @computed_field
    @property
    def is_dead(self) -> bool:
        """Check if character is dead (6th hit)."""
        return self.damage_taken >= self.death_threshold

    @computed_field
    @property
    def health_remaining(self) -> int:
        """Calculate remaining health before death."""
        return max(0, self.death_threshold - self.damage_taken - 1)

    def take_damage(self, amount: int) -> int:
        """Take damage and return actual damage taken (capped at death threshold).

        Args:
            amount: Amount of damage to take

        Returns:
            Actual damage taken (may be less if it would exceed death threshold)
        """
        damage_taken = min(amount, self.death_threshold - self.damage_taken)
        self.damage_taken += damage_taken
        return damage_taken

    def heal(self, amount: int) -> int:
        """Heal health and return actual healing done.

        Args:
            amount: Amount of healing to apply

        Returns:
            Actual healing done (may be less if already at max)
        """
        healing_done = min(amount, self.damage_taken)
        self.damage_taken = max(0, self.damage_taken - healing_done)
        return healing_done


class StressTrack(BaseModel):
    """Represents a character's stress/sanity track."""

    max_stress: int = Field(default=5, ge=1, description="Maximum stress (5 slots)")
    current_stress: int = Field(default=0, ge=0, description="Current stress (0-5)")
    insanity_threshold: int = Field(
        default=10, ge=1, description="Stress value at which character goes insane"
    )

    @computed_field
    @property
    def is_insane(self) -> bool:
        """Check if character is insane."""
        return self.current_stress >= self.insanity_threshold

    @computed_field
    @property
    def stress_remaining(self) -> int:
        """Calculate remaining stress capacity."""
        return max(0, self.max_stress - self.current_stress)

    def take_stress(self, amount: int) -> int:
        """Take stress and return actual stress taken (capped at max).

        Args:
            amount: Amount of stress to take

        Returns:
            Actual stress taken (may be less if at max)
        """
        stress_taken = min(amount, self.max_stress - self.current_stress)
        self.current_stress += stress_taken
        return stress_taken

    def heal_stress(self, amount: int) -> int:
        """Heal stress and return actual healing done.

        Args:
            amount: Amount of stress healing to apply

        Returns:
            Actual healing done (may be less if already at 0)
        """
        healing_done = min(amount, self.current_stress)
        self.current_stress = max(0, self.current_stress - healing_done)
        return healing_done


class RestAction(BaseModel):
    """Represents a Rest action that provides healing points."""

    healing_points: int = Field(
        default=3, ge=1, description="Number of healing points provided (default 3)"
    )
    requires_safe_space: bool = Field(
        default=True, description="Whether rest requires a safe space"
    )

    def apply_healing(
        self,
        health_track: "HealthTrack",
        stress_track: "StressTrack",
        health_amount: int,
        stress_amount: int,
    ) -> tuple[int, int]:
        """Apply healing points to health and stress tracks.

        Args:
            health_track: Character's health track
            stress_track: Character's stress track
            health_amount: Amount of healing points to allocate to health
            stress_amount: Amount of healing points to allocate to stress

        Returns:
            Tuple of (actual health healed, actual stress healed)
        """
        total_requested = health_amount + stress_amount
        if total_requested > self.healing_points:
            # Scale down proportionally if over limit
            scale = self.healing_points / total_requested
            health_amount = int(health_amount * scale)
            stress_amount = int(stress_amount * scale)

        health_healed = health_track.heal(health_amount)
        stress_healed = stress_track.heal_stress(stress_amount)

        return (health_healed, stress_healed)


class TurnStructure(BaseModel):
    """Represents the structure of a player's turn."""

    actions_per_turn: int = Field(
        default=3, ge=1, description="Number of actions per turn (default 3)"
    )
    available_actions: List[ActionType] = Field(
        default_factory=lambda: [
            ActionType.RUN,
            ActionType.ATTACK,
            ActionType.REST,
            ActionType.TRADE,
            ActionType.INVESTIGATE,
        ],
        description="Available action types",
    )
    rest_action: RestAction = Field(
        default_factory=RestAction, description="Rest action configuration"
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
    turn_structure: TurnStructure = Field(
        default_factory=TurnStructure,
        description="Turn structure and actions",
    )
    default_health_track: HealthTrack = Field(
        default_factory=lambda: HealthTrack(),
        description="Default health track configuration",
    )
    default_stress_track: StressTrack = Field(
        default_factory=lambda: StressTrack(),
        description="Default stress track configuration",
    )
    default_insanity_track: InsanityTrack = Field(
        default_factory=lambda: InsanityTrack(),
        description="Default insanity track configuration",
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
