#!/usr/bin/env python3
"""
Extract character portraits from character card images.

This script detects and crops character portraits from card images, preparing
them for animation generation. Uses edge detection and contour analysis to
identify character boundaries.
"""

import sys
from pathlib import Path
from typing import Final, Optional, Tuple

try:
    import click
    import cv2
    import numpy as np
    from PIL import Image
    from pydantic import BaseModel, Field
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/animation/extract_character.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/animation/extract_character.py [options]\n\n"
        "Recommended: uv run ./scripts/animation/extract_character.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
DEFAULT_PADDING_PERCENT: Final[float] = 0.05  # 5% padding around character
MIN_CHARACTER_AREA_PERCENT: Final[float] = 0.1  # Character should be at least 10% of image
MAX_CHARACTER_AREA_PERCENT: Final[float] = 0.9  # Character should be at most 90% of image


class CharacterRegion(BaseModel):
    """Bounding box for character region in image."""

    x: int = Field(ge=0, description="X coordinate of top-left corner")
    y: int = Field(ge=0, description="Y coordinate of top-left corner")
    width: int = Field(gt=0, description="Width of bounding box")
    height: int = Field(gt=0, description="Height of bounding box")

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as tuple (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    @property
    def area(self) -> int:
        """Calculate area of bounding box."""
        return self.width * self.height

    def add_padding(
        self, padding_percent: float, image_width: int, image_height: int
    ) -> "CharacterRegion":
        """Add padding around the bounding box.

        Args:
            padding_percent: Percentage of width/height to add as padding
            image_width: Full image width
            image_height: Full image height

        Returns:
            New CharacterRegion with padding
        """
        pad_x = int(self.width * padding_percent)
        pad_y = int(self.height * padding_percent)

        new_x = max(0, self.x - pad_x)
        new_y = max(0, self.y - pad_y)
        new_width = min(image_width - new_x, self.width + 2 * pad_x)
        new_height = min(image_height - new_y, self.height + 2 * pad_y)

        return CharacterRegion(x=new_x, y=new_y, width=new_width, height=new_height)


class CharacterExtractor:
    """Extract character portraits from card images."""

    def __init__(
        self,
        padding_percent: float = DEFAULT_PADDING_PERCENT,
        min_area_percent: float = MIN_CHARACTER_AREA_PERCENT,
        max_area_percent: float = MAX_CHARACTER_AREA_PERCENT,
    ):
        """Initialize character extractor.

        Args:
            padding_percent: Percentage of width/height to add as padding around character
            min_area_percent: Minimum area percentage for valid character region
            max_area_percent: Maximum area percentage for valid character region
        """
        self.padding_percent = padding_percent
        self.min_area_percent = min_area_percent
        self.max_area_percent = max_area_percent

    def detect_character_region(self, image_path: Path) -> Optional[CharacterRegion]:
        """Detect character region in card image.

        Uses multiple strategies to find the character portrait:
        1. Try to find largest central region with high detail
        2. Fallback to simple center crop if detection fails

        Args:
            image_path: Path to character card image

        Returns:
            CharacterRegion if detected, None otherwise
        """
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        height, width = img.shape[:2]
        img_area = width * height

        # Strategy 1: Look for high-detail regions (character portraits have more detail than text)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Calculate local variance (detail measure)
        kernel = np.ones((9, 9), np.float32) / 81
        mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqr_mean = cv2.filter2D((gray.astype(np.float32)) ** 2, -1, kernel)
        variance = sqr_mean - mean**2

        # Threshold to find high-detail regions
        _, detail_mask = cv2.threshold(
            variance.astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Find contours in high-detail regions
        contours, _ = cv2.findContours(detail_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid_regions = []
        if contours:
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                area_percent = area / img_area

                # Filter by area
                if area_percent < self.min_area_percent or area_percent > self.max_area_percent:
                    continue

                # Filter by aspect ratio (character portraits are usually roughly square or portrait-oriented)
                aspect_ratio = w / h if h > 0 else 0
                if aspect_ratio < 0.3 or aspect_ratio > 3.0:
                    continue

                # Prefer regions closer to center
                center_x = x + w // 2
                center_y = y + h // 2
                dist_from_center = np.sqrt(
                    (center_x - width // 2) ** 2 + (center_y - height // 2) ** 2
                )
                max_dist = np.sqrt((width // 2) ** 2 + (height // 2) ** 2)
                centrality_score = 1.0 - (dist_from_center / max_dist)

                valid_regions.append(
                    (CharacterRegion(x=x, y=y, width=w, height=h), centrality_score)
                )

        # Strategy 2: If no valid regions found, use center crop heuristic
        if not valid_regions:
            # Character cards typically have portrait in upper-middle or center
            # Try center region (assuming portrait takes up middle portion)
            center_region_width = int(width * 0.6)  # 60% of width
            center_region_height = int(height * 0.7)  # 70% of height
            center_x = (width - center_region_width) // 2
            center_y = int(height * 0.1)  # Start 10% from top

            return CharacterRegion(
                x=center_x, y=center_y, width=center_region_width, height=center_region_height
            )

        # Select best region (largest area with good centrality)
        best_region, _ = max(valid_regions, key=lambda r: r[0].area * r[1])

        # Add padding
        padded_region = best_region.add_padding(self.padding_percent, width, height)

        return padded_region

    def crop_character(self, image_path: Path, region: CharacterRegion) -> Image.Image:
        """Crop character from image using bounding box.

        Args:
            image_path: Path to source image
            region: CharacterRegion defining crop area

        Returns:
            Cropped PIL Image
        """
        # Load image with PIL
        img = Image.open(image_path)

        # Crop using bounding box
        bbox = (region.x, region.y, region.x + region.width, region.y + region.height)
        cropped = img.crop(bbox)

        return cropped

    def extract_from_card(
        self, image_path: Path, output_path: Optional[Path] = None
    ) -> Tuple[Image.Image, Optional[CharacterRegion]]:
        """Extract character portrait from card image.

        Args:
            image_path: Path to character card image
            output_path: Optional path to save cropped image

        Returns:
            Tuple of (cropped_image, detected_region)
        """
        # Detect character region
        region = self.detect_character_region(image_path)
        if region is None:
            raise ValueError(f"Could not detect character region in {image_path}")

        # Crop character
        cropped = self.crop_character(image_path, region)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cropped.save(output_path)

        return cropped, region

    def preprocess_for_animation(
        self, image: Image.Image, remove_background: bool = False
    ) -> Image.Image:
        """Preprocess extracted character image for animation.

        Args:
            image: PIL Image to preprocess
            remove_background: If True, attempt to remove background (requires rembg)

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Background removal (optional)
        if remove_background:
            try:
                from rembg import remove

                # Convert PIL to numpy array
                img_array = np.array(image)
                # Remove background
                output_array = remove(img_array)
                # Convert back to PIL Image
                image = Image.fromarray(output_array)
            except ImportError:
                console.print(
                    "[yellow]Warning: rembg not installed. Skipping background removal.[/yellow]"
                )

        return image


@click.command()
@click.option(
    "--character-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Directory containing character card images (e.g., data/season1/adam)",
)
@click.option(
    "--image",
    type=click.Path(exists=True, path_type=Path),
    help="Single image file to process",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory for extracted characters (default: character_dir/animation/extracted)",
)
@click.option(
    "--padding",
    type=float,
    default=DEFAULT_PADDING_PERCENT,
    help=f"Padding percentage around character (default: {DEFAULT_PADDING_PERCENT})",
)
@click.option(
    "--remove-bg",
    is_flag=True,
    help="Remove background from extracted character (requires rembg)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing extracted images",
)
def main(
    character_dir: Optional[Path],
    image: Optional[Path],
    output_dir: Optional[Path],
    padding: float,
    remove_bg: bool,
    force: bool,
):
    """Extract character portraits from card images."""
    console.print(
        Panel.fit(
            "[bold cyan]Character Portrait Extractor[/bold cyan]\n"
            "Detects and crops character portraits from card images",
            border_style="cyan",
        )
    )

    # Determine input
    if image:
        images_to_process = [image]
        if not output_dir:
            output_dir = image.parent / "animation" / "extracted"
    elif character_dir:
        # Find front image (prefer webp, then jpg)
        front_image = None
        for ext in [".webp", ".jpg", ".jpeg", ".png"]:
            candidate = character_dir / f"front{ext}"
            if candidate.exists():
                front_image = candidate
                break

        if not front_image:
            console.print(
                f"[red]Error: No front image found in {character_dir}[/red]\n"
                "Looking for: front.webp, front.jpg, front.jpeg, or front.png"
            )
            sys.exit(1)

        images_to_process = [front_image]
        if not output_dir:
            output_dir = character_dir / "animation" / "extracted"
    else:
        console.print("[red]Error: Must provide either --character-dir or --image[/red]")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    extractor = CharacterExtractor(padding_percent=padding)

    # Process images
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting characters...", total=len(images_to_process))

        for image_path in images_to_process:
            image_name = image_path.stem
            progress.update(task, description=f"Processing {image_name}...")

            try:
                # Extract character
                cropped, region = extractor.extract_from_card(image_path)

                # Preprocess
                preprocessed = extractor.preprocess_for_animation(
                    cropped, remove_background=remove_bg
                )

                # Save outputs
                output_cropped = output_dir / f"{image_name}_cropped.jpg"
                output_preprocessed = output_dir / f"{image_name}_preprocessed.png"

                if output_cropped.exists() and not force:
                    console.print(f"[yellow]Skipping {image_name} (already exists)[/yellow]")
                else:
                    cropped.save(output_cropped, quality=95)
                    preprocessed.save(output_preprocessed)

                    console.print(
                        f"[green]✓ Extracted {image_name}[/green]\n"
                        f"  Region: x={region.x}, y={region.y}, "
                        f"w={region.width}, h={region.height}\n"
                        f"  Saved: {output_cropped.name}, {output_preprocessed.name}"
                    )

            except ValueError as e:
                console.print(f"[red]Error processing {image_name}: {e}[/red]")
            except Exception as e:
                console.print(f"[red]Unexpected error processing {image_name}: {e}[/red]")

            progress.update(task, advance=1)

    console.print("\n[green]✓ Extraction complete![/green]")
    console.print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
