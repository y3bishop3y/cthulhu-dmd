#!/usr/bin/env python3
"""
Play Strategy Models

Models for analyzing character play strategies and recommending approaches.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from scripts.models.character_build import CharacterBuild, CharacterStatistics


class Playstyle(str, Enum):
    """Character playstyle types."""

    OFFENSIVE = "offensive"  # High damage, attack-focused
    DEFENSIVE = "defensive"  # High survival, healing-focused
    BALANCED = "balanced"  # Good all-around
    UTILITY = "utility"  # Support, movement, investigation
    SPECIALIST = "specialist"  # Unique/niche role


class UpgradeRecommendation(BaseModel):
    """Recommendation for a power upgrade."""

    power_name: str = Field(..., description="Power to upgrade")
    current_level: int = Field(..., ge=1, le=4, description="Current power level")
    recommended_level: int = Field(..., ge=1, le=4, description="Recommended power level")
    reason: str = Field(..., description="Why this upgrade is recommended")
    priority: int = Field(..., ge=1, le=10, description="Priority (1-10, 10 = highest)")


class PlayStrategy(BaseModel):
    """Play strategy analysis for a character."""

    character_name: str = Field(..., description="Character name")
    playstyle: Playstyle = Field(..., description="Recommended playstyle")
    strengths: List[str] = Field(default_factory=list, description="Character strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Character weaknesses")
    recommended_upgrades: List[UpgradeRecommendation] = Field(
        default_factory=list, description="Recommended power upgrades"
    )
    upgrade_path: List[str] = Field(
        default_factory=list, description="Recommended upgrade path (power names)"
    )

    @computed_field
    @property
    def primary_strength(self) -> Optional[str]:
        """Get primary strength."""
        return self.strengths[0] if self.strengths else None

    @computed_field
    @property
    def primary_weakness(self) -> Optional[str]:
        """Get primary weakness."""
        return self.weaknesses[0] if self.weaknesses else None


class PlayStrategyAnalyzer:
    """Analyzes character builds and generates play strategies."""

    def analyze(
        self, build: CharacterBuild, stats: Optional[CharacterStatistics] = None
    ) -> PlayStrategy:
        """Analyze a character build and generate play strategy.

        Args:
            build: Character build to analyze
            stats: Optional pre-computed statistics (for testing)

        Returns:
            PlayStrategy with recommendations
        """
        if stats is None:
            stats = build.statistics

        # Determine playstyle
        playstyle = self._determine_playstyle(stats, build)

        # Identify strengths
        strengths = self._identify_strengths(stats, build)

        # Identify weaknesses
        weaknesses = self._identify_weaknesses(stats, build)

        # Generate upgrade recommendations
        upgrades = self._generate_upgrade_recommendations(build)

        # Generate upgrade path
        upgrade_path = self._generate_upgrade_path(build, upgrades)

        return PlayStrategy(
            character_name=build.character_name,
            playstyle=playstyle,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_upgrades=upgrades,
            upgrade_path=upgrade_path,
        )

    def _determine_playstyle(self, stats: CharacterStatistics, build: CharacterBuild) -> Playstyle:
        """Determine character playstyle based on statistics."""
        # High expected successes + low tentacle risk = offensive
        if stats.expected_successes > 2.5 and stats.expected_tentacles < 1.0:
            return Playstyle.OFFENSIVE

        # High healing = defensive
        if stats.wounds_healed_per_turn > 0 or stats.stress_healed_per_turn > 0:
            return Playstyle.DEFENSIVE

        # High rerolls = utility
        if stats.rerolls_per_roll > 0:
            return Playstyle.UTILITY

        # Default to balanced
        return Playstyle.BALANCED

    def _identify_strengths(self, stats: CharacterStatistics, build: CharacterBuild) -> List[str]:
        """Identify character strengths."""
        strengths = []

        if stats.expected_successes > 2.0:
            strengths.append("High success rate")
        if stats.expected_tentacles < 1.0:
            strengths.append("Low tentacle risk")
        if stats.total_green_dice > 0:
            strengths.append("Green dice bonuses (safer rolls)")
        if stats.wounds_healed_per_turn > 0:
            strengths.append("Wound healing")
        if stats.stress_healed_per_turn > 0:
            strengths.append("Stress healing")
        if stats.rerolls_per_roll > 0:
            strengths.append("Reroll capabilities")
        if stats.elder_signs_converted_to_successes > 0:
            strengths.append("Elder sign conversion")

        return strengths

    def _identify_weaknesses(self, stats: CharacterStatistics, build: CharacterBuild) -> List[str]:
        """Identify character weaknesses."""
        weaknesses = []

        if stats.expected_successes < 1.5:
            weaknesses.append("Low success rate")
        if stats.expected_tentacles > 1.5:
            weaknesses.append("High tentacle risk")
        if stats.total_green_dice == 0:
            weaknesses.append("No green dice (higher tentacle risk)")
        if stats.wounds_healed_per_turn == 0 and stats.stress_healed_per_turn == 0:
            weaknesses.append("No healing capabilities")
        if stats.rerolls_per_roll == 0:
            weaknesses.append("No reroll capabilities")

        return weaknesses

    def _generate_upgrade_recommendations(
        self, build: CharacterBuild
    ) -> List[UpgradeRecommendation]:
        """Generate upgrade recommendations."""
        recommendations = []

        # TODO: Implement upgrade recommendation logic
        # For now, return empty list

        return recommendations

    def _generate_upgrade_path(
        self, build: CharacterBuild, upgrades: List[UpgradeRecommendation]
    ) -> List[str]:
        """Generate recommended upgrade path."""
        # TODO: Implement upgrade path generation
        # For now, return empty list

        return []
