#!/usr/bin/env python3
"""
Update common_powers.json with statistical analysis for each power level.

This script analyzes each power level and adds statistical data including:
- Dice additions (green/black)
- Expected successes
- Tentacle risk
- Success increases
"""

import json
import sys
from pathlib import Path
from typing import Final

try:
    import click
    from rich.console import Console
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/update_common_powers_with_stats.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/update_common_powers_with_stats.py [options]\n\n"
        "Recommended: uv run ./scripts/update_common_powers_with_stats.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.cli.analyze.powers import (
    DATA_DIR,
    FILENAME_COMMON_POWERS,
    analyze_power_level,
)

console = Console()

# Constants
BACKUP_SUFFIX: Final[str] = ".backup"


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def main(data_dir: Path, dry_run: bool):
    """Update common_powers.json with statistical analysis for each power level."""
    console.print("[bold cyan]Updating Common Powers with Statistics[/bold cyan]\n")

    common_powers_path = data_dir / FILENAME_COMMON_POWERS
    if not common_powers_path.exists():
        console.print(f"[red]Error: {common_powers_path} not found![/red]")
        sys.exit(1)

    # Load existing data
    with open(common_powers_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[cyan]Processing {len(powers_data)} powers...[/cyan]\n")

    # Analyze and update each power
    updated_count = 0
    for power in powers_data:
        power_name = power["name"]
        console.print(f"[bold]{power_name}[/bold]")

        for level_data in power["levels"]:
            level = level_data["level"]
            description = level_data["description"]

            # Analyze this power level
            analysis = analyze_power_level(power_name, level, description)

            # Update level data with statistics and effect
            level_data["effect"] = analysis.effect
            level_data["statistics"] = {
                "green_dice_added": analysis.green_dice_added,
                "black_dice_added": analysis.black_dice_added,
                "base_expected_successes": round(analysis.base_expected_successes, 3),
                "enhanced_expected_successes": round(analysis.enhanced_expected_successes, 3),
                "expected_successes_increase": round(analysis.expected_successes_increase, 3),
                "expected_successes_percent_increase": round(
                    analysis.expected_successes_percent_increase, 2
                ),
                "max_successes_increase": analysis.max_successes_increase,
                "tentacle_risk": round(analysis.tentacle_risk, 3),
                "base_tentacle_risk": round(analysis.base_tentacle_risk, 3),
            }

            has_dice = analysis.dice_addition.adds_any_dice
            has_elder_conversion = analysis.elder_sign_conversion.elder_signs_as_successes > 0

            if has_dice or has_elder_conversion:
                effects = []
                if has_dice:
                    dice_info = []
                    if analysis.green_dice_added > 0:
                        dice_info.append(f"{analysis.green_dice_added} green")
                    if analysis.black_dice_added > 0:
                        dice_info.append(f"{analysis.black_dice_added} black")
                    effects.append(f"Adds {' + '.join(dice_info)} dice")

                if has_elder_conversion:
                    if analysis.elder_sign_conversion.converts_any_number:
                        effects.append("Counts any number of elder signs as successes")
                    else:
                        effects.append(
                            f"Counts {analysis.elder_sign_conversion.elder_signs_as_successes} elder sign(s) as successes"
                        )

                effect_str = " | ".join(effects)
                console.print(
                    f"  Level {level}: {effect_str} "
                    f"(+{analysis.expected_successes_increase:.2f} successes, "
                    f"{analysis.expected_successes_percent_increase:.1f}%)"
                )
                updated_count += 1
            else:
                console.print(f"  Level {level}: No dice added (other effect)")

        console.print()

    if dry_run:
        console.print("[yellow]DRY RUN - No changes made[/yellow]\n")
        console.print("Updated data preview:")
        console.print(json.dumps(powers_data, indent=2, ensure_ascii=False)[:500] + "...")
    else:
        # Create backup
        backup_path = common_powers_path.with_suffix(common_powers_path.suffix + BACKUP_SUFFIX)
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(powers_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Backup created: {backup_path}[/green]")

        # Write updated data
        with open(common_powers_path, "w", encoding="utf-8") as f:
            json.dump(powers_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Updated {updated_count} power levels with statistics[/green]")
        console.print(f"[green]✓ Saved to {common_powers_path}[/green]")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()
