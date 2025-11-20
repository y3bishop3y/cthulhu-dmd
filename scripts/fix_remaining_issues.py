#!/usr/bin/env python3
"""
Fix remaining issues in common_powers.json with manual corrections.

This script applies specific fixes for known problematic descriptions.
"""

import json
import sys
from pathlib import Path
from typing import Final

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/fix_remaining_issues.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/fix_remaining_issues.py [options]\n\n"
        "Recommended: uv run ./scripts/fix_remaining_issues.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Manual corrections for known issues
MANUAL_CORRECTIONS: Final[dict] = {
    "Brawling": {
        1: "When you attack, you may target figures in your space. Gain 1 green dice while attacking a target in your space.",
    },
    "Marksman": {
        3: "You may attack a target 1 additional space away (2 total).",
    },
    "Swiftness": {
        3: "You may perform 1 free Run action each turn. When you Run, you may Sneak 3 times.",
    },
    "Toughness": {
        3: "Instead, you may reduce wounds taken and loss of sanity by 1 when attacked or rolling for Fire.",
        4: "Instead, you may reduce wounds taken and loss of sanity by 2 when attacked or rolling for Fire. You have 1 free reroll when attacked or rolling for Fire.",
    },
}


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data",
    help="Data directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without updating files",
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="Create backup before updating (default: True)",
)
def main(data_dir: Path, dry_run: bool, backup: bool):
    """Fix remaining issues in common_powers.json with manual corrections."""
    console.print(
        Panel.fit(
            "[bold cyan]Fix Remaining Issues[/bold cyan]\n"
            "Applying manual corrections for known problematic descriptions",
            border_style="cyan",
        )
    )

    common_powers_path = data_dir / "common_powers.json"
    if not common_powers_path.exists():
        console.print(f"[red]Error: {common_powers_path} not found![/red]")
        sys.exit(1)

    # Load existing data
    console.print(f"[cyan]Loading {common_powers_path}...[/cyan]")
    with open(common_powers_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[green]✓ Loaded {len(powers_data)} powers[/green]\n")

    # Track changes
    total_fixed = 0

    # Apply manual corrections
    for power in powers_data:
        power_name = power["name"]
        if power_name not in MANUAL_CORRECTIONS:
            continue

        console.print(f"[bold cyan]{power_name}[/bold cyan]")
        corrections = MANUAL_CORRECTIONS[power_name]

        for level_data in power["levels"]:
            level = level_data["level"]
            if level not in corrections:
                continue

            original_desc = level_data["description"]
            corrected_desc = corrections[level]

            if original_desc != corrected_desc:
                console.print(f"  Level {level}: [yellow]Applying manual correction[/yellow]")
                console.print(f"    Before: {original_desc[:100]}{'...' if len(original_desc) > 100 else ''}")
                console.print(f"    After:  {corrected_desc[:100]}{'...' if len(corrected_desc) > 100 else ''}")

                level_data["description"] = corrected_desc
                total_fixed += 1

        console.print()

    # Summary
    console.print("=" * 80)
    console.print("[bold cyan]Summary[/bold cyan]")
    console.print("=" * 80)
    console.print(f"Descriptions fixed: {total_fixed}")

    if dry_run:
        console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
    else:
        # Create backup
        if backup:
            backup_path = common_powers_path.with_suffix(common_powers_path.suffix + ".backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(powers_data, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓ Backup created: {backup_path}[/green]")

        # Write updated data
        with open(common_powers_path, "w", encoding="utf-8") as f:
            json.dump(powers_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Updated {common_powers_path}[/green]")
        console.print(f"[green]✓ Fixed {total_fixed} descriptions[/green]")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()

