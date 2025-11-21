#!/usr/bin/env python3
"""Convert pixel coordinates to percentages for OCR region constants.

This script helps convert the pixel coordinates you see on annotated images
to the percentage values needed in the constants file.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import cv2
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install: pip install opencv-python rich")
    sys.exit(1)

console = Console()


def convert_pixels_to_percent(
    image_path: Path, x: int, y: int, width: int, height: int
) -> tuple[float, float, float, float]:
    """Convert pixel coordinates to percentages.

    Args:
        image_path: Path to image file
        x: X coordinate in pixels
        y: Y coordinate in pixels
        width: Width in pixels
        height: Height in pixels

    Returns:
        Tuple of (x_percent, y_percent, width_percent, height_percent)
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    img_height, img_width = img.shape[:2]

    x_pct = (x / img_width) * 100
    y_pct = (y / img_height) * 100
    width_pct = (width / img_width) * 100
    height_pct = (height / img_height) * 100

    return (x_pct / 100, y_pct / 100, width_pct / 100, height_pct / 100)


def main() -> None:
    """Main entry point."""
    import click

    @click.command()
    @click.option(
        "--image",
        type=click.Path(exists=True, path_type=Path),
        required=True,
        help="Path to image file (front.jpg or back.jpg)",
    )
    @click.option(
        "--x",
        type=int,
        required=True,
        help="X coordinate in pixels",
    )
    @click.option(
        "--y",
        type=int,
        required=True,
        help="Y coordinate in pixels",
    )
    @click.option(
        "--width",
        type=int,
        required=True,
        help="Width in pixels",
    )
    @click.option(
        "--height",
        type=int,
        required=True,
        help="Height in pixels",
    )
    def convert(image: Path, x: int, y: int, width: int, height: int) -> None:
        """Convert pixel coordinates to percentages."""
        try:
            x_pct, y_pct, w_pct, h_pct = convert_pixels_to_percent(image, x, y, width, height)

            table = Table(title="Coordinate Conversion")
            table.add_column("Type", style="cyan")
            table.add_column("Pixels", justify="right")
            table.add_column("Percent", justify="right")
            table.add_column("Decimal", justify="right")

            table.add_row("X", str(x), f"{x_pct*100:.2f}%", f"{x_pct:.4f}")
            table.add_row("Y", str(y), f"{y_pct*100:.2f}%", f"{y_pct:.4f}")
            table.add_row("Width", str(width), f"{w_pct*100:.2f}%", f"{w_pct:.4f}")
            table.add_row("Height", str(height), f"{h_pct*100:.2f}%", f"{h_pct:.4f}")

            console.print(table)
            console.print(f"\n[bold]Python constant value:[/bold]")
            console.print(f"({x_pct:.4f}, {y_pct:.4f}, {w_pct:.4f}, {h_pct:.4f})")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    convert()


if __name__ == "__main__":
    main()

