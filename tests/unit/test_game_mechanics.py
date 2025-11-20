#!/usr/bin/env python3
"""
Unit tests for game mechanics models.

Tests the Pydantic models for dice, faces, and game mechanics.
"""

import pytest

from scripts.models.game_mechanics import (
    BonusDice,
    DiceFaceSymbol,
    DiceType,
    GameMechanics,
    StandardDice,
)


class TestDiceType:
    """Test DiceType enum."""

    def test_dice_type_values(self):
        """Test dice type enum values."""
        assert DiceType.BLACK.value == "black"
        assert DiceType.GREEN.value == "green"


class TestDiceFaceSymbol:
    """Test DiceFaceSymbol enum."""

    def test_symbol_values(self):
        """Test dice face symbol enum values."""
        assert DiceFaceSymbol.SUCCESS.value == "success"
        assert DiceFaceSymbol.TENTACLE.value == "tentacle"
        assert DiceFaceSymbol.ELDER_SIGN.value == "elder_sign"
        assert DiceFaceSymbol.BLANK.value == "blank"


class TestStandardDice:
    """Test StandardDice model."""

    def test_standard_dice_creation(self):
        """Test standard dice can be created."""
        dice = StandardDice()

        assert dice.type == DiceType.BLACK
        assert dice.count == 3
        assert len(dice.faces) == 6  # 6 faces per die

    def test_standard_dice_faces(self):
        """Test standard dice has correct faces."""
        dice = StandardDice()

        # Should have faces with success, tentacle, elder_sign, blank
        success_faces = [face for face in dice.faces if DiceFaceSymbol.SUCCESS in face.symbols]
        tentacle_faces = [face for face in dice.faces if DiceFaceSymbol.TENTACLE in face.symbols]
        elder_sign_faces = [
            face for face in dice.faces if DiceFaceSymbol.ELDER_SIGN in face.symbols
        ]
        blank_faces = [face for face in dice.faces if DiceFaceSymbol.BLANK in face.symbols]

        assert len(success_faces) >= 2  # At least 2 success faces
        assert len(tentacle_faces) >= 1  # At least 1 tentacle face
        assert len(elder_sign_faces) >= 1  # At least 1 elder sign face
        assert len(blank_faces) >= 1  # At least 1 blank face

    def test_standard_dice_probabilities(self):
        """Test standard dice face probabilities sum to 1."""
        dice = StandardDice()

        total_prob = sum(face.probability for face in dice.faces)
        assert total_prob == pytest.approx(1.0, rel=0.01)

        # Each face should have probability 1/6
        for face in dice.faces:
            assert face.probability == pytest.approx(1.0 / 6.0, rel=0.01)


class TestBonusDice:
    """Test BonusDice model."""

    def test_bonus_dice_creation(self):
        """Test bonus dice can be created."""
        dice = BonusDice()

        assert dice.type == DiceType.GREEN
        assert len(dice.faces) == 6  # 6 faces per die

    def test_bonus_dice_no_tentacles(self):
        """Test bonus dice has no tentacle faces."""
        dice = BonusDice()

        tentacle_faces = [face for face in dice.faces if DiceFaceSymbol.TENTACLE in face.symbols]

        assert len(tentacle_faces) == 0  # No tentacles in green dice

    def test_bonus_dice_probabilities(self):
        """Test bonus dice face probabilities sum to 1."""
        dice = BonusDice()

        total_prob = sum(face.probability for face in dice.faces)
        assert total_prob == pytest.approx(1.0, rel=0.01)

        # Each face should have probability 1/6
        for face in dice.faces:
            assert face.probability == pytest.approx(1.0 / 6.0, rel=0.01)


class TestGameMechanics:
    """Test GameMechanics model."""

    def test_game_mechanics_creation(self):
        """Test game mechanics can be created."""
        mechanics = GameMechanics()

        assert mechanics.standard_dice is not None
        assert mechanics.bonus_dice is not None
        assert mechanics.investigator_rolls is not None
        assert mechanics.sanity_cost is not None
        assert mechanics.insanity_threshold is not None

    def test_investigator_rolls(self):
        """Test investigator rolls configuration."""
        mechanics = GameMechanics()

        assert mechanics.investigator_rolls.standard_dice_count == 3
        assert mechanics.investigator_rolls.standard_dice_type == DiceType.BLACK
        assert mechanics.investigator_rolls.bonus_dice_type == DiceType.GREEN
