#!/usr/bin/env python3
"""
Preprocess character card images for better OCR accuracy.

This script converts images to optimized formats and applies preprocessing
to improve OCR text extraction quality.
"""

import sys
from pathlib import Path
from typing import Final, Optional

try:
    import click
    import cv2
    import numpy as np
    from PIL import Image
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/preprocess_images_for_ocr.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/preprocess_images_for_ocr.py [options]\n\n"
        "Recommended: uv run ./scripts/preprocess_images_for_ocr.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.constants import Filename

console = Console()

# Constants
DATA_DIR: Final[str] = "data"
OCR_PREPROCESSED_SUFFIX: Final[str] = "_ocr_preprocessed"


def convert_to_optimized_format(
    image_path: Path, output_path: Optional[Path] = None, format: str = "PNG"
) -> Path:
    """Convert image to optimized format for OCR.

    Args:
        image_path: Input image path
        output_path: Output path (if None, creates _ocr_preprocessed version)
        format: Output format ("PNG", "TIFF", etc.)

    Returns:
        Path to converted image
    """
    if output_path is None:
        # Create output path with suffix
        output_path = (
            image_path.parent / f"{image_path.stem}{OCR_PREPROCESSED_SUFFIX}.{format.lower()}"
        )

    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Convert to grayscale for OCR (better accuracy)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply enhanced preprocessing - softer approach for better OCR
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # Use moderate settings to preserve detail
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Apply light denoising (less aggressive)
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    # Use OTSU thresholding instead of adaptive - better for OCR
    # This creates a binary image but preserves more detail
    _, processed = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save as PNG (lossless, good for OCR)
    cv2.imwrite(str(output_path), processed)

    return output_path


def preprocess_character_images(
    char_dir: Path, force: bool = False, format: str = "PNG"
) -> tuple[int, int]:
    """Preprocess all images for a character.

    Args:
        char_dir: Character directory
        force: If True, overwrite existing preprocessed images
        format: Output format

    Returns:
        Tuple of (processed_count, skipped_count)
    """
    processed = 0
    skipped = 0

    # Find back card images (prefer WebP, then JPG)
    back_path = None
    for ext in [".webp", ".jpg", ".jpeg"]:
        candidate = char_dir / f"back{ext}"
        if candidate.exists():
            back_path = candidate
            break

    if not back_path:
        return 0, 0

    # Create preprocessed version
    output_path = char_dir / f"back{OCR_PREPROCESSED_SUFFIX}.{format.lower()}"

    if output_path.exists() and not force:
        skipped += 1
        return 0, 1

    try:
        convert_to_optimized_format(back_path, output_path, format)
        processed += 1
    except Exception as e:
        console.print(f"[yellow]Warning: Could not preprocess {char_dir.name}: {e}[/yellow]")
        return 0, 0

    return processed, skipped


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help=f"Data directory (default: {DATA_DIR})",
)
@click.option(
    "--character",
    type=str,
    help="Specific character name to preprocess (e.g., 'adam')",
)
@click.option(
    "--season",
    type=str,
    help="Specific season to process (e.g., 'season1')",
)
@click.option(
    "--format",
    type=click.Choice(["PNG", "TIFF", "JPEG"], case_sensitive=False),
    default="PNG",
    help="Output format (default: PNG)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reprocessing even if preprocessed images exist",
)
def main(
    data_dir: Path,
    character: Optional[str],
    season: Optional[str],
    format: str,
    force: bool,
):
    """Preprocess character card images for better OCR accuracy."""
    console.print("[bold cyan]Preprocessing Images for OCR[/bold cyan]\n")

    # Find characters to process
    characters_to_process: list[Path] = []

    if character and season:
        char_path = data_dir / season / character
        if char_path.exists():
            characters_to_process = [char_path]
        else:
            console.print(f"[red]Error: Character directory not found: {char_path}[/red]")
            sys.exit(1)
    elif season:
        season_dir = data_dir / season
        if season_dir.exists():
            characters_to_process = [
                d for d in season_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
            ]
        else:
            console.print(f"[red]Error: Season directory not found: {season_dir}[/red]")
            sys.exit(1)
    else:
        # Process all characters
        for season_dir in data_dir.iterdir():
            if season_dir.is_dir() and not season_dir.name.startswith("."):
                characters_to_process.extend(
                    [d for d in season_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
                )

    if not characters_to_process:
        console.print("[yellow]No characters found to process[/yellow]")
        return

    console.print(f"[green]Found {len(characters_to_process)} characters to process[/green]\n")

    # Process characters
    processed_count = 0
    skipped_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing images...", total=len(characters_to_process))

        for char_dir in characters_to_process:
            char_name = char_dir.name
            progress.update(task, description=f"Processing {char_name}...")

            processed, skipped = preprocess_character_images(char_dir, force, format)

            if processed > 0:
                processed_count += processed
                console.print(f"[green]Preprocessed {char_name}[/green]")
            elif skipped > 0:
                skipped_count += skipped

            progress.update(task, advance=1)

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Processed: {processed_count}")
    console.print(f"  Skipped: {skipped_count}")
    console.print(f"  Total: {len(characters_to_process)}")

    if processed_count > 0:
        console.print(f"\n[green]✓ Created preprocessed images (format: {format})[/green]")
        console.print(
            "[cyan]Tip: Use these preprocessed images for OCR by updating scripts to use *_ocr_preprocessed.* files[/cyan]"
        )


if __name__ == "__main__":
    main()
