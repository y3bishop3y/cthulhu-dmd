#!/usr/bin/env python3
"""Helper script to adjust OCR extraction region coordinates.

This script allows you to adjust region coordinates and immediately see
the results on the annotated images.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install: pip install rich")
    sys.exit(1)

console = Console()


def show_current_regions() -> None:
    """Display current region coordinates."""
    from scripts.cli.parse.parsing_constants import (
        COMMON_POWER_REGIONS,
        FRONT_CARD_MOTTO_END_PERCENT,
        FRONT_CARD_MOTTO_START_PERCENT,
        FRONT_CARD_STORY_HEIGHT_PERCENT,
        FRONT_CARD_STORY_START_PERCENT,
        FRONT_CARD_TOP_PERCENT,
    )

    table = Table(title="Current Front Card Regions")
    table.add_column("Region", style="cyan")
    table.add_column("Start %", justify="right")
    table.add_column("End %", justify="right")
    table.add_column("Height %", justify="right")

    table.add_row(
        "Name",
        "0",
        f"{FRONT_CARD_TOP_PERCENT*100/2:.1f}",
        f"{FRONT_CARD_TOP_PERCENT*100/2:.1f}",
    )
    table.add_row(
        "Location",
        f"{FRONT_CARD_TOP_PERCENT*100/2:.1f}",
        f"{FRONT_CARD_TOP_PERCENT*100:.1f}",
        f"{FRONT_CARD_TOP_PERCENT*100/2:.1f}",
    )
    table.add_row(
        "Motto",
        f"{FRONT_CARD_MOTTO_START_PERCENT*100:.1f}",
        f"{FRONT_CARD_MOTTO_END_PERCENT*100:.1f}",
        f"{(FRONT_CARD_MOTTO_END_PERCENT - FRONT_CARD_MOTTO_START_PERCENT)*100:.1f}",
    )
    table.add_row(
        "Story",
        f"{FRONT_CARD_STORY_START_PERCENT*100:.1f}",
        f"{FRONT_CARD_STORY_START_PERCENT*100 + FRONT_CARD_STORY_HEIGHT_PERCENT*100:.1f}",
        f"{FRONT_CARD_STORY_HEIGHT_PERCENT*100:.1f}",
    )

    console.print(table)

    table2 = Table(title="Current Back Card Common Power Regions")
    table2.add_column("Region", style="cyan")
    table2.add_column("X %", justify="right")
    table2.add_column("Y %", justify="right")
    table2.add_column("Width %", justify="right")
    table2.add_column("Height %", justify="right")

    for idx, (x, y, w, h) in enumerate(COMMON_POWER_REGIONS):
        table2.add_row(f"Region {idx+1}", f"{x*100:.0f}", f"{y*100:.0f}", f"{w*100:.0f}", f"{h*100:.0f}")

    console.print("\n")
    console.print(table2)


def update_front_card_regions() -> None:
    """Update front card region coordinates."""
    console.print("\n[bold cyan]Front Card Region Adjustment[/bold cyan]")
    console.print("Enter new percentages (0-100), or press Enter to keep current value\n")

    from scripts.cli.parse.parsing_constants import (
        FRONT_CARD_MOTTO_END_PERCENT,
        FRONT_CARD_MOTTO_START_PERCENT,
        FRONT_CARD_STORY_HEIGHT_PERCENT,
        FRONT_CARD_STORY_START_PERCENT,
        FRONT_CARD_TOP_PERCENT,
    )

    # Read the constants file
    constants_file = project_root / "scripts" / "cli" / "parse" / "parsing_constants.py"
    content = constants_file.read_text()

    # Get new values
    new_top = Prompt.ask(
        f"Top region (name+location) [current: {FRONT_CARD_TOP_PERCENT*100:.1f}%]",
        default=str(FRONT_CARD_TOP_PERCENT * 100),
    )
    new_motto_start = Prompt.ask(
        f"Motto start [current: {FRONT_CARD_MOTTO_START_PERCENT*100:.1f}%]",
        default=str(FRONT_CARD_MOTTO_START_PERCENT * 100),
    )
    new_motto_end = Prompt.ask(
        f"Motto end [current: {FRONT_CARD_MOTTO_END_PERCENT*100:.1f}%]",
        default=str(FRONT_CARD_MOTTO_END_PERCENT * 100),
    )
    new_story_start = Prompt.ask(
        f"Story start [current: {FRONT_CARD_STORY_START_PERCENT*100:.1f}%]",
        default=str(FRONT_CARD_STORY_START_PERCENT * 100),
    )
    new_story_height = Prompt.ask(
        f"Story height [current: {FRONT_CARD_STORY_HEIGHT_PERCENT*100:.1f}%]",
        default=str(FRONT_CARD_STORY_HEIGHT_PERCENT * 100),
    )

    # Convert to decimals
    new_top_val = float(new_top) / 100
    new_motto_start_val = float(new_motto_start) / 100
    new_motto_end_val = float(new_motto_end) / 100
    new_story_start_val = float(new_story_start) / 100
    new_story_height_val = float(new_story_height) / 100

    # Update the file
    content = content.replace(
        f"FRONT_CARD_TOP_PERCENT: Final[float] = {FRONT_CARD_TOP_PERCENT}",
        f"FRONT_CARD_TOP_PERCENT: Final[float] = {new_top_val}",
    )
    content = content.replace(
        f"FRONT_CARD_MOTTO_START_PERCENT: Final[float] = {FRONT_CARD_MOTTO_START_PERCENT}",
        f"FRONT_CARD_MOTTO_START_PERCENT: Final[float] = {new_motto_start_val}",
    )
    content = content.replace(
        f"FRONT_CARD_MOTTO_END_PERCENT: Final[float] = {FRONT_CARD_MOTTO_END_PERCENT}",
        f"FRONT_CARD_MOTTO_END_PERCENT: Final[float] = {new_motto_end_val}",
    )
    content = content.replace(
        f"FRONT_CARD_STORY_START_PERCENT: Final[float] = {FRONT_CARD_STORY_START_PERCENT}",
        f"FRONT_CARD_STORY_START_PERCENT: Final[float] = {new_story_start_val}",
    )
    content = content.replace(
        f"FRONT_CARD_STORY_HEIGHT_PERCENT: Final[float] = {FRONT_CARD_STORY_HEIGHT_PERCENT}",
        f"FRONT_CARD_STORY_HEIGHT_PERCENT: Final[float] = {new_story_height_val}",
    )

    constants_file.write_text(content)
    console.print(f"\n[green]✓ Updated front card regions[/green]")


def update_back_card_regions() -> None:
    """Update back card common power region coordinates."""
    console.print("\n[bold cyan]Back Card Common Power Region Adjustment[/bold cyan]")
    console.print("Enter new percentages (0-100), or press Enter to keep current value\n")

    from scripts.cli.parse.parsing_constants import COMMON_POWER_REGIONS

    # Read the constants file
    constants_file = project_root / "scripts" / "cli" / "parse" / "parsing_constants.py"
    content = constants_file.read_text()

    new_regions = []
    for idx, (x, y, w, h) in enumerate(COMMON_POWER_REGIONS):
        console.print(f"\n[bold]Region {idx+1}:[/bold]")
        new_x = Prompt.ask(f"  X start [current: {x*100:.0f}%]", default=str(x * 100))
        new_y = Prompt.ask(f"  Y start [current: {y*100:.0f}%]", default=str(y * 100))
        new_w = Prompt.ask(f"  Width [current: {w*100:.0f}%]", default=str(w * 100))
        new_h = Prompt.ask(f"  Height [current: {h*100:.0f}%]", default=str(h * 100))
        new_regions.append((float(new_x) / 100, float(new_y) / 100, float(new_w) / 100, float(new_h) / 100))

    # Update the file - find and replace the COMMON_POWER_REGIONS definition
    import re

    # Build the new regions list string
    new_regions_str = "[\n"
    for idx, (x, y, w, h) in enumerate(new_regions):
        new_regions_str += f"    ({x}, {y}, {w}, {h}),"
        if idx < len(new_regions) - 1:
            new_regions_str += f"  # Region {idx+1}\n"
        else:
            new_regions_str += f"  # Region {idx+1}\n"
    new_regions_str += "]"

    # Find and replace the region list
    pattern = r"COMMON_POWER_REGIONS: Final\[List\[Tuple\[float, float, float, float\]\]\] = \[.*?\]"
    content = re.sub(pattern, f"COMMON_POWER_REGIONS: Final[List[Tuple[float, float, float, float]]] = {new_regions_str}", content, flags=re.DOTALL)

    constants_file.write_text(content)
    console.print(f"\n[green]✓ Updated back card regions[/green]")


def main() -> None:
    """Main entry point."""
    import click

    @click.command()
    @click.option(
        "--character-dir",
        type=click.Path(exists=True, path_type=Path),
        help="Character directory to visualize after adjustment",
    )
    def adjust(character_dir: Path | None) -> None:
        """Adjust OCR extraction region coordinates."""
        console.print("[bold cyan]OCR Region Coordinate Adjuster[/bold cyan]\n")

        show_current_regions()

        console.print("\n[bold]Which regions would you like to adjust?[/bold]")
        console.print("1. Front card regions (name, location, motto, story)")
        console.print("2. Back card common power regions")
        console.print("3. Both")

        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")

        if choice in ["1", "3"]:
            update_front_card_regions()

        if choice in ["2", "3"]:
            update_back_card_regions()

        console.print("\n[bold]Updated regions:[/bold]")
        show_current_regions()

        if character_dir:
            console.print(f"\n[bold]Regenerating visualization for {character_dir}...[/bold]")
            from scripts.cli.tools.visualize_extraction_regions import (
                draw_back_card_regions,
                draw_front_card_regions,
            )

            # Find images
            front_path = None
            back_path = None
            for ext in [".png", ".webp", ".jpg", ".jpeg"]:
                front_candidate = character_dir / f"front{ext}"
                back_candidate = character_dir / f"back{ext}"
                if front_candidate.exists() and front_path is None:
                    front_path = front_candidate
                if back_candidate.exists() and back_path is None:
                    back_path = back_candidate

            if front_path:
                output_front = character_dir / f"{front_path.stem}_annotated{front_path.suffix}"
                draw_front_card_regions(front_path, output_front)
                console.print(f"[green]✓[/green] Updated: {output_front}")

            if back_path:
                output_back = character_dir / f"{back_path.stem}_annotated{back_path.suffix}"
                draw_back_card_regions(back_path, output_back)
                console.print(f"[green]✓[/green] Updated: {output_back}")

    adjust()


if __name__ == "__main__":
    main()

