#!/usr/bin/env python3
"""
Analyze common powers and calculate their statistical impact on dice rolls.

This script calculates how each power level affects:
- Expected successes
- Tentacle risk
- Elder sign probability
- Overall power value/importance
"""

import json
import re
import sys
from pathlib import Path
from typing import ClassVar, Final, List, Optional

try:
    import click
    from pydantic import BaseModel, Field, computed_field
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/analyze_power_statistics.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/analyze_power_statistics.py [options]\n\n"
        "Recommended: uv run ./scripts/analyze_power_statistics.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.dice_probabilities import (
    BASE_BLACK_DICE_COUNT,
    BASE_GREEN_DICE_COUNT,
    DiceProbabilityCalculator,
)
from scripts.models.game_mechanics import ActionType

console = Console()

# Constants
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
DATA_DIR: Final[str] = "data"


class DiceAddition(BaseModel):
    """Represents dice additions parsed from a power description.
    
    Uses Pydantic v2 features to parse and validate dice additions.
    """

    green_dice: int = Field(default=0, ge=0, description="Number of green dice added")
    black_dice: int = Field(default=0, ge=0, description="Number of black dice added")

    # Constants for regex patterns (class variables, not instance fields)
    # More comprehensive patterns to handle OCR variations and different phrasings
    GREEN_PATTERNS: ClassVar[List[str]] = [
        r"gain\s+a\s+green\s+dice",  # "gain a green dice" (singular, = 1)
        r"gain\s+a\s+Green\s+Dice",  # "gain a Green Dice" (capitalized, singular)
        r"gain\s+(\d+)\s+green\s+dice",  # "gain 2 green dice"
        r"(\d+)\s+green\s+dice",  # "2 green dice"
        r"gain\s+(\d+)\s+green",  # "gain 2 green"
        r"add\s+(\d+)\s+green\s+dice",  # "add 2 green dice"
        r"gain\s+(\d+)\s+Green\s+dice",  # Capitalized
        r"(\d+)\s+Green\s+dice",  # Capitalized
        r"gain\s+a\s+green\s+dice\s+when",  # Conditional: "gain a green dice when" (= 1)
        r"gain\s+a\s+green\s+dice\s+while",  # Conditional: "gain a green dice while" (= 1)
        r"gain\s+(\d+)\s+green\s+dice\s+when",  # Conditional: "gain 2 green dice when"
        r"(\d+)\s+green\s+dice\s+when",  # Conditional: "2 green dice when"
        r"gain\s+(\d+)\s+green\s+dice\s+while",  # Conditional: "gain 2 green dice while"
        r"add\s+(\d+)\s+green\s+dice\s+to",  # "add 2 green dice to"
        r"(\d+)\s+additional\s+green\s+dice",  # "2 additional green dice"
        r"(\d+)\s+extra\s+green\s+dice",  # "2 extra green dice"
    ]

    BLACK_PATTERNS: ClassVar[List[str]] = [
        r"gain\s+(\d+)\s+black\s+dice",  # "gain 1 black dice"
        r"(\d+)\s+black\s+dice",  # "1 black dice"
        r"gain\s+(\d+)\s+black",  # "gain 1 black"
        r"add\s+(\d+)\s+black\s+dice",  # "add 1 black dice"
        r"gain\s+(\d+)\s+Black\s+dice",  # Capitalized
        r"(\d+)\s+Black\s+dice",  # Capitalized
        r"gain\s+(\d+)\s+black\s+dice\s+when",  # Conditional
        r"(\d+)\s+black\s+dice\s+when",  # Conditional
        r"(\d+)\s+additional\s+black\s+dice",  # "1 additional black dice"
        r"(\d+)\s+extra\s+black\s+dice",  # "1 extra black dice"
    ]

    @classmethod
    def from_description(cls, description: str) -> "DiceAddition":
        """Parse dice additions from a power description.
        
        Args:
            description: Power level description text
            
        Returns:
            DiceAddition model with parsed green and black dice counts
        """
        green_dice = 0
        black_dice = 0

        for pattern in cls.GREEN_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Handle "gain a green dice" pattern (no capture group, means 1)
                if r"gain\s+a\s+green" in pattern:
                    green_dice = 1
                else:
                    # Extract number from capture group
                    green_dice = int(match.group(1))
                break

        for pattern in cls.BLACK_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                black_dice = int(match.group(1))
                break

        return cls(green_dice=green_dice, black_dice=black_dice)

    @computed_field
    @property
    def total_dice_added(self) -> int:
        """Total number of dice added (green + black)."""
        return self.green_dice + self.black_dice

    @computed_field
    @property
    def adds_any_dice(self) -> bool:
        """Whether this addition adds any dice."""
        return self.total_dice_added > 0


class ElderSignConversion(BaseModel):
    """Represents elder sign to success conversion parsed from a power description.
    
    Uses Pydantic v2 features to parse and validate elder sign conversions.
    """

    elder_signs_as_successes: int = Field(
        default=0, ge=0, description="Number of elder signs that can be counted as successes"
    )
    successes_per_elder_sign: int = Field(
        default=1, ge=1, description="Number of successes each elder sign counts as (default: 1, can be 2)"
    )

    # Constants for regex patterns (class variables, not instance fields)
    ELDER_SIGN_PATTERNS: ClassVar[List[str]] = [
        r"count\s+(\d+)\s+(?:Arcane|elder\s+sign|elder)",
        r"count\s+(?:any\s+number\s+of|all)\s+(?:Arcane|elder\s+signs?|elders?)",
        r"(?:Arcane|elder\s+signs?|elders?)\s+as\s+success",
    ]

    @classmethod
    def from_description(cls, description: str) -> "ElderSignConversion":
        """Parse elder sign conversions from a power description.
        
        Args:
            description: Power level description text
            
        Returns:
            ElderSignConversion model with parsed elder sign count
        """
        elder_signs = 0

        # Pattern 1: "count 1 Arcane as success" or "count 1 elder sign as success"
        # Handle "Arcane (elder sign)" pattern - try multiple variations
        patterns_to_try = [
            r"count\s+(\d+)\s+Arcane(?:\s*\([^)]*\))?\s+as\s+success",  # "count 1 Arcane as success"
            r"count\s+(\d+)\s+(?:elder\s+sign|elder)(?:\s*\([^)]*\))?\s+as\s+success",  # "count 1 elder sign as success"
            r"count\s+(\d+)\s+Arcane",  # "count 1 Arcane"
            r"count\s+(\d+)\s+elder",  # "count 1 elder"
            r"may\s+count\s+(\d+)\s+Arcane\s+as\s+success",  # "may count 1 Arcane as success"
            r"may\s+count\s+(\d+)\s+elder\s+sign\s+as\s+success",  # "may count 1 elder sign as success"
            r"(\d+)\s+Arcane\s+as\s+success",  # "1 Arcane as success"
            r"(\d+)\s+elder\s+sign\s+as\s+success",  # "1 elder sign as success"
        ]
        for pattern in patterns_to_try:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                elder_signs = int(match.group(1))
                return cls(elder_signs_as_successes=elder_signs)

        # Pattern 2: "count any number of elder signs as successes" or "as 2 success"
        match_any = re.search(
            r"count\s+(?:any\s+number\s+of|all)\s+(?:Arcane|elder\s+signs?|elders?)",
            description,
            re.IGNORECASE,
        )
        if match_any:
            # Check if it says "as 2 success" or "as 2 successes"
            successes_per = 1
            if re.search(r"as\s+2\s+success", description, re.IGNORECASE):
                successes_per = 2
            return cls(elder_signs_as_successes=999, successes_per_elder_sign=successes_per)  # Special value for "any number"

        # Pattern 3: "Heal X stress for each elder sign you count as a success"
        # This implies elder signs can be counted as successes
        heal_match = re.search(
            r"heal\s+\d+\s+stress\s+for\s+each\s+(?:Arcane|elder\s+sign|elder)\s+you\s+count\s+as\s+a?\s+success",
            description,
            re.IGNORECASE,
        )
        if heal_match:
            # This means any elder signs can be counted as successes (for the heal effect)
            return cls(elder_signs_as_successes=999, successes_per_elder_sign=1)

        return cls(elder_signs_as_successes=0)

    @computed_field
    @property
    def converts_any_number(self) -> bool:
        """Whether this converts any number of elder signs (unlimited)."""
        return self.elder_signs_as_successes >= 999


class ActionAddition(BaseModel):
    """Represents action additions parsed from a power description.
    
    Some powers add free actions (like free attacks) that don't consume
    the character's normal 3 actions per turn.
    """

    actions_added: int = Field(
        default=0, ge=0, description="Number of free actions added per turn"
    )
    action_type: ActionType = Field(
        default=ActionType.ATTACK, description="Type of action added"
    )

    # Constants for regex patterns (class variables, not instance fields)
    # More comprehensive patterns for action additions
    FREE_ACTION_PATTERNS: ClassVar[List[str]] = [
        r"(\d+)\s+free\s+attack",  # "1 free attack"
        r"perform\s+(\d+)\s+free\s+attack",  # "perform 1 free attack"
        r"(\d+)\s+additional\s+action",  # "1 additional action"
        r"gain\s+(\d+)\s+action",  # "gain 1 action"
        r"(\d+)\s+free\s+action",  # "1 free action"
        r"(\d+)\s+extra\s+action",  # "1 extra action"
        r"(\d+)\s+bonus\s+action",  # "1 bonus action"
        r"may\s+perform\s+(\d+)\s+free\s+attack",  # "may perform 1 free attack"
        r"may\s+(\d+)\s+free\s+attack",  # "may 1 free attack"
        r"(\d+)\s+free\s+attack\s+per\s+turn",  # "1 free attack per turn"
    ]

    @classmethod
    def from_description(cls, description: str) -> "ActionAddition":
        """Parse action additions from a power description.
        
        Args:
            description: Power level description text
            
        Returns:
            ActionAddition model with parsed action count
        """
        actions = 0
        action_type = ActionType.ATTACK

        # Pattern: "1 free attack" or "perform 1 free attack"
        for pattern in cls.FREE_ACTION_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                actions = int(match.group(1))
                # Determine action type from description
                desc_lower = description.lower()
                if "attack" in desc_lower:
                    action_type = ActionType.ATTACK
                elif "run" in desc_lower:
                    action_type = ActionType.RUN
                elif "move" in desc_lower:
                    action_type = ActionType.MOVE
                elif "rest" in desc_lower:
                    action_type = ActionType.REST
                elif "investigate" in desc_lower:
                    action_type = ActionType.INVESTIGATE
                elif "trade" in desc_lower:
                    action_type = ActionType.TRADE
                else:
                    action_type = ActionType.ACTION
                return cls(actions_added=actions, action_type=action_type)

        return cls(actions_added=0)


class PowerLevelAnalysis(BaseModel):
    """Analysis results for a single power level."""

    power_name: str = Field(..., description="Name of the power")
    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    description: str = Field(..., description="Power level description")
    effect: str = Field(..., description="What this power level does (e.g., 'Adds 1 green dice', 'Counts 1 elder sign as success')")
    dice_addition: DiceAddition = Field(..., description="Dice additions parsed from description")
    elder_sign_conversion: ElderSignConversion = Field(
        ..., description="Elder sign to success conversions parsed from description"
    )
    action_addition: ActionAddition = Field(
        default_factory=lambda: ActionAddition(),
        description="Free actions added per turn (e.g., free attacks)",
    )
    base_expected_successes: float = Field(
        ..., ge=0.0, description="Expected successes with base dice only"
    )
    enhanced_expected_successes: float = Field(
        ..., ge=0.0, description="Expected successes with power enhancement"
    )
    expected_successes_increase: float = Field(
        ..., description="Absolute increase in expected successes"
    )
    expected_successes_percent_increase: float = Field(
        ..., description="Percentage increase in expected successes"
    )
    max_successes_increase: int = Field(
        ..., ge=0, description="Increase in maximum possible successes"
    )
    tentacle_risk: float = Field(..., ge=0.0, description="Expected tentacles with enhancement")
    base_tentacle_risk: float = Field(
        ..., ge=0.0, description="Expected tentacles with base dice only"
    )

    @computed_field
    @property
    def green_dice_added(self) -> int:
        """Number of green dice added (convenience property)."""
        return self.dice_addition.green_dice

    @computed_field
    @property
    def black_dice_added(self) -> int:
        """Number of black dice added (convenience property)."""
        return self.dice_addition.black_dice


def analyze_power_level(power_name: str, level: int, description: str) -> PowerLevelAnalysis:
    """Analyze a single power level and calculate its statistical impact."""
    dice_addition = DiceAddition.from_description(description)
    elder_sign_conversion = ElderSignConversion.from_description(description)
    action_addition = ActionAddition.from_description(description)

    # Calculate base stats
    calculator = DiceProbabilityCalculator()
    base_stats = calculator.calculate_combined_stats(
        BASE_BLACK_DICE_COUNT, BASE_GREEN_DICE_COUNT
    )

    # Calculate enhanced stats (with dice additions)
    enhanced_stats = calculator.calculate_combined_stats(
        BASE_BLACK_DICE_COUNT + dice_addition.black_dice,
        BASE_GREEN_DICE_COUNT + dice_addition.green_dice,
    )

    # Calculate elder sign conversion bonus
    elder_bonus_successes = 0.0
    if elder_sign_conversion.elder_signs_as_successes > 0:
        # Expected elder signs from the enhanced roll
        expected_elder = enhanced_stats.expected_elder_signs
        if elder_sign_conversion.converts_any_number:
            # Can convert all elder signs
            elder_signs_converted = expected_elder
        else:
            # Can convert up to the specified number
            elder_signs_converted = min(
                expected_elder, float(elder_sign_conversion.elder_signs_as_successes)
            )
        # Multiply by successes per elder sign (usually 1, but can be 2)
        elder_bonus_successes = elder_signs_converted * elder_sign_conversion.successes_per_elder_sign

    # Enhanced successes = base successes + dice additions + elder sign conversions
    enhanced_expected_successes = enhanced_stats.expected_successes + elder_bonus_successes

    expected_successes_increase = enhanced_expected_successes - base_stats.expected_successes
    expected_successes_percent_increase = (
        (enhanced_expected_successes - base_stats.expected_successes)
        / base_stats.expected_successes
        * 100
        if base_stats.expected_successes > 0
        else 0
    )
    max_successes_increase = (
        enhanced_stats.max_possible_successes - base_stats.max_possible_successes
    )

    # Generate effect description
    effect_parts = []
    if dice_addition.adds_any_dice:
        dice_desc = []
        if dice_addition.green_dice > 0:
            dice_desc.append(f"{dice_addition.green_dice} green dice")
        if dice_addition.black_dice > 0:
            dice_desc.append(f"{dice_addition.black_dice} black dice")
        effect_parts.append(f"Adds {' + '.join(dice_desc)}")

    if elder_sign_conversion.elder_signs_as_successes > 0:
        if elder_sign_conversion.converts_any_number:
            if elder_sign_conversion.successes_per_elder_sign > 1:
                effect_parts.append(f"Counts any elder signs as {elder_sign_conversion.successes_per_elder_sign} successes each")
            else:
                effect_parts.append("Counts any elder signs as successes")
        else:
            if elder_sign_conversion.successes_per_elder_sign > 1:
                effect_parts.append(f"Counts {elder_sign_conversion.elder_signs_as_successes} elder sign(s) as {elder_sign_conversion.successes_per_elder_sign} successes each")
            else:
                effect_parts.append(f"Counts {elder_sign_conversion.elder_signs_as_successes} elder sign(s) as success(es)")

    if action_addition.actions_added > 0:
        action_name = action_addition.action_type.value
        if action_addition.actions_added == 1:
            effect_parts.append(f"Adds 1 free {action_name} per turn")
        else:
            # Handle pluralization
            plural_name = action_name if action_name.endswith("s") else f"{action_name}s"
            effect_parts.append(f"Adds {action_addition.actions_added} free {plural_name} per turn")

    if not effect_parts:
        effect_parts.append("Other effect (no dice, elder sign conversion, or actions)")

    effect = ". ".join(effect_parts)

    return PowerLevelAnalysis(
        power_name=power_name,
        level=level,
        description=description,
        effect=effect,
        dice_addition=dice_addition,
        elder_sign_conversion=elder_sign_conversion,
        action_addition=action_addition,
        base_expected_successes=base_stats.expected_successes,
        enhanced_expected_successes=enhanced_expected_successes,
        expected_successes_increase=expected_successes_increase,
        expected_successes_percent_increase=expected_successes_percent_increase,
        max_successes_increase=max_successes_increase,
        tentacle_risk=enhanced_stats.expected_tentacles,
        base_tentacle_risk=base_stats.expected_tentacles,
    )


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--output-json",
    type=click.Path(path_type=Path),
    help="Output JSON file with detailed statistics (optional)",
)
def main(data_dir: Path, output_json: Optional[Path]):
    """Analyze common powers and calculate their statistical impact."""
    console.print("[bold cyan]Power Statistics Analysis[/bold cyan]\n")

    common_powers_path = data_dir / FILENAME_COMMON_POWERS
    if not common_powers_path.exists():
        console.print(f"[red]Error: {common_powers_path} not found![/red]")
        sys.exit(1)

    with open(common_powers_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[cyan]Analyzing {len(powers_data)} powers...[/cyan]\n")

    # Analyze each power
    all_analyses: List[PowerLevelAnalysis] = []

    for power in powers_data:
        power_name = power["name"]
        console.print(f"[bold]{power_name}[/bold]")

        for level_data in power["levels"]:
            level = level_data["level"]
            description = level_data["description"]

            analysis = analyze_power_level(power_name, level, description)
            all_analyses.append(analysis)

            has_dice = analysis.green_dice_added > 0 or analysis.black_dice_added > 0
            has_elder_conversion = analysis.elder_sign_conversion.elder_signs_as_successes > 0

            if has_dice or has_elder_conversion:
                effects = []
                if has_dice:
                    dice_desc = []
                    if analysis.green_dice_added > 0:
                        dice_desc.append(f"{analysis.green_dice_added} green")
                    if analysis.black_dice_added > 0:
                        dice_desc.append(f"{analysis.black_dice_added} black")
                    effects.append(f"Adds {' + '.join(dice_desc)} dice")

                if has_elder_conversion:
                    if analysis.elder_sign_conversion.converts_any_number:
                        effects.append("Counts any number of elder signs as successes")
                    else:
                        effects.append(f"Counts {analysis.elder_sign_conversion.elder_signs_as_successes} elder sign(s) as successes")

                effect_str = " | ".join(effects)
                console.print(f"  Level {level}: {effect_str}")
                console.print(
                    f"    Expected successes: {analysis.base_expected_successes:.2f} -> "
                    f"{analysis.enhanced_expected_successes:.2f} "
                    f"(+{analysis.expected_successes_increase:.2f}, "
                    f"+{analysis.expected_successes_percent_increase:.1f}%)"
                )
                if has_dice:
                    console.print(
                        f"    Max successes: {BASE_BLACK_DICE_COUNT} -> "
                        f"{BASE_BLACK_DICE_COUNT + analysis.black_dice_added + analysis.green_dice_added}"
                    )
                console.print(
                    f"    Tentacle risk: {analysis.base_tentacle_risk:.2f} -> "
                    f"{analysis.tentacle_risk:.2f}"
                )
            else:
                console.print(f"  Level {level}: No dice added (other effect)")

        console.print()

    # Create summary table for powers that affect statistics
    table = Table(title="Power Statistics Summary - Powers with Statistical Impact")
    table.add_column("Power", style="cyan")
    table.add_column("Level", justify="right")
    table.add_column("Effect", style="green")
    table.add_column("Green Dice", justify="right")
    table.add_column("Black Dice", justify="right")
    table.add_column("Exp Successes", justify="right")
    table.add_column("Success Increase", justify="right")
    table.add_column("Tentacle Risk", justify="right")

    for analysis in all_analyses:
        has_dice = analysis.green_dice_added > 0 or analysis.black_dice_added > 0
        has_elder = analysis.elder_sign_conversion.elder_signs_as_successes > 0

        if has_dice or has_elder:
            # Show effect summary
            effect_summary = analysis.effect[:40] + "..." if len(analysis.effect) > 40 else analysis.effect

            table.add_row(
                analysis.power_name,
                str(analysis.level),
                effect_summary,
                str(analysis.green_dice_added),
                str(analysis.black_dice_added),
                f"{analysis.enhanced_expected_successes:.2f}",
                f"+{analysis.expected_successes_increase:.2f} ({analysis.expected_successes_percent_increase:.1f}%)",
                f"{analysis.tentacle_risk:.2f}",
            )

    console.print(table)

    # Save detailed analysis if requested
    if output_json:
        # Convert Pydantic models to dicts for JSON serialization
        analyses_dict = [analysis.model_dump() for analysis in all_analyses]
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(analyses_dict, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]✓ Saved detailed analysis to {output_json}[/green]")

    console.print("\n[green]✓ Analysis complete![/green]")


if __name__ == "__main__":
    main()
