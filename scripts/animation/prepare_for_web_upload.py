#!/usr/bin/env python3
"""
Prepare character image for web-based animation tools.

This script extracts the character from the card and prepares it
for upload to web-based animation services.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    from PIL import Image
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install click pillow rich\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()


def extract_character_for_upload(
    image_path: Path,
    coordinates: str,
    output_path: Path,
    size_limit: Optional[tuple[int, int]] = None,
) -> bool:
    """Extract character and prepare for web upload.
    
    Args:
        image_path: Path to source image
        coordinates: Coordinates as 'x,y,width,height' percentages
        output_path: Path to save extracted character
        size_limit: Optional max size (width, height) for web upload
        
    Returns:
        True if successful
    """
    try:
        # Import helper function
        create_gif_module_path = Path(__file__).parent / "create_gif.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("create_gif", create_gif_module_path)
        create_gif_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(create_gif_module)
        extract_character_with_coordinates = create_gif_module.extract_character_with_coordinates
        
        # Parse coordinates
        parts = [x.strip() for x in coordinates.split(",")]
        if len(parts) != 4:
            raise ValueError("Need 4 values: x,y,width,height")
        
        if any("%" in p for p in parts):
            coords_percent = tuple(float(p.replace("%", "")) / 100.0 for p in parts)
            coords = None
        else:
            coords = tuple(int(p) for p in parts)
            coords_percent = None
        
        console.print(f"[cyan]Extracting character...[/cyan]")
        character_image, _ = extract_character_with_coordinates(image_path, coords, coords_percent)
        
        # Resize if size limit provided
        if size_limit:
            max_width, max_height = size_limit
            if character_image.width > max_width or character_image.height > max_height:
                console.print(f"[cyan]Resizing to fit {max_width}x{max_height} limit...[/cyan]")
                character_image.thumbnail(size_limit, Image.Resampling.LANCZOS)
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        character_image.save(output_path, "PNG")
        
        console.print(f"[green]✓ Character extracted: {output_path}[/green]")
        console.print(f"[dim]Size: {character_image.width}x{character_image.height} pixels[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


@click.command()
@click.option(
    "--season",
    required=True,
    help="Season name (e.g., 'season1')",
)
@click.option(
    "--character",
    required=True,
    help="Character name (e.g., 'rasputin')",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=Path("data"),
    help="Root data directory",
)
@click.option(
    "--image-type",
    type=click.Choice(["front", "back", "auto"]),
    default="auto",
    help="Which card image to use (auto = prefer front, fallback to back)",
)
@click.option(
    "--coordinates",
    type=str,
    help="Character extraction coordinates as 'x,y,width,height' percentages (e.g., '15%,17%,28%,58%'). If not provided, will prompt or use defaults.",
)
@click.option(
    "--front-coordinates",
    type=str,
    help="Coordinates for front card (if different from back). Format: 'x,y,width,height' percentages",
)
@click.option(
    "--back-coordinates",
    type=str,
    help="Coordinates for back card (if different from front). Format: 'x,y,width,height' percentages",
)
@click.option(
    "--max-size",
    type=str,
    help="Maximum size for web upload as 'width,height' (e.g., '1024,1024')",
)
@click.option(
    "--output-name",
    type=str,
    help="Output filename (default: character_web_ready.png)",
)
def main(
    season: str,
    character: str,
    data_dir: Path,
    image_type: str,
    coordinates: Optional[str],
    front_coordinates: Optional[str],
    back_coordinates: Optional[str],
    max_size: Optional[str],
    output_name: Optional[str],
):
    """Extract character image and prepare for web-based animation tools."""
    console.print(
        Panel.fit(
            "[bold cyan]Character Image Preparer[/bold cyan]\n"
            "Extracts character for upload to web animation tools",
            border_style="cyan",
        )
    )
    
    # Find character directory
    char_dir = data_dir / season / character.lower()
    if not char_dir.exists():
        console.print(f"[red]Error: Character directory not found: {char_dir}[/red]")
        sys.exit(1)
    
    # Find image file
    image_path = None
    
    if image_type == "auto":
        # Try front first, then back
        console.print("[cyan]Auto-detecting best image (preferring front card)...[/cyan]")
        for card_type in ["front", "back"]:
            for ext in [".webp", ".jpg", ".jpeg", ".png"]:
                candidate = char_dir / f"{card_type}{ext}"
                if candidate.exists():
                    image_path = candidate
                    console.print(f"[green]Found {card_type} card: {candidate.name}[/green]")
                    break
            if image_path:
                break
    else:
        # Use specified image type
        for ext in [".webp", ".jpg", ".jpeg", ".png"]:
            candidate = char_dir / f"{image_type}{ext}"
            if candidate.exists():
                image_path = candidate
                break
    
    if not image_path:
        if image_type == "auto":
            console.print(f"[red]Error: No front or back image found in {char_dir}[/red]")
        else:
            console.print(f"[red]Error: No {image_type} image found in {char_dir}[/red]")
        sys.exit(1)
    
    # Determine which coordinates to use
    detected_card_type = image_path.stem.split(".")[0]  # "front" or "back"
    
    if coordinates:
        # Use provided coordinates
        coords_to_use = coordinates
    elif front_coordinates and detected_card_type == "front":
        coords_to_use = front_coordinates
    elif back_coordinates and detected_card_type == "back":
        coords_to_use = back_coordinates
    elif front_coordinates or back_coordinates:
        # Use the appropriate one based on detected card type
        coords_to_use = front_coordinates if detected_card_type == "front" else back_coordinates
    else:
        console.print(f"[red]Error: No coordinates provided for {detected_card_type} card[/red]")
        console.print("[yellow]Please provide --coordinates or --front-coordinates/--back-coordinates[/yellow]")
        sys.exit(1)
    
    console.print(f"[cyan]Using coordinates for {detected_card_type} card: {coords_to_use}[/cyan]")
    
    # Parse max size if provided
    size_limit = None
    if max_size:
        try:
            parts = max_size.split(",")
            size_limit = (int(parts[0]), int(parts[1]))
        except ValueError:
            console.print(f"[yellow]Warning: Invalid max-size format, ignoring[/yellow]")
    
    # Determine output path
    output_dir = char_dir / "animation"
    if not output_name:
        output_name = f"{character}_web_ready.png"
    output_path = output_dir / output_name
    
    # Extract character
    success = extract_character_for_upload(
        image_path,
        coords_to_use,
        output_path,
        size_limit=size_limit,
    )
    
    if not success:
        sys.exit(1)
    
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Go to a web animation tool (e.g., insmind.com/ai-walking-video-generator)")
    console.print(f"2. Upload: {output_path}")
    console.print("3. Download the generated animation")
    console.print("4. Convert to GIF if needed")


if __name__ == "__main__":
    main()

