#!/usr/bin/env python3
"""Visualize OCR extraction regions on character card images.

This script draws colored rectangles on card images to show the regions
being used for OCR extraction, helping to verify and adjust coordinates.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import cv2
    import numpy as np
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install: pip install opencv-python rich numpy")
    sys.exit(1)

from scripts.cli.parse.parsing_constants import (
    COMMON_POWER_REGIONS,
    FRONT_CARD_MOTTO_END_PERCENT,
    FRONT_CARD_MOTTO_START_PERCENT,
    FRONT_CARD_STORY_HEIGHT_PERCENT,
    FRONT_CARD_STORY_START_PERCENT,
    FRONT_CARD_TOP_PERCENT,
    SPECIAL_POWER_REGION,
)

console = Console()


def draw_front_card_regions(image_path: Path, output_path: Path) -> None:
    """Draw extraction regions on front card image.

    Args:
        image_path: Path to front card image
        output_path: Path to save annotated image
    """
    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        console.print(f"[red]Error: Could not load image {image_path}[/red]")
        return

    h, w = img.shape[:2]

    # Use 45% width for most front card regions
    region_width = int(w * 0.45)
    # Start X position at 5% from the left
    x_start = int(w * 0.05)

    # Name region has width 45% (same as other regions), height 6.8%, starts at 26% Y
    name_width = int(w * 0.45)  # Width is 45% (same as other regions)
    name_start_y = int(h * 0.26)
    name_height = int(h * 0.068)  # Height is 6.8%

    # Define regions with colors and labels
    regions = [
        {
            "name": "Name Region",
            "coords": (x_start, name_start_y, name_width, name_height),
            "color": (0, 255, 0),  # Green
        },
        {
            "name": "Location Region",
            "coords": (x_start, int(h * 0.32), region_width, int(h * 0.05)),  # Start at 32%, height 5% for now
            "color": (255, 0, 0),  # Blue
        },
        {
            "name": "Motto Region",
            "coords": (
                x_start,
                int(h * FRONT_CARD_MOTTO_START_PERCENT),
                region_width,
                int(h * (FRONT_CARD_MOTTO_END_PERCENT - FRONT_CARD_MOTTO_START_PERCENT)),
            ),
            "color": (0, 0, 255),  # Red
        },
        {
            "name": "Story Region",
            "coords": (
                x_start,
                int(h * FRONT_CARD_STORY_START_PERCENT),
                region_width,
                int(h * FRONT_CARD_STORY_HEIGHT_PERCENT),
            ),
            "color": (255, 255, 0),  # Cyan
        },
    ]

    # Draw rectangles and labels
    annotated_img = img.copy()
    for region in regions:
        x, y, width, height = region["coords"]
        color = region["color"]
        name = region["name"]

        # Draw rectangle
        cv2.rectangle(annotated_img, (x, y), (x + width, y + height), color, 3)

        # Calculate percentages for display
        x_pct = (x / w) * 100
        y_pct = (y / h) * 100
        width_pct = (width / w) * 100
        height_pct = (height / h) * 100

        # Add label with both pixel coordinates and percentages
        # Use smaller fonts (2 sizes smaller than before)
        font_scale_large = 0.8  # Was 1.2, now 0.8 (2 sizes smaller)
        font_scale_medium = 0.6  # Was 1.0, now 0.6 (2 sizes smaller)
        font_thickness_large = 2  # Was 3, now 2
        font_thickness_medium = 1  # Was 2, now 1

        label_text = f"{name}"
        label_text2 = f"Pixels: ({x},{y},{width},{height})"
        label_text3 = f"Percent: ({x_pct:.1f}%,{y_pct:.1f}%,{width_pct:.1f}%,{height_pct:.1f}%)"

        # Calculate text size for multi-line label
        (text_width1, text_height1), _ = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_large, font_thickness_large
        )
        (text_width2, text_height2), _ = cv2.getTextSize(
            label_text2, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
        )
        (text_width3, text_height3), _ = cv2.getTextSize(
            label_text3, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
        )

        max_width = max(text_width1, text_width2, text_width3)
        total_height = text_height1 + text_height2 + text_height3 + 15
        padding = 5

        # For Story, Motto, and Location regions, place label inside the box
        # Story: bottom-left, Motto & Location: bottom-right
        # For other regions, place above the box
        if name == "Story Region":
            # Position label inside the box at bottom-left
            label_x = x + padding
            label_y = y + height - total_height - padding
        elif name == "Motto Region":
            # Position label inside the box at bottom-left
            label_x = x + padding
            label_y = y + height - total_height - padding

            # Draw label background with border for better visibility
            bg_color = (0, 0, 0)  # Black background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                bg_color,
                -1,  # Filled
            )
            # Add white border around background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                (255, 255, 255),
                1,  # Border thickness
            )

            # Add label text (multi-line) inside the box
            cv2.putText(
                annotated_img,
                label_text,
                (label_x, label_y + text_height1),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_large,
                color,
                font_thickness_large,
            )
            cv2.putText(
                annotated_img,
                label_text2,
                (label_x, label_y + text_height1 + text_height2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (255, 255, 255),  # Bright white
                font_thickness_medium,
            )
            cv2.putText(
                annotated_img,
                label_text3,
                (label_x, label_y + text_height1 + text_height2 + text_height3 + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (200, 255, 200),  # Light green for percentages
                font_thickness_medium,
            )
        elif name == "Motto Region" or name == "Location Region":
            # Position label inside the box at bottom-right
            label_x = x + width - max_width - padding * 2
            label_y = y + height - total_height - padding

            # Draw label background with border for better visibility
            bg_color = (0, 0, 0)  # Black background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                bg_color,
                -1,  # Filled
            )
            # Add white border around background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                (255, 255, 255),
                1,  # Border thickness
            )

            # Add label text (multi-line) inside the box
            cv2.putText(
                annotated_img,
                label_text,
                (label_x, label_y + text_height1),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_large,
                color,
                font_thickness_large,
            )
            cv2.putText(
                annotated_img,
                label_text2,
                (label_x, label_y + text_height1 + text_height2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (255, 255, 255),  # Bright white
                font_thickness_medium,
            )
            cv2.putText(
                annotated_img,
                label_text3,
                (label_x, label_y + text_height1 + text_height2 + text_height3 + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (200, 255, 200),  # Light green for percentages
                font_thickness_medium,
            )
        else:
            # Position label above the box for other regions
            label_x = x + padding
            label_y = y - total_height - padding

            # Draw label background with border for better visibility
            bg_color = (0, 0, 0)  # Black background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                bg_color,
                -1,  # Filled
            )
            # Add white border around background
            cv2.rectangle(
                annotated_img,
                (label_x - 2, label_y - 2),
                (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
                (255, 255, 255),
                1,  # Border thickness
            )

            # Add label text (multi-line) with better contrast
            cv2.putText(
                annotated_img,
                label_text,
                (label_x, label_y + text_height1),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_large,
                color,
                font_thickness_large,
            )
            cv2.putText(
                annotated_img,
                label_text2,
                (label_x, label_y + text_height1 + text_height2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (255, 255, 255),  # Bright white
                font_thickness_medium,
            )
            cv2.putText(
                annotated_img,
                label_text3,
                (label_x, label_y + text_height1 + text_height2 + text_height3 + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale_medium,
                (200, 255, 200),  # Light green for percentages
                font_thickness_medium,
            )

    # Save annotated image
    cv2.imwrite(str(output_path), annotated_img)
    console.print(f"[green]✓[/green] Saved annotated front card: {output_path}")


def draw_back_card_regions(image_path: Path, output_path: Path) -> None:
    """Draw extraction regions on back card image.

    Args:
        image_path: Path to back card image
        output_path: Path to save annotated image
    """
    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        console.print(f"[red]Error: Could not load image {image_path}[/red]")
        return

    h, w = img.shape[:2]

    # Define colors for different regions
    colors = [
        (255, 165, 0),  # Orange for special power
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
    ]

    annotated_img = img.copy()

    # Draw special power region first
    sp_x_pct, sp_y_pct, sp_width_pct, sp_height_pct = SPECIAL_POWER_REGION
    sp_x = int(w * sp_x_pct)
    sp_y = int(h * sp_y_pct)
    sp_width = int(w * sp_width_pct)
    sp_height = int(h * sp_height_pct)
    sp_color = colors[0]  # Orange

    # Draw special power rectangle outline first (so sub-regions are on top)
    cv2.rectangle(annotated_img, (sp_x, sp_y), (sp_x + sp_width, sp_y + sp_height), sp_color, 3)

    # Create 4 vertical sub-regions for special power levels
    # Level 1: 32%, Level 2: 22.67%, Level 3: 19.87%, Level 4: 25.45% (of special power region width)
    level_width_pcts = [
        sp_width_pct * 0.32,      # Level 1: 32%
        sp_width_pct * 0.2267,     # Level 2: 22.67%
        sp_width_pct * 0.1987,     # Level 3: 19.87%
        sp_width_pct * 0.2545,     # Level 4: 25.45%
    ]
    level_colors = [
        (255, 200, 0),    # Gold for Level 1
        (255, 140, 0),    # Dark orange for Level 2
        (255, 100, 0),    # Darker orange for Level 3
        (255, 60, 0),     # Darkest orange for Level 4
    ]

    # Draw the 4 level sub-regions (vertical splits)
    current_x_pct = sp_x_pct
    for level_idx in range(4):
        level_x_pct = current_x_pct
        level_x = int(w * level_x_pct)
        level_width_pct = level_width_pcts[level_idx]
        level_width = int(w * level_width_pct)
        level_color = level_colors[level_idx]

        # Update current_x_pct for next iteration
        current_x_pct += level_width_pct

        # Draw rectangle for this level (same Y and Height as special power region)
        cv2.rectangle(
            annotated_img,
            (level_x, sp_y),
            (level_x + level_width, sp_y + sp_height),
            level_color,
            2,  # Thinner border for sub-regions
        )

        # Add label for this level
        font_scale = 0.5
        font_thickness = 1
        label_text = f"Level {level_idx + 1}"

        (text_width, text_height), _ = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
        )

        # Position label at top-left of sub-region
        label_x = level_x + 5
        label_y = sp_y + text_height + 5

        # Draw label background
        cv2.rectangle(
            annotated_img,
            (label_x - 2, label_y - text_height - 2),
            (label_x + text_width + 2, label_y + 2),
            (0, 0, 0),
            -1,
        )

        # Draw label text
        cv2.putText(
            annotated_img,
            label_text,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            level_color,
            font_thickness,
        )

    # Add special power label (same style as front card)
    font_scale_large = 0.8
    font_scale_medium = 0.6
    font_thickness_large = 2
    font_thickness_medium = 1

    sp_label_text = "Special Power Region"
    sp_label_text2 = f"Pixels: ({sp_x},{sp_y},{sp_width},{sp_height})"
    sp_label_text3 = f"Percent: ({sp_x_pct*100:.0f}%,{sp_y_pct*100:.0f}%,{sp_width_pct*100:.0f}%,{sp_height_pct*100:.0f}%)"

    (sp_text_width1, sp_text_height1), _ = cv2.getTextSize(
        sp_label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_large, font_thickness_large
    )
    (sp_text_width2, sp_text_height2), _ = cv2.getTextSize(
        sp_label_text2, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
    )
    (sp_text_width3, sp_text_height3), _ = cv2.getTextSize(
        sp_label_text3, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
    )

    sp_max_width = max(sp_text_width1, sp_text_width2, sp_text_width3)
    sp_total_height = sp_text_height1 + sp_text_height2 + sp_text_height3 + 15
    sp_padding = 5

    # Position label inside the box at bottom-right
    sp_label_x = sp_x + sp_width - sp_max_width - sp_padding * 2
    sp_label_y = sp_y + sp_height - sp_total_height - sp_padding

    # Draw label background
    cv2.rectangle(
        annotated_img,
        (sp_label_x - 2, sp_label_y - 2),
        (sp_label_x + sp_max_width + sp_padding * 2 + 2, sp_label_y + sp_total_height + 2),
        (0, 0, 0),
        -1,
    )
    cv2.rectangle(
        annotated_img,
        (sp_label_x - 2, sp_label_y - 2),
        (sp_label_x + sp_max_width + sp_padding * 2 + 2, sp_label_y + sp_total_height + 2),
        (255, 255, 255),
        1,
    )

    # Add label text
    cv2.putText(
        annotated_img,
        sp_label_text,
        (sp_label_x, sp_label_y + sp_text_height1),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale_large,
        sp_color,
        font_thickness_large,
    )
    cv2.putText(
        annotated_img,
        sp_label_text2,
        (sp_label_x, sp_label_y + sp_text_height1 + sp_text_height2 + 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale_medium,
        (255, 255, 255),
        font_thickness_medium,
    )
    cv2.putText(
        annotated_img,
        sp_label_text3,
        (sp_label_x, sp_label_y + sp_text_height1 + sp_text_height2 + sp_text_height3 + 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale_medium,
        (200, 255, 200),
        font_thickness_medium,
    )

    # Draw rectangles for each common power region
    for idx, (x_pct, y_pct, width_pct, height_pct) in enumerate(COMMON_POWER_REGIONS):
        x = int(w * x_pct)
        y = int(h * y_pct)
        width = int(w * width_pct)
        height = int(h * height_pct)
        color = colors[idx + 1]  # Skip first color (orange) used for special power

        # Draw rectangle
        cv2.rectangle(annotated_img, (x, y), (x + width, y + height), color, 3)

        # Add label with both pixel coordinates and percentages
        # Use smaller fonts (2 sizes smaller than before)
        font_scale_large = 0.8  # Was 1.2, now 0.8 (2 sizes smaller)
        font_scale_medium = 0.6  # Was 1.0, now 0.6 (2 sizes smaller)
        font_thickness_large = 2  # Was 3, now 2
        font_thickness_medium = 1  # Was 2, now 1

        label_text = f"Common Power Region {idx+1}"
        color = colors[idx + 1]  # Skip first color (orange) used for special power
        label_text2 = f"Pixels: ({x},{y},{width},{height})"
        label_text3 = f"Percent: ({x_pct*100:.0f}%,{y_pct*100:.0f}%,{width_pct*100:.0f}%,{height_pct*100:.0f}%)"

        # Calculate text size for multi-line label
        (text_width1, text_height1), _ = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_large, font_thickness_large
        )
        (text_width2, text_height2), _ = cv2.getTextSize(
            label_text2, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
        )
        (text_width3, text_height3), _ = cv2.getTextSize(
            label_text3, cv2.FONT_HERSHEY_SIMPLEX, font_scale_medium, font_thickness_medium
        )

        max_width = max(text_width1, text_width2, text_width3)
        total_height = text_height1 + text_height2 + text_height3 + 15
        padding = 5  # Same padding as front card

        # Position label inside the box at bottom-right (same style as front card Motto/Location regions)
        label_x = x + width - max_width - padding * 2
        label_y = y + height - total_height - padding

        # Draw label background with border for better visibility
        bg_color = (0, 0, 0)  # Black background
        cv2.rectangle(
            annotated_img,
            (label_x - 2, label_y - 2),
            (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
            bg_color,
            -1,  # Filled
        )
        # Add white border around background
        cv2.rectangle(
            annotated_img,
            (label_x - 2, label_y - 2),
            (label_x + max_width + padding * 2 + 2, label_y + total_height + 2),
            (255, 255, 255),
            1,  # Border thickness (same as front card)
        )

        # Add label text (multi-line) inside the box
        cv2.putText(
            annotated_img,
            label_text,
            (label_x, label_y + text_height1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale_large,
            color,
            font_thickness_large,
        )
        cv2.putText(
            annotated_img,
            label_text2,
            (label_x, label_y + text_height1 + text_height2 + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale_medium,
            (255, 255, 255),  # Bright white
            font_thickness_medium,
        )
        cv2.putText(
            annotated_img,
            label_text3,
            (label_x, label_y + text_height1 + text_height2 + text_height3 + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale_medium,
            (200, 255, 200),  # Light green for percentages
            font_thickness_medium,
        )

    # Save annotated image
    cv2.imwrite(str(output_path), annotated_img)
    console.print(f"[green]✓[/green] Saved annotated back card: {output_path}")


def main() -> None:
    """Main entry point."""
    import click

    @click.command()
    @click.option(
        "--character-dir",
        type=click.Path(exists=True, path_type=Path),
        required=True,
        help="Character directory containing front.jpg/webp and back.jpg/webp",
    )
    @click.option(
        "--output-dir",
        type=click.Path(path_type=Path),
        help="Output directory for annotated images (default: same as character-dir)",
    )
    def visualize(character_dir: Path, output_dir: Path | None) -> None:
        """Visualize OCR extraction regions on character card images."""
        console.print("[bold cyan]OCR Region Visualizer[/bold cyan]\n")

        # Determine output directory
        if output_dir is None:
            output_dir = character_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find image files (check webp first since that's what we convert to)
        front_path = None
        back_path = None

        # Check for PNG first (converted versions), then webp, then jpg
        for ext in [".png", ".webp", ".jpg", ".jpeg"]:
            front_candidate = character_dir / f"front{ext}"
            back_candidate = character_dir / f"back{ext}"
            if front_candidate.exists() and front_path is None:
                front_path = front_candidate
            if back_candidate.exists() and back_path is None:
                back_path = back_candidate

        if not front_path:
            console.print("[red]Error: Could not find front card image[/red]")
            return

        if not back_path:
            console.print("[yellow]Warning: Could not find back card image[/yellow]")

        # Visualize regions
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("Annotating front card...", total=1)
            if front_path:
                output_front = output_dir / f"{front_path.stem}_annotated{front_path.suffix}"
                draw_front_card_regions(front_path, output_front)
            progress.update(task1, advance=1)

            if back_path:
                task2 = progress.add_task("Annotating back card...", total=1)
                output_back = output_dir / f"{back_path.stem}_annotated{back_path.suffix}"
                draw_back_card_regions(back_path, output_back)
                progress.update(task2, advance=1)

        console.print("\n[green]✓ Visualization complete![/green]")
        console.print(f"\nAnnotated images saved to: {output_dir}")
        console.print("\n[bold]Region Summary:[/bold]")
        console.print("\n[cyan]Front Card Regions:[/cyan]")
        console.print(f"  • Name: Top {FRONT_CARD_TOP_PERCENT*100/2:.1f}% (first half)")
        console.print(f"  • Location: Top {FRONT_CARD_TOP_PERCENT*100/2:.1f}% (second half)")
        console.print(f"  • Motto: {FRONT_CARD_MOTTO_START_PERCENT*100:.0f}% - {FRONT_CARD_MOTTO_END_PERCENT*100:.0f}%")
        console.print(f"  • Story: {FRONT_CARD_STORY_START_PERCENT*100:.0f}% - {FRONT_CARD_STORY_START_PERCENT*100 + FRONT_CARD_STORY_HEIGHT_PERCENT*100:.0f}%")
        console.print("\n[cyan]Back Card Common Power Regions:[/cyan]")
        for idx, (x_pct, y_pct, width_pct, height_pct) in enumerate(COMMON_POWER_REGIONS):
            console.print(f"  • Region {idx+1}: ({x_pct*100:.0f}%, {y_pct*100:.0f}%, {width_pct*100:.0f}%, {height_pct*100:.0f}%)")

    visualize()


if __name__ == "__main__":
    main()

