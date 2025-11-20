#!/usr/bin/env python3
"""
Power Combination Analysis Script

Demonstrates how to combine multiple powers and calculate their combined effects.
"""

import json
import sys
from pathlib import Path
from typing import List

try:
    import click
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/analysis/power_combiner.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/analysis/power_combiner.py [options]\n\n"
        "Recommended: uv run ./scripts/analysis/power_combiner.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.character import CommonPower as CommonPowerModel
from scripts.models.power_combination import (
    PowerCombination,
    PowerCombinationCalculator,
    create_power_effect_from_level,
)

console = Console()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
COMMON_POWERS_FILE = DATA_DIR / "common_powers.json"


def load_common_powers() -> List[CommonPowerModel]:
    """Load common powers from JSON file."""
    if not COMMON_POWERS_FILE.exists():
        console.print(f"[red]Error: {COMMON_POWERS_FILE} not found[/red]")
        sys.exit(1)

    with open(COMMON_POWERS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    return [CommonPowerModel.from_dict(power_dict) for power_dict in data]


@click.command()
@click.option(
    "--power",
    multiple=True,
    help="Power name and level (e.g., 'Marksman:2' or 'Arcane Mastery:1')",
)
@click.option(
    "--base-black",
    default=3,
    help="Base black dice count (default: 3)",
)
@click.option(
    "--base-green",
    default=0,
    help="Base green dice count (default: 0)",
)
@click.option(
    "--list-powers",
    is_flag=True,
    help="List all available powers",
)
def main(power: tuple, base_black: int, base_green: int, list_powers: bool):
    """Combine multiple powers and calculate their combined effects."""
    common_powers = load_common_powers()

    if list_powers:
        table = Table(title="Available Powers")
        table.add_column("Power Name", style="cyan")
        table.add_column("Levels", style="green")

        for power_model in common_powers:
            power_name = power_model.name
            levels = ", ".join(str(level.level) for level in power_model.levels)
            table.add_row(power_name, levels)

        console.print(table)
        return

    if not power:
        console.print("[yellow]No powers specified. Use --power to add powers.[/yellow]")
        console.print("Example: --power 'Marksman:2' --power 'Arcane Mastery:1'")
        console.print("Use --list-powers to see available powers.")
        return

    # Create power combination
    combination = PowerCombination(
        base_black_dice=base_black,
        base_green_dice=base_green,
    )

    # Parse power specifications
    for power_spec in power:
        if ":" not in power_spec:
            console.print(f"[red]Error: Invalid power specification: {power_spec}[/red]")
            console.print("Format: 'PowerName:Level' (e.g., 'Marksman:2')")
            continue

        power_name, level_str = power_spec.split(":", 1)
        try:
            level = int(level_str)
        except ValueError:
            console.print(f"[red]Error: Invalid level: {level_str}[/red]")
            continue

        # Find power
        power_model = None
        for p in common_powers:
            if p.name == power_name:
                power_model = p
                break

        if power_model is None:
            available = ", ".join(p.name for p in common_powers)
            console.print(f"[red]Error: Power '{power_name}' not found[/red]")
            console.print(f"Available powers: {available}")
            continue

        # Find level
        level_data = None
        for level_item in power_model.levels:
            if level_item.level == level:
                level_data = level_item
                break

        if level_data is None:
            available_levels = ", ".join(str(level_item.level) for level_item in power_model.levels)
            console.print(f"[red]Error: Power '{power_name}' has no level {level}[/red]")
            console.print(f"Available levels: {available_levels}")
            continue

        # Create effect
        effect = create_power_effect_from_level(power_name, level_data)
        combination.effects.append(effect)

    if not combination.effects:
        console.print("[red]Error: No valid powers to combine[/red]")
        return

    # Calculate combined statistics
    calculator = PowerCombinationCalculator()
    stats = calculator.calculate_with_elder_conversion(combination)

    # Display results
    console.print("\n[bold cyan]Power Combination Analysis[/bold cyan]\n")

    # Power list
    table = Table(title="Active Powers")
    table.add_column("Power", style="cyan")
    table.add_column("Level", style="green")
    table.add_column("Effect", style="yellow")

    for effect in combination.effects:
        table.add_row(
            effect.power_name,
            str(effect.level),
            effect.power_name,  # TODO: Show actual effect description
        )

    console.print(table)

    # Dice summary
    console.print("\n[bold]Dice Summary:[/bold]")
    console.print(f"  Black Dice: {combination.total_black_dice}")
    console.print(f"  Green Dice: {combination.total_green_dice}")
    console.print(f"  Total Dice: {combination.total_black_dice + combination.total_green_dice}")

    # Statistics
    console.print("\n[bold]Combined Statistics:[/bold]")
    console.print(f"  Expected Successes: {stats['expected_successes']:.2f}")
    console.print(f"  Expected Tentacles: {stats['expected_tentacles']:.2f}")
    console.print(f"  Expected Elder Signs: {stats['expected_elder_signs']:.2f}")
    console.print(f"  P(At Least 1 Success): {stats['prob_at_least_1_success'] * 100:.1f}%")
    console.print(f"  P(At Least 1 Tentacle): {stats['prob_at_least_1_tentacle'] * 100:.1f}%")

    if "elder_signs_converted" in stats:
        console.print(f"  Elder Signs Converted to Successes: {stats['elder_signs_converted']:.2f}")

    # Healing summary
    wounds, stress = combination.total_healing
    if wounds > 0 or stress > 0:
        console.print("\n[bold]Healing:[/bold]")
        if wounds > 0:
            console.print(f"  Wounds Healed: {wounds}")
        if stress > 0:
            console.print(f"  Stress Healed: {stress}")

    # Rerolls
    if combination.total_rerolls > 0:
        console.print(f"\n[bold]Rerolls:[/bold] {combination.total_rerolls}")


if __name__ == "__main__":
    main()
