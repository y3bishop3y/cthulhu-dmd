#!/usr/bin/env python3
"""
Unit tests for PlayStrategy models.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from scripts.models.character_build import CharacterBuild, CharacterStatistics
from scripts.models.play_strategy import (
    PlayStrategy,
    PlayStrategyAnalyzer,
    Playstyle,
    UpgradeRecommendation,
)


class TestPlaystyle:
    """Test Playstyle enum."""

    def test_playstyle_values(self):
        """Test Playstyle enum values."""
        assert Playstyle.OFFENSIVE == "offensive"
        assert Playstyle.DEFENSIVE == "defensive"
        assert Playstyle.BALANCED == "balanced"
        assert Playstyle.UTILITY == "utility"
        assert Playstyle.SPECIALIST == "specialist"


class TestUpgradeRecommendation:
    """Test UpgradeRecommendation model."""

    def test_create_recommendation(self):
        """Test creating UpgradeRecommendation."""
        rec = UpgradeRecommendation(
            power_name="Marksman",
            current_level=1,
            recommended_level=2,
            reason="Adds green dice for safer attacks",
            priority=8,
        )

        assert rec.power_name == "Marksman"
        assert rec.current_level == 1
        assert rec.recommended_level == 2
        assert rec.priority == 8


class TestPlayStrategy:
    """Test PlayStrategy model."""

    def test_create_strategy(self):
        """Test creating PlayStrategy."""
        strategy = PlayStrategy(
            character_name="Test",
            playstyle=Playstyle.OFFENSIVE,
            strengths=["High success rate"],
            weaknesses=["High tentacle risk"],
        )

        assert strategy.character_name == "Test"
        assert strategy.playstyle == Playstyle.OFFENSIVE
        assert len(strategy.strengths) == 1
        assert len(strategy.weaknesses) == 1

    def test_primary_strength(self):
        """Test primary_strength property."""
        strategy = PlayStrategy(
            character_name="Test",
            playstyle=Playstyle.BALANCED,
            strengths=["Strength 1", "Strength 2"],
        )

        assert strategy.primary_strength == "Strength 1"

    def test_primary_weakness(self):
        """Test primary_weakness property."""
        strategy = PlayStrategy(
            character_name="Test",
            playstyle=Playstyle.BALANCED,
            weaknesses=["Weakness 1", "Weakness 2"],
        )

        assert strategy.primary_weakness == "Weakness 1"


class TestPlayStrategyAnalyzer:
    """Test PlayStrategyAnalyzer."""

    def test_analyze_offensive_character(self):
        """Test analyzing an offensive character."""
        build = CharacterBuild(character_name="Test")
        stats = CharacterStatistics(
            expected_successes=3.0,
            expected_tentacles=0.5,
            prob_at_least_1_success=0.95,
            prob_at_least_1_tentacle=0.3,
        )

        analyzer = PlayStrategyAnalyzer()
        strategy = analyzer.analyze(build, stats=stats)

        assert strategy.playstyle == Playstyle.OFFENSIVE
        assert "High success rate" in strategy.strengths
        assert "Low tentacle risk" in strategy.strengths

    def test_analyze_defensive_character(self):
        """Test analyzing a defensive character."""
        build = CharacterBuild(character_name="Test")
        stats = CharacterStatistics(
            expected_successes=1.5,
            expected_tentacles=1.5,
            wounds_healed_per_turn=2,
            stress_healed_per_turn=1,
        )

        analyzer = PlayStrategyAnalyzer()
        strategy = analyzer.analyze(build, stats=stats)

        assert strategy.playstyle == Playstyle.DEFENSIVE
        assert "Wound healing" in strategy.strengths
        assert "Stress healing" in strategy.strengths

