#!/usr/bin/env python3
"""
Convert JPEG images to WebP format for a specific directory/season.
Preserves original JPEG files.
"""

import sys
from pathlib import Path
from typing import Final, List

try:
    from PIL import Image
    import click
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/convert_to_webp.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/convert_to_webp.py [options]\n\n"
        "Recommended: uv run ./scripts/convert_to_webp.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
WEBP_QUALITY: Final[int] = 85
WEBP_EXTENSION: Final[str] = ".webp"
JPEG_EXTENSIONS: Final[tuple] = (".jpg", ".jpeg")
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
            webp_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(webp_path, "WEBP", quality=quality, method=6)  # method=6 is slowest but best compression
            return True
    except Exception as e:
        console.print(f"[red]Error converting {jpeg_path}:[/red] {e}")
        return False


def find_jpeg_images(directory: Path) -> List[Path]:
    """Find all JPEG images in directory and subdirectories."""
    jpegs: List[Path] = []
    for ext in JPEG_EXTENSIONS:
        jpegs.extend(directory.rglob(f"*{ext}"))
    return sorted(jpegs)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data",
    help="Base data directory (default: data)",
)
@click.option(
    "--season",
    type=str,
    required=True,
    help="Season/box directory name (e.g., 'season1', 'season2', 'unknowable-box')",
)
@click.option(
    "--quality",
    type=int,
    default=WEBP_QUALITY,
    help=f"WebP quality (0-100, default: {WEBP_QUALITY})",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be converted without actually converting",
)
def main(data_dir: Path, season: str, quality: int, dry_run: bool):
    """Convert JPEG images to WebP format for a specific season/box."""
    season_path = data_dir / season

    if not season_path.exists():
        console.print(f"[red]Error: Directory not found: {season_path}[/red]")
        sys.exit(1)

    if not season_path.is_dir():
        console.print(f"[red]Error: Not a directory: {season_path}[/red]")
        sys.exit(1)

    console.print(f"[cyan]Scanning:[/cyan] {season_path}")

    # Find all JPEG images
    jpeg_images = find_jpeg_images(season_path)

    if not jpeg_images:
        console.print(f"[yellow]No JPEG images found in {season_path}[/yellow]")
        return

    # Filter out images that already have WebP versions
    images_to_convert: List[Path] = []
    already_converted: List[Path] = []

    for jpeg_path in jpeg_images:
        webp_path = jpeg_path.with_suffix(WEBP_EXTENSION)
        if webp_path.exists():
            already_converted.append(jpeg_path)
        else:
            images_to_convert.append(jpeg_path)

    if not images_to_convert and not already_converted:
        console.print(f"[yellow]No images to convert[/yellow]")
        return

    # Show summary
    console.print(f"\n[cyan]Found {len(jpeg_images)} JPEG image(s)[/cyan]")
    if already_converted:
        console.print(f"[yellow]{len(already_converted)} already have WebP versions[/yellow]")
    if images_to_convert:
        console.print(f"[green]{len(images_to_convert)} to convert[/green]")

    if dry_run:
        console.print("\n[bold yellow]DRY RUN - No files will be converted[/bold yellow]\n")
        for img_path in images_to_convert:
            webp_path = img_path.with_suffix(WEBP_EXTENSION)
            console.print(f"Would convert: {img_path.relative_to(data_dir)} → {webp_path.name}")
        return

    if not images_to_convert:
        console.print("[green]All images already converted![/green]")
        return

    # Convert images
    total_original_size = 0
    total_webp_size = 0
    converted = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Converting images...", total=len(images_to_convert))

        for jpeg_path in images_to_convert:
            webp_path = jpeg_path.with_suffix(WEBP_EXTENSION)
            original_size = jpeg_path.stat().st_size
            total_original_size += original_size

            if convert_jpeg_to_webp(jpeg_path, webp_path, quality):
                webp_size = webp_path.stat().st_size
                total_webp_size += webp_size
                converted += 1
                progress.update(task, advance=1)
            else:
                failed += 1
                progress.update(task, advance=1)

    # Summary
    console.print("\n[bold green]Conversion Summary[/bold green]")
    table = Table(title=f"Results for {season}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Images converted", str(converted))
    if failed > 0:
        table.add_row("Failed", str(failed), style="red")
    table.add_row("Original total size", format_file_size(total_original_size))
    table.add_row("WebP total size", format_file_size(total_webp_size))
    if total_original_size > 0:
        reduction = ((total_original_size - total_webp_size) / total_original_size) * 100
        table.add_row("Size reduction", f"{reduction:.1f}%", style="yellow")

    console.print("\n")
    console.print(table)

    console.print(f"\n[green]✓ WebP files saved in:[/green] {season_path}")
    console.print("[bold yellow]Note:[/bold yellow] Original JPEG files preserved.")


if __name__ == "__main__":
    main()

