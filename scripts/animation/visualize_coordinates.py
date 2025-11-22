#!/usr/bin/env python3
"""
Visualize extraction coordinates on a card image.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    import cv2
    import numpy as np
    from PIL import Image
    from rich.console import Console
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}", file=sys.stderr)
    sys.exit(1)

console = Console()


def draw_coordinates_on_image(
    image_path: Path,
    output_path: Path,
    x_percent: float,
    y_percent: float,
    width_percent: float,
    height_percent: float,
    color: tuple[int, int, int] = (0, 255, 0),  # Green (BGR)
    thickness: int = 4,
) -> None:
    """Draw extraction region on image.
    
    Args:
        image_path: Path to source image
        output_path: Path to save visualization
        x_percent: X coordinate as percentage (0-100)
        y_percent: Y coordinate as percentage (0-100)
        width_percent: Width as percentage (0-100)
        height_percent: Height as percentage (0-100)
        color: BGR color tuple for rectangle
        thickness: Line thickness
    """
    # Load image
    img_cv = cv2.imread(str(image_path))
    if img_cv is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    h, w = img_cv.shape[:2]
    
    # Convert percentages to pixels
    x = int(w * x_percent / 100.0)
    y = int(h * y_percent / 100.0)
    width = int(w * width_percent / 100.0)
    height = int(h * height_percent / 100.0)
    
    # Draw rectangle
    cv2.rectangle(img_cv, (x, y), (x + width, y + height), color, thickness)
    
    # Draw corner markers
    corner_size = 20
    # Top-left
    cv2.line(img_cv, (x, y), (x + corner_size, y), color, thickness)
    cv2.line(img_cv, (x, y), (x, y + corner_size), color, thickness)
    # Top-right
    cv2.line(img_cv, (x + width, y), (x + width - corner_size, y), color, thickness)
    cv2.line(img_cv, (x + width, y), (x + width, y + corner_size), color, thickness)
    # Bottom-left
    cv2.line(img_cv, (x, y + height), (x + corner_size, y + height), color, thickness)
    cv2.line(img_cv, (x, y + height), (x, y + height - corner_size), color, thickness)
    # Bottom-right
    cv2.line(img_cv, (x + width, y + height), (x + width - corner_size, y + height), color, thickness)
    cv2.line(img_cv, (x + width, y + height), (x + width, y + height - corner_size), color, thickness)
    
    # Add label
    label = f"X={x_percent:.0f}%, Y={y_percent:.0f}%, W={width_percent:.0f}%, H={height_percent:.0f}%"
    label2 = f"Pixels: X={x}, Y={y}, W={width}, H={height}"
    
    # Add text background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    text_thickness = 2
    
    (text_width1, text_height1), _ = cv2.getTextSize(label, font, font_scale, text_thickness)
    (text_width2, text_height2), _ = cv2.getTextSize(label2, font, font_scale, text_thickness)
    
    # Draw background for text
    text_y = y - 10 if y > 30 else y + height + 30
    cv2.rectangle(
        img_cv,
        (x, text_y - text_height1 - text_height2 - 10),
        (x + max(text_width1, text_width2) + 10, text_y + 5),
        (0, 0, 0),
        -1,
    )
    
    # Draw text
    cv2.putText(img_cv, label, (x + 5, text_y - text_height2 - 5), font, font_scale, color, text_thickness)
    cv2.putText(img_cv, label2, (x + 5, text_y), font, font_scale, color, text_thickness)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img_cv)
    
    console.print(f"[green]✓ Visualization saved: {output_path}[/green]")
    console.print(f"[dim]Coordinates: X={x_percent:.0f}%, Y={y_percent:.0f}%, W={width_percent:.0f}%, H={height_percent:.0f}%[/dim]")
    console.print(f"[dim]Pixels: X={x}, Y={y}, W={width}, H={height}[/dim]")


@click.command()
@click.option(
    "--image",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to image file",
)
@click.option(
    "--x",
    type=float,
    required=True,
    help="X coordinate as percentage (0-100)",
)
@click.option(
    "--y",
    type=float,
    required=True,
    help="Y coordinate as percentage (0-100)",
)
@click.option(
    "--width",
    type=float,
    required=True,
    help="Width as percentage (0-100)",
)
@click.option(
    "--height",
    type=float,
    required=True,
    help="Height as percentage (0-100)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output path (default: image_name_with_coords.png)",
)
def main(
    image: Path,
    x: float,
    y: float,
    width: float,
    height: float,
    output: Optional[Path],
):
    """Draw extraction coordinates on an image."""
    if not output:
        output = image.parent / f"{image.stem}_coords_{int(x)}_{int(y)}_{int(width)}_{int(height)}.png"
    
    draw_coordinates_on_image(image, output, x, y, width, height)
    console.print(f"\n[yellow]Open the file to see the green box: {output}[/yellow]")


if __name__ == "__main__":
    main()

