#!/usr/bin/env python3
"""
Character Build Analysis Script

Analyzes character builds and calculates their effectiveness.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/analysis/character_analyzer.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/analysis/character_analyzer.py [options]\n\n"
        "Recommended: uv run ./scripts/analysis/character_analyzer.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.character import CharacterData, CommonPower
from scripts.models.character_build import CharacterBuild

console = Console()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
COMMON_POWERS_FILE = DATA_DIR / "common_powers.json"


def load_common_powers() -> Dict[str, "CommonPower"]:
    """Load common powers from JSON file."""
    if not COMMON_POWERS_FILE.exists():
        console.print(f"[red]Error: {COMMON_POWERS_FILE} not found[/red]")
        sys.exit(1)

    with open(COMMON_POWERS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    from scripts.models.character import CommonPower as CommonPowerModel

    return {power_dict["name"]: CommonPowerModel.from_dict(power_dict) for power_dict in data}


def load_character_data(season: str, character_name: str) -> Optional[CharacterData]:
    """Load character data from JSON file."""
    char_dir = DATA_DIR / season / character_name
    json_file = char_dir / "character.json"

    if not json_file.exists():
        return None

    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        return CharacterData(**data)
    except Exception as e:
        console.print(f"[red]Error loading character data: {e}[/red]")
        return None


@click.command()
@click.option(
    "--character",
    required=True,
    help="Character name (e.g., 'amelie')",
)
@click.option(
    "--season",
    default="unknowable-box",
    help="Season name (default: unknowable-box)",
)
@click.option(
    "--special-level",
    default=1,
    type=int,
    help="Special power level (default: 1)",
)
@click.option(
    "--common-1-level",
    default=1,
    type=int,
    help="First common power level (default: 1)",
)
@click.option(
    "--common-2-level",
    default=1,
    type=int,
    help="Second common power level (default: 1)",
)
@click.option(
    "--insanity",
    default=1,
    type=int,
    help="Current insanity slot (default: 1)",
)
def main(
    character: str,
    season: str,
    special_level: int,
    common_1_level: int,
    common_2_level: int,
    insanity: int,
):
    """Analyze a character build and display statistics."""
    # Load character data
    character_data = load_character_data(season, character)
    if not character_data:
        console.print(f"[red]Error: Character '{character}' not found in season '{season}'[/red]")
        sys.exit(1)

    # Load power data
    power_data = load_common_powers()

    # Create build
    build = CharacterBuild.from_character_data(
        character_data,
        special_power_level=special_level,
        common_power_1_level=common_1_level,
        common_power_2_level=common_2_level,
        power_data=power_data,
    )

    # Set insanity level
    build.insanity_track.current_insanity = insanity

    # Display character info
    console.print(f"\n[bold cyan]Character: {build.character_name}[/bold cyan]")
    console.print(f"Season: {season}")

    # Display powers
    table = Table(title="Active Powers")
    table.add_column("Power", style="cyan")
    table.add_column("Level", style="green")
    table.add_column("Type", style="yellow")

    if build.common_power_1_name:
        table.add_row(build.common_power_1_name, str(build.common_power_1_level), "Common 1")
    if build.common_power_2_name:
        table.add_row(build.common_power_2_name, str(build.common_power_2_level), "Common 2")

    console.print(table)

    # Display statistics
    stats = build.statistics

    console.print("\n[bold]Dice Configuration:[/bold]")
    console.print(f"  Black Dice: {stats.total_black_dice}")
    console.print(
        f"  Green Dice: {stats.total_green_dice} (from red swirls: {build.insanity_track.green_dice_bonus})"
    )
    console.print(f"  Total Dice: {stats.total_dice}")

    console.print("\n[bold]Expected Outcomes (per roll):[/bold]")
    console.print(f"  Expected Successes: {stats.expected_successes:.2f}")
    console.print(f"  Expected Tentacles: {stats.expected_tentacles:.2f}")
    console.print(f"  Expected Elder Signs: {stats.expected_elder_signs:.2f}")

    console.print("\n[bold]Probabilities:[/bold]")
    console.print(f"  P(At Least 1 Success): {stats.prob_at_least_1_success * 100:.1f}%")
    console.print(f"  P(At Least 1 Tentacle): {stats.prob_at_least_1_tentacle * 100:.1f}%")
    console.print(f"  P(At Least 1 Elder Sign): {stats.prob_at_least_1_elder * 100:.1f}%")

    if stats.elder_signs_converted_to_successes > 0:
        console.print(
            f"\n[bold]Elder Sign Conversion:[/bold] {stats.elder_signs_converted_to_successes:.2f} elder signs → successes"
        )

    # Display capabilities
    if stats.wounds_healed_per_turn > 0 or stats.stress_healed_per_turn > 0:
        console.print("\n[bold]Healing Capabilities:[/bold]")
        if stats.wounds_healed_per_turn > 0:
            console.print(f"  Wounds Healed: {stats.wounds_healed_per_turn}")
        if stats.stress_healed_per_turn > 0:
            console.print(f"  Stress Healed: {stats.stress_healed_per_turn}")

    if stats.rerolls_per_roll > 0:
        console.print(f"\n[bold]Rerolls:[/bold] {stats.rerolls_per_roll} per roll")

    # Display insanity track info
    console.print("\n[bold]Insanity Track:[/bold]")
    console.print(f"  Current Insanity: Slot {build.insanity_track.current_insanity}")
    console.print(f"  Red Swirls Reached: {build.insanity_track.red_swirls_reached}/6")
    console.print(f"  Level-Ups Available: {build.insanity_track.level_ups_available}")
    console.print(f"  Green Dice Bonus: +{build.insanity_track.green_dice_bonus}")
    if build.insanity_track.next_red_swirl:
        console.print(
            f"  Next Red Swirl: Slot {build.insanity_track.next_red_swirl} "
            f"({build.insanity_track.tentacles_until_next_red_swirl} tentacles away)"
        )
    console.print(f"  Tentacles Until Death: {build.insanity_track.tentacles_until_death}")


if __name__ == "__main__":
    main()
