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
from typing import Final, List, Optional

try:
    import click
    from pydantic import BaseModel, Field
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
    analyze_power_dice_impact,
    get_combined_stats,
)

console = Console()

# Constants
FILENAME_COMMON_POWERS: Final[str] = "common_powers.json"
DATA_DIR: Final[str] = "data"


class PowerLevelAnalysis(BaseModel):
    """Analysis results for a single power level."""

    power_name: str = Field(..., description="Name of the power")
    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    description: str = Field(..., description="Power level description")
    green_dice_added: int = Field(..., ge=0, description="Number of green dice this level adds")
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


def extract_green_dice_from_description(description: str) -> int:
    """Extract number of green dice mentioned in a power description."""
    # Look for patterns like "gain 1 green dice", "gain 2 green dice", etc.
    patterns = [
        r"gain\s+(\d+)\s+green\s+dice",
        r"(\d+)\s+green\s+dice",
        r"gain\s+(\d+)\s+green",
        r"add\s+(\d+)\s+green\s+dice",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return 0


def analyze_power_level(power_name: str, level: int, description: str) -> PowerLevelAnalysis:
    """Analyze a single power level and calculate its statistical impact."""
    green_dice_added = extract_green_dice_from_description(description)

    if green_dice_added > 0:
        impact = analyze_power_dice_impact(
            BASE_BLACK_DICE_COUNT, BASE_GREEN_DICE_COUNT, green_dice_added
        )

        return PowerLevelAnalysis(
            power_name=power_name,
            level=level,
            description=description,
            green_dice_added=green_dice_added,
            base_expected_successes=impact.base.expected_successes,
            enhanced_expected_successes=impact.enhanced.expected_successes,
            expected_successes_increase=impact.improvement.expected_successes_increase,
            expected_successes_percent_increase=impact.improvement.expected_successes_percent_increase,
            max_successes_increase=impact.improvement.max_successes_increase,
            tentacle_risk=impact.enhanced.expected_tentacles,
            base_tentacle_risk=impact.base.expected_tentacles,
        )
    else:
        # Power doesn't add dice, return base stats
        base_stats = get_combined_stats(BASE_BLACK_DICE_COUNT, BASE_GREEN_DICE_COUNT)
        return PowerLevelAnalysis(
            power_name=power_name,
            level=level,
            description=description,
            green_dice_added=0,
            base_expected_successes=base_stats.expected_successes,
            enhanced_expected_successes=base_stats.expected_successes,
            expected_successes_increase=0.0,
            expected_successes_percent_increase=0.0,
            max_successes_increase=0,
            tentacle_risk=base_stats.expected_tentacles,
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

            if analysis.green_dice_added > 0:
                console.print(f"  Level {level}: Adds {analysis.green_dice_added} green dice")
                console.print(
                    f"    Expected successes: {analysis.base_expected_successes:.2f} -> "
                    f"{analysis.enhanced_expected_successes:.2f} "
                    f"(+{analysis.expected_successes_increase:.2f}, "
                    f"+{analysis.expected_successes_percent_increase:.1f}%)"
                )
                console.print(
                    f"    Max successes: {BASE_BLACK_DICE_COUNT} -> "
                    f"{BASE_BLACK_DICE_COUNT + analysis.green_dice_added}"
                )
            else:
                console.print(f"  Level {level}: No dice added (other effect)")

        console.print()

    # Create summary table
    table = Table(title="Power Statistics Summary")
    table.add_column("Power", style="cyan")
    table.add_column("Level", justify="right")
    table.add_column("Green Dice", justify="right")
    table.add_column("Exp Successes", justify="right")
    table.add_column("Success Increase", justify="right")
    table.add_column("Max Successes", justify="right")

    for analysis in all_analyses:
        if analysis.green_dice_added > 0:
            table.add_row(
                analysis.power_name,
                str(analysis.level),
                str(analysis.green_dice_added),
                f"{analysis.enhanced_expected_successes:.2f}",
                f"+{analysis.expected_successes_increase:.2f}",
                str(BASE_BLACK_DICE_COUNT + analysis.green_dice_added),
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
