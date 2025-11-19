#!/usr/bin/env python3
"""
Demonstration script to convert JPEG images to WebP format.
Shows file size comparison and quality before committing to the change.
"""

import sys
from pathlib import Path
from typing import Final

try:
    from PIL import Image
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/convert_to_webp_demo.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/convert_to_webp_demo.py [options]\n\n"
        "Recommended: uv run ./scripts/convert_to_webp_demo.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

import click

console = Console()

# Constants
WEBP_QUALITY: Final[int] = 85  # Good balance between quality and size
WEBP_EXTENSION: Final[str] = ".webp"
JPEG_EXTENSION: Final[str] = ".jpg"
PNG_EXTENSION: Final[str] = ".png"
FILENAME_FRONT: Final[str] = "front.jpg"
FILENAME_BACK: Final[str] = "back.jpg"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def convert_jpeg_to_webp(jpeg_path: Path, webp_path: Path, quality: int = WEBP_QUALITY) -> bool:
    """Convert JPEG image to WebP format."""
    try:
        with Image.open(jpeg_path) as img:
            # Convert to RGB if necessary (WebP doesn't support all modes)
            if img.mode in ("RGBA", "LA", "P"):
                # Convert RGBA/LA to RGB
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Save as WebP
            img.save(webp_path, "WEBP", quality=quality, method=6)  # method=6 is slowest but best compression
            return True
    except Exception as e:
        console.print(f"[red]Error converting {jpeg_path}:[/red] {e}")
        return False


def convert_webp_to_png_grayscale(webp_path: Path, png_path: Path) -> bool:
    """Convert WebP image to PNG grayscale for OCR processing."""
    try:
        with Image.open(webp_path) as img:
            # Convert to grayscale
            gray_img = img.convert("L")
            # Save as PNG
            gray_img.save(png_path, "PNG")
            return True
    except Exception as e:
        console.print(f"[red]Error converting {webp_path} to PNG grayscale:[/red] {e}")
        return False


@click.command()
@click.option(
    "--image-path",
    type=click.Path(exists=True, path_type=Path),
    default="data/season1/adam/front.jpg",
    help="Path to JPEG image to convert (default: data/season1/adam/front.jpg)",
)
@click.option(
    "--quality",
    type=int,
    default=WEBP_QUALITY,
    help=f"WebP quality (0-100, default: {WEBP_QUALITY})",
)
@click.option(
    "--show-png",
    is_flag=True,
    help="Also convert to PNG grayscale to show OCR format",
)
def main(image_path: Path, quality: int, show_png: bool):
    """Convert a sample JPEG image to WebP and show file size comparison."""
    console.print(Panel.fit("[bold cyan]WebP Conversion Demo[/bold cyan]"))

    if not image_path.exists():
        console.print(f"[red]Error: Image not found: {image_path}[/red]")
        sys.exit(1)

    if not image_path.suffix.lower() in (".jpg", ".jpeg"):
        console.print(f"[yellow]Warning: Expected JPEG file, got: {image_path.suffix}[/yellow]")

    # Create output paths
    webp_path = image_path.with_suffix(WEBP_EXTENSION)
    png_path = image_path.with_suffix(PNG_EXTENSION) if show_png else None

    # Get original file size
    original_size = image_path.stat().st_size

    console.print(f"\n[cyan]Converting:[/cyan] {image_path.name}")
    console.print(f"[cyan]Original size:[/cyan] {format_file_size(original_size)}")

    # Convert to WebP
    console.print(f"\n[green]Converting to WebP...[/green]")
    if convert_jpeg_to_webp(image_path, webp_path, quality):
        webp_size = webp_path.stat().st_size
        reduction = ((original_size - webp_size) / original_size) * 100

        # Create comparison table
        table = Table(title="File Size Comparison")
        table.add_column("Format", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Reduction", style="yellow")

        table.add_row("JPEG (Original)", format_file_size(original_size), "-")
        table.add_row(
            "WebP",
            format_file_size(webp_size),
            f"{reduction:.1f}% smaller",
        )

        console.print("\n")
        console.print(table)

        console.print(f"\n[green]✓ WebP saved to:[/green] {webp_path}")
        console.print(f"[green]✓ File size reduction:[/green] {reduction:.1f}%")

        # Show quality info
        with Image.open(image_path) as orig_img:
            with Image.open(webp_path) as webp_img:
                console.print(f"\n[cyan]Image dimensions:[/cyan] {orig_img.size[0]}x{orig_img.size[1]}")
                console.print(f"[cyan]Original mode:[/cyan] {orig_img.mode}")
                console.print(f"[cyan]WebP mode:[/cyan] {webp_img.mode}")

        # Convert to PNG grayscale if requested
        if show_png and png_path:
            console.print(f"\n[green]Converting WebP to PNG grayscale for OCR...[/green]")
            if convert_webp_to_png_grayscale(webp_path, png_path):
                png_size = png_path.stat().st_size
                console.print(f"[green]✓ PNG grayscale saved to:[/green] {png_path}")
                console.print(f"[cyan]PNG grayscale size:[/cyan] {format_file_size(png_size)}")

                # Add PNG to table
                table.add_row(
                    "PNG Grayscale (OCR)",
                    format_file_size(png_size),
                    f"{((png_size - original_size) / original_size) * 100:.1f}% larger",
                )
                console.print("\n")
                console.print(table)

        console.print("\n[bold yellow]Note:[/bold yellow] Original JPEG file preserved.")
        console.print("[bold yellow]Note:[/bold yellow] WebP file created for comparison.")
        if show_png and png_path:
            console.print("[bold yellow]Note:[/bold yellow] PNG grayscale created for OCR demo.")

    else:
        console.print("[red]✗ Conversion failed[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

