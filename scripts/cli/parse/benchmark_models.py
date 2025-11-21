#!/usr/bin/env python3
"""
Pydantic models for OCR benchmark results.

Provides type-safe data structures for benchmark scoring and results.
"""

from typing import Any, Dict, Final, List, Optional

from pydantic import BaseModel, Field, computed_field

# Benchmark category constants
CATEGORY_NAME: Final[str] = "name"
CATEGORY_LOCATION: Final[str] = "location"
CATEGORY_MOTTO: Final[str] = "motto"
CATEGORY_STORY: Final[str] = "story"
CATEGORY_SPECIAL_POWER: Final[str] = "special_power"
CATEGORY_DICE_RECOGNITION: Final[str] = "dice_recognition"
CATEGORY_MECHANICS_RECOGNITION: Final[str] = "mechanics_recognition"

# List of all benchmark categories
BENCHMARK_CATEGORIES: Final[List[str]] = [
    CATEGORY_NAME,
    CATEGORY_LOCATION,
    CATEGORY_MOTTO,
    CATEGORY_STORY,
    CATEGORY_SPECIAL_POWER,
    CATEGORY_DICE_RECOGNITION,
    CATEGORY_MECHANICS_RECOGNITION,
]


class LevelScores(BaseModel):
    """Scores for each power level (1-4)."""

    level_1: float = Field(default=0.0, ge=0.0, le=100.0, description="Score for level 1")
    level_2: float = Field(default=0.0, ge=0.0, le=100.0, description="Score for level 2")
    level_3: float = Field(default=0.0, ge=0.0, le=100.0, description="Score for level 3")
    level_4: float = Field(default=0.0, ge=0.0, le=100.0, description="Score for level 4")

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "LevelScores":
        """Create LevelScores from dictionary."""
        return cls(
            level_1=data.get("level_1", 0.0),
            level_2=data.get("level_2", 0.0),
            level_3=data.get("level_3", 0.0),
            level_4=data.get("level_4", 0.0),
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "level_1": self.level_1,
            "level_2": self.level_2,
            "level_3": self.level_3,
            "level_4": self.level_4,
        }


class ExtractionScores(BaseModel):
    """Scores for each extraction category."""

    name: float = Field(default=0.0, ge=0.0, le=100.0, description="Name extraction score")
    location: float = Field(default=0.0, ge=0.0, le=100.0, description="Location extraction score")
    motto: float = Field(default=0.0, ge=0.0, le=100.0, description="Motto extraction score")
    story: float = Field(default=0.0, ge=0.0, le=100.0, description="Story extraction score")
    special_power: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Special power extraction score"
    )
    dice_recognition: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Dice recognition score"
    )
    mechanics_recognition: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Mechanics recognition score"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def average_score(self) -> float:
        """Calculate average score across all categories."""
        scores = [
            self.name,
            self.location,
            self.motto,
            self.story,
            self.special_power,
            self.dice_recognition,
            self.mechanics_recognition,
        ]
        return sum(scores) / len(scores) if scores else 0.0


class ExtractedData(BaseModel):
    """Data extracted by OCR strategy."""

    name: Optional[str] = Field(default=None, description="Extracted character name")
    location: Optional[str] = Field(default=None, description="Extracted character location")
    motto: Optional[str] = Field(default=None, description="Extracted character motto")
    story: Optional[str] = Field(default=None, description="Extracted character story")
    special_power_levels: int = Field(
        default=0, ge=0, le=4, description="Number of special power levels extracted"
    )


class ComponentStrategies(BaseModel):
    """Component strategies used in hybrid approach."""

    story: Optional[str] = Field(default=None, description="Strategy used for story extraction")
    special_power: Optional[str] = Field(
        default=None, description="Strategy used for special power extraction"
    )


class BenchmarkResult(BaseModel):
    """Complete benchmark result for a single OCR strategy."""

    strategy_name: str = Field(..., description="Name of the OCR strategy")
    strategy_description: str = Field(default="", description="Description of the strategy")
    overall_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall weighted score"
    )
    scores: ExtractionScores = Field(
        default_factory=ExtractionScores, description="Category scores"
    )
    level_scores: LevelScores = Field(default_factory=LevelScores, description="Power level scores")
    extracted: ExtractedData = Field(default_factory=ExtractedData, description="Extracted data")
    front_text_length: int = Field(default=0, ge=0, description="Length of front card OCR text")
    back_text_length: int = Field(default=0, ge=0, description="Length of back card OCR text")
    error: Optional[str] = Field(default=None, description="Error message if extraction failed")
    component_strategies: Optional[ComponentStrategies] = Field(
        default=None, description="Component strategies (for hybrid approaches)"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        """Create BenchmarkResult from dictionary."""
        scores_data = data.get("scores", {})
        level_scores_data = data.get("level_scores", {})
        extracted_data = data.get("extracted", {})
        component_strategies_data = data.get("component_strategies")

        return cls(
            strategy_name=data.get("strategy_name", ""),
            strategy_description=data.get("strategy_description", ""),
            overall_score=data.get("overall_score", 0.0),
            scores=ExtractionScores(**scores_data) if scores_data else ExtractionScores(),
            level_scores=LevelScores.from_dict(level_scores_data)
            if level_scores_data
            else LevelScores(),
            extracted=ExtractedData(**extracted_data) if extracted_data else ExtractedData(),
            front_text_length=data.get("front_text_length", 0),
            back_text_length=data.get("back_text_length", 0),
            error=data.get("error"),
            component_strategies=ComponentStrategies(**component_strategies_data)
            if component_strategies_data
            else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "strategy_name": self.strategy_name,
            "strategy_description": self.strategy_description,
            "overall_score": round(self.overall_score, 2),
            "scores": {
                "name": round(self.scores.name, 2),
                "location": round(self.scores.location, 2),
                "motto": round(self.scores.motto, 2),
                "story": round(self.scores.story, 2),
                "special_power": round(self.scores.special_power, 2),
                "dice_recognition": round(self.scores.dice_recognition, 2),
                "mechanics_recognition": round(self.scores.mechanics_recognition, 2),
            },
            "level_scores": self.level_scores.to_dict(),
            "extracted": {
                "name": self.extracted.name,
                "location": self.extracted.location,
                "motto": self.extracted.motto,
                "story": (
                    self.extracted.story[:200] + "..."
                    if self.extracted.story and len(self.extracted.story) > 200
                    else self.extracted.story
                ),
                "special_power_levels": self.extracted.special_power_levels,
            },
            "front_text_length": self.front_text_length,
            "back_text_length": self.back_text_length,
        }

        if self.error:
            result["error"] = self.error

        if self.component_strategies:
            result["component_strategies"] = {
                "story": self.component_strategies.story,
                "special_power": self.component_strategies.special_power,
            }

        return result


class BestStrategyPerCategory(BaseModel):
    """Best strategy for a specific category."""

    strategy_name: str = Field(..., description="Name of the best strategy")
    strategy_description: str = Field(default="", description="Strategy description")
    score: float = Field(ge=0.0, le=100.0, description="Score achieved")
    extracted: Optional[Any] = Field(default=None, description="Extracted value for this category")


class BenchmarkResultsSummary(BaseModel):
    """Summary of benchmark results."""

    character: str = Field(..., description="Character name")
    season: str = Field(..., description="Season directory")
    timestamp: str = Field(..., description="ISO timestamp")
    total_strategies: int = Field(ge=0, description="Total number of strategies tested")
    top_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Highest overall score")
    results: List[BenchmarkResult] = Field(
        default_factory=list, description="All benchmark results"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def top_result(self) -> Optional[BenchmarkResult]:
        """Get the top-scoring result."""
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.overall_score)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def best_strategies_per_category(self) -> Dict[str, BestStrategyPerCategory]:
        """Find best strategy for each category."""
        best_strategies = {}

        for category in BENCHMARK_CATEGORIES:
            best_score = -1.0
            best_result = None

            for result in self.results:
                if result.error:
                    continue

                score = getattr(result.scores, category, 0.0)
                if score > best_score:
                    best_score = score
                    best_result = result

            if best_result:
                extracted_value = getattr(
                    best_result.extracted,
                    category.replace("_recognition", "").replace(
                        "special_power", "special_power_levels"
                    ),
                    None,
                )

                best_strategies[category] = BestStrategyPerCategory(
                    strategy_name=best_result.strategy_name,
                    strategy_description=best_result.strategy_description,
                    score=best_score,
                    extracted=extracted_value,
                )

        return best_strategies
