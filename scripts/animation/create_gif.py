#!/usr/bin/env python3
"""
Create animated GIF from character card images.

This script extracts character portraits and creates animated GIFs with
various effects (parallax, breathing, rotation, etc.).
"""

import sys
from pathlib import Path
from typing import Final, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run python scripts/animation/create_gif.py [options]\n"
        "  2. source .venv/bin/activate && python scripts/animation/create_gif.py [options]\n\n"
        "Recommended: uv run python scripts/animation/create_gif.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from scripts.animation.extract_character import CharacterExtractor, CharacterRegion
except ImportError:
    # Fallback if extract_character is not available
    CharacterExtractor = None
    CharacterRegion = None

console = Console()

# Constants
DEFAULT_FPS: Final[int] = 10
DEFAULT_DURATION: Final[float] = 2.0  # seconds
DEFAULT_LOOP: Final[int] = 0  # 0 = infinite loop
DEFAULT_EFFECT: Final[str] = "breathing"  # breathing, parallax, zoom, rotate


def extract_character_with_coordinates(
    image_path: Path,
    coordinates: Optional[Tuple[int, int, int, int]] = None,
    coordinates_percent: Optional[Tuple[float, float, float, float]] = None,
) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Extract character from image using coordinates or auto-detection.
    
    Args:
        image_path: Path to character card image
        coordinates: Optional tuple (x, y, width, height) in pixels
        coordinates_percent: Optional tuple (x%, y%, width%, height%) as percentages
        
    Returns:
        Tuple of (extracted character image, bbox in pixels as (x, y, width, height))
    """
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    if coordinates_percent:
        # Convert percentages to pixels
        x_pct, y_pct, width_pct, height_pct = coordinates_percent
        x = int(img_width * x_pct)
        y = int(img_height * y_pct)
        width = int(img_width * width_pct)
        height = int(img_height * height_pct)
        bbox = (x, y, x + width, y + height)
        return img.crop(bbox), (x, y, width, height)
    elif coordinates:
        # Manual extraction using provided pixel coordinates
        x, y, width, height = coordinates
        bbox = (x, y, x + width, y + height)
        return img.crop(bbox), (x, y, width, height)
    elif CharacterExtractor:
        # Auto-detection
        extractor = CharacterExtractor()
        cropped, region = extractor.extract_from_card(image_path)
        return cropped, (region.x, region.y, region.width, region.height)
    else:
        # Fallback: use center crop if extraction not available
        # Crop center 60% of image
        crop_width = int(img_width * 0.6)
        crop_height = int(img_height * 0.7)
        x = (img_width - crop_width) // 2
        y = int(img_height * 0.1)  # Start 10% from top
        bbox = (x, y, x + crop_width, y + crop_height)
        return img.crop(bbox), (x, y, crop_width, crop_height)


def visualize_extraction_region(
    image_path: Path,
    bbox: Tuple[int, int, int, int],
    output_path: Path,
    coordinates_percent: Optional[Tuple[float, float, float, float]] = None,
) -> None:
    """Draw extraction region box on image and save visualization.
    
    Args:
        image_path: Path to source image
        bbox: Bounding box (x, y, width, height) in pixels
        output_path: Path to save visualization
        coordinates_percent: Optional percentage coordinates for label
    """
    # Load image with OpenCV for drawing
    img_cv = cv2.imread(str(image_path))
    if img_cv is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    h, w = img_cv.shape[:2]
    x, y, width, height = bbox
    
    # Draw rectangle with thicker border for visibility
    color = (0, 255, 0)  # Green (BGR format)
    thickness = 4
    cv2.rectangle(img_cv, (x, y), (x + width, y + height), color, thickness)
    
    # Draw corner markers for better visibility
    corner_size = 20
    # Top-left corner
    cv2.line(img_cv, (x, y), (x + corner_size, y), color, thickness)
    cv2.line(img_cv, (x, y), (x, y + corner_size), color, thickness)
    # Top-right corner
    cv2.line(img_cv, (x + width, y), (x + width - corner_size, y), color, thickness)
    cv2.line(img_cv, (x + width, y), (x + width, y + corner_size), color, thickness)
    # Bottom-left corner
    cv2.line(img_cv, (x, y + height), (x + corner_size, y + height), color, thickness)
    cv2.line(img_cv, (x, y + height), (x, y + height - corner_size), color, thickness)
    # Bottom-right corner
    cv2.line(img_cv, (x + width, y + height), (x + width - corner_size, y + height), color, thickness)
    cv2.line(img_cv, (x + width, y + height), (x + width, y + height - corner_size), color, thickness)
    
    # Add label with coordinates
    if coordinates_percent:
        x_pct, y_pct, w_pct, h_pct = coordinates_percent
        label = f"Character Region: X={x_pct*100:.0f}%, Y={y_pct*100:.0f}%, W={w_pct*100:.0f}%, H={h_pct*100:.0f}%"
        label2 = f"Pixels: X={x}, Y={y}, W={width}, H={height}"
    else:
        label = f"Character Region: X={x}, Y={y}, W={width}, H={height}"
        label2 = None
    
    # Draw label background and text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.9
    font_thickness = 2
    
    # Calculate text size
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
    
    # Position label above the box (or below if not enough space)
    if y > text_height + 20:
        label_y = y - 15
    else:
        label_y = y + height + text_height + 20
    
    label_x = x
    
    # Draw background rectangle for text (black with some transparency effect)
    padding = 5
    cv2.rectangle(
        img_cv,
        (label_x - padding, label_y - text_height - padding),
        (label_x + text_width + padding, label_y + baseline + padding),
        (0, 0, 0),
        -1,
    )
    
    # Draw main label text
    cv2.putText(
        img_cv,
        label,
        (label_x, label_y),
        font,
        font_scale,
        (0, 255, 0),  # Green text
        font_thickness,
        cv2.LINE_AA,
    )
    
    # Draw second line if we have percentage coordinates
    if label2:
        (text_width2, text_height2), baseline2 = cv2.getTextSize(label2, font, font_scale * 0.8, font_thickness)
        label_y2 = label_y + text_height + 10
        cv2.rectangle(
            img_cv,
            (label_x - padding, label_y2 - text_height2 - padding),
            (label_x + text_width2 + padding, label_y2 + baseline2 + padding),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            img_cv,
            label2,
            (label_x, label_y2),
            font,
            font_scale * 0.8,
            (200, 200, 200),  # Light gray text
            font_thickness - 1,
            cv2.LINE_AA,
        )
    
    # Save visualization
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img_cv)


def create_breathing_animation(
    image: Image.Image, num_frames: int, scale_range: Tuple[float, float] = (0.95, 1.05)
) -> list[Image.Image]:
    """Create breathing animation effect (subtle zoom in/out).
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        scale_range: Min and max scale factors
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    min_scale, max_scale = scale_range
    
    for i in range(num_frames):
        # Create sine wave for smooth breathing effect
        progress = i / num_frames
        scale = min_scale + (max_scale - min_scale) * (0.5 + 0.5 * np.sin(progress * 2 * np.pi))
        
        # Calculate new size
        width, height = image.size
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create new image with original size and paste resized image centered
        frame = Image.new("RGBA" if image.mode == "RGBA" else "RGB", (width, height), (0, 0, 0, 0))
        paste_x = (width - new_width) // 2
        paste_y = (height - new_height) // 2
        frame.paste(resized, (paste_x, paste_y))
        
        frames.append(frame)
    
    return frames


def create_parallax_animation(
    image: Image.Image, num_frames: int, shift_range: Tuple[int, int] = (-10, 10)
) -> list[Image.Image]:
    """Create parallax animation effect (subtle horizontal shift).
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        shift_range: Min and max horizontal shift in pixels
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    min_shift, max_shift = shift_range
    
    for i in range(num_frames):
        # Create sine wave for smooth parallax effect
        progress = i / num_frames
        shift = int(min_shift + (max_shift - min_shift) * (0.5 + 0.5 * np.sin(progress * 2 * np.pi)))
        
        # Create new image
        width, height = image.size
        frame = Image.new("RGBA" if image.mode == "RGBA" else "RGB", (width, height), (0, 0, 0, 0))
        
        # Paste image with shift
        paste_x = shift
        frame.paste(image, (paste_x, 0))
        
        frames.append(frame)
    
    return frames


def create_zoom_animation(
    image: Image.Image, num_frames: int, zoom_range: Tuple[float, float] = (1.0, 1.1)
) -> list[Image.Image]:
    """Create zoom animation effect.
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        zoom_range: Min and max zoom factors
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    min_zoom, max_zoom = zoom_range
    
    for i in range(num_frames):
        # Create smooth zoom effect
        progress = i / num_frames
        zoom = min_zoom + (max_zoom - min_zoom) * progress
        
        # Calculate new size
        width, height = image.size
        new_width = int(width * zoom)
        new_height = int(height * zoom)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create new image with original size and paste resized image centered
        frame = Image.new("RGBA" if image.mode == "RGBA" else "RGB", (width, height), (0, 0, 0, 0))
        paste_x = (width - new_width) // 2
        paste_y = (height - new_height) // 2
        frame.paste(resized, (paste_x, paste_y))
        
        frames.append(frame)
    
    return frames


def create_rotate_animation(
    image: Image.Image, num_frames: int, rotation_range: Tuple[float, float] = (-5, 5)
) -> list[Image.Image]:
    """Create rotation animation effect (subtle rotation).
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        rotation_range: Min and max rotation angles in degrees
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    min_rot, max_rot = rotation_range
    
    for i in range(num_frames):
        # Create sine wave for smooth rotation
        progress = i / num_frames
        angle = min_rot + (max_rot - min_rot) * (0.5 + 0.5 * np.sin(progress * 2 * np.pi))
        
        # Rotate image
        rotated = image.rotate(angle, expand=False, resample=Image.Resampling.BILINEAR)
        
        frames.append(rotated)
    
    return frames


def create_horizontal_move_animation(
    image: Image.Image, num_frames: int, move_range: Tuple[int, int] = (-50, 50)
) -> list[Image.Image]:
    """Create horizontal movement animation (character moves left to right).
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        move_range: Min and max horizontal movement in pixels (negative = left, positive = right)
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    min_move, max_move = move_range
    width, height = image.size
    
    for i in range(num_frames):
        # Create smooth left-to-right movement using sine wave
        progress = i / num_frames
        # Sine wave goes from -1 to 1, so movement goes from min_move to max_move
        move_x = int(min_move + (max_move - min_move) * (0.5 + 0.5 * np.sin(progress * 2 * np.pi)))
        
        # Create new image with extra width to accommodate movement
        extra_width = max(abs(min_move), abs(max_move))
        frame_width = width + 2 * extra_width
        frame = Image.new("RGBA" if image.mode == "RGBA" else "RGB", (frame_width, height), (0, 0, 0, 0))
        
        # Paste character at calculated position (centered + movement offset)
        paste_x = extra_width + move_x
        frame.paste(image, (paste_x, 0))
        
        # Crop to original size (centered on character)
        crop_x = extra_width
        bbox = (crop_x, 0, crop_x + width, height)
        frame = frame.crop(bbox)
        
        frames.append(frame)
    
    return frames


def create_3d_turn_animation(
    image: Image.Image, num_frames: int, turn_angle: float = 30.0
) -> list[Image.Image]:
    """Create 3D-like turn animation (character appears to rotate left/right).
    
    Uses perspective transformation to simulate 3D rotation effect.
    
    Args:
        image: Base character image
        num_frames: Number of frames in animation
        turn_angle: Maximum turn angle in degrees (e.g., 30 = 30° left and right)
        
    Returns:
        List of PIL Images for animation frames
    """
    frames = []
    width, height = image.size
    
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    if image.mode == "RGBA":
        # Handle alpha channel
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
    else:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    for i in range(num_frames):
        # Create smooth turn: -30° to +30° and back
        progress = i / num_frames
        # Use sine wave: goes from -1 to +1, so angle goes from -turn_angle to +turn_angle
        angle_rad = np.sin(progress * 2 * np.pi) * np.radians(turn_angle)
        
        # Calculate perspective transform points
        # Original corners (in order: top-left, top-right, bottom-right, bottom-left)
        src_points = np.float32([
            [0, 0],           # top-left
            [width, 0],       # top-right
            [width, height],  # bottom-right
            [0, height]       # bottom-left
        ])
        
        # Calculate perspective distortion based on angle
        # For a 3D turn effect, we want to:
        # - Shift top corners horizontally based on angle
        # - Keep bottom corners more stable (like rotating around bottom)
        # - Scale width based on perspective
        
        # Perspective factor: how much the top shifts relative to bottom
        perspective_factor = np.sin(angle_rad) * 0.3  # 30% max shift
        scale_factor = np.cos(angle_rad)  # Scale based on rotation
        
        # Calculate destination points
        # Top corners shift horizontally, bottom stays more stable
        shift_x = perspective_factor * width
        
        dst_points = np.float32([
            [shift_x, 0],                                    # top-left shifts
            [width - shift_x, 0],                           # top-right shifts opposite
            [width * scale_factor + (width * (1 - scale_factor)) / 2, height],  # bottom-right
            [width * (1 - scale_factor) / 2, height]        # bottom-left
        ])
        
        # Get perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Apply perspective transform
        if image.mode == "RGBA":
            # Handle alpha channel
            transformed = cv2.warpPerspective(img_cv, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
            # Convert back to PIL
            frame = Image.fromarray(cv2.cvtColor(transformed, cv2.COLOR_BGRA2RGBA))
        else:
            transformed = cv2.warpPerspective(img_cv, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            # Convert back to PIL
            frame = Image.fromarray(cv2.cvtColor(transformed, cv2.COLOR_BGR2RGB))
        
        frames.append(frame)
    
    return frames


def create_gif_from_frames(
    frames: list[Image.Image],
    output_path: Path,
    duration: float = DEFAULT_DURATION,
    loop: int = DEFAULT_LOOP,
) -> None:
    """Create animated GIF from list of frames.
    
    Args:
        frames: List of PIL Images
        output_path: Path to save GIF
        duration: Duration of animation in seconds
        loop: Number of loops (0 = infinite)
    """
    if not frames:
        raise ValueError("No frames provided")
    
    # Calculate frame duration in milliseconds
    frame_duration_ms = int((duration / len(frames)) * 1000)
    
    # Save as GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=loop,
        optimize=True,
    )


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
    type=click.Choice(["front", "back"]),
    default="front",
    help="Which card image to use (front or back)",
)
@click.option(
    "--coordinates",
    type=str,
    help="Manual coordinates as 'x,y,width,height' (e.g., '100,50,300,400')",
)
@click.option(
    "--effect",
    type=click.Choice(["breathing", "parallax", "zoom", "rotate", "turn_3d", "move_horizontal"]),
    default=DEFAULT_EFFECT,
    help="Animation effect type (turn_3d = 3D rotation, move_horizontal = left-right movement)",
)
@click.option(
    "--move-distance",
    type=int,
    default=50,
    help="Maximum horizontal movement distance in pixels for move_horizontal effect (default: 50)",
)
@click.option(
    "--turn-angle",
    type=float,
    default=30.0,
    help="Maximum turn angle in degrees for turn_3d effect (default: 30)",
)
@click.option(
    "--fps",
    type=int,
    default=DEFAULT_FPS,
    help=f"Frames per second (default: {DEFAULT_FPS})",
)
@click.option(
    "--duration",
    type=float,
    default=DEFAULT_DURATION,
    help=f"Animation duration in seconds (default: {DEFAULT_DURATION})",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory (default: character_dir/animation)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing GIF",
)
@click.option(
    "--visualize",
    is_flag=True,
    help="Draw extraction region on image and save visualization (don't create GIF)",
)
def main(
    season: str,
    character: str,
    data_dir: Path,
    image_type: str,
    coordinates: Optional[str],
    effect: str,
    fps: int,
    duration: float,
    output_dir: Optional[Path],
    force: bool,
    visualize: bool,
    turn_angle: float,
    move_distance: int,
):
    """Create animated GIF from character card images."""
    console.print(
        Panel.fit(
            "[bold cyan]Character Animation Generator[/bold cyan]\n"
            "Creates animated GIFs from character card images",
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
    for ext in [".webp", ".jpg", ".jpeg", ".png"]:
        candidate = char_dir / f"{image_type}{ext}"
        if candidate.exists():
            image_path = candidate
            break

    if not image_path:
        console.print(
            f"[red]Error: No {image_type} image found in {char_dir}[/red]\n"
            f"Looking for: {image_type}.webp, {image_type}.jpg, {image_type}.jpeg, or {image_type}.png"
        )
        sys.exit(1)

    console.print(f"[green]Found image: {image_path.name}[/green]")

    # Parse coordinates if provided (can be pixels or percentages)
    coords = None
    coords_percent = None
    if coordinates:
        try:
            parts = [x.strip() for x in coordinates.split(",")]
            if len(parts) != 4:
                raise ValueError("Need 4 values: x,y,width,height")
            
            # Check if percentages (contain %)
            if any("%" in p for p in parts):
                # Parse as percentages
                coords_percent = tuple(float(p.replace("%", "")) / 100.0 for p in parts)
                console.print(f"[cyan]Using percentage coordinates: {coords_percent}[/cyan]")
            else:
                # Parse as pixels
                coords = tuple(int(p) for p in parts)
                console.print(f"[cyan]Using pixel coordinates: {coords}[/cyan]")
        except ValueError as e:
            console.print(f"[red]Error parsing coordinates: {e}[/red]")
            sys.exit(1)

    # Extract character
    try:
        console.print("\n[cyan]Extracting character...[/cyan]")
        character_image, bbox = extract_character_with_coordinates(
            image_path, coords, coords_percent
        )
        console.print(f"[green]✓ Extracted character ({character_image.size[0]}x{character_image.size[1]})[/green]")
        console.print(f"[dim]Region: x={bbox[0]}, y={bbox[1]}, w={bbox[2]}, h={bbox[3]}[/dim]")
    except Exception as e:
        console.print(f"[red]Error extracting character: {e}[/red]")
        sys.exit(1)

    # Visualize extraction region if requested
    if visualize:
        if not output_dir:
            output_dir = char_dir / "animation"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save visualization with name matching source image
        image_stem = image_path.stem  # e.g., "back" from "back.webp"
        viz_output = output_dir / f"{image_stem}_character_region.png"
        
        try:
            visualize_extraction_region(image_path, bbox, viz_output, coords_percent)
            console.print(f"\n[green]✓ Visualization saved: {viz_output}[/green]")
            console.print(f"[dim]Showing extraction region on {image_path.name}[/dim]")
            console.print(f"[dim]Open the file to see the green box showing the character extraction area[/dim]")
        except Exception as e:
            console.print(f"[red]Error creating visualization: {e}[/red]")
            sys.exit(1)
        return

    # Calculate number of frames
    num_frames = int(fps * duration)

    # Generate animation frames
    console.print(f"\n[cyan]Generating {effect} animation ({num_frames} frames)...[/cyan]")
    try:
        if effect == "breathing":
            frames = create_breathing_animation(character_image, num_frames)
        elif effect == "parallax":
            frames = create_parallax_animation(character_image, num_frames)
        elif effect == "zoom":
            frames = create_zoom_animation(character_image, num_frames)
        elif effect == "rotate":
            frames = create_rotate_animation(character_image, num_frames)
        elif effect == "turn_3d":
            console.print(f"[dim]Using turn angle: {turn_angle}°[/dim]")
            frames = create_3d_turn_animation(character_image, num_frames, turn_angle)
        elif effect == "move_horizontal":
            console.print(f"[dim]Using movement distance: {move_distance} pixels[/dim]")
            frames = create_horizontal_move_animation(character_image, num_frames, (-move_distance, move_distance))
        else:
            console.print(f"[red]Unknown effect: {effect}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error generating animation: {e}[/red]")
        sys.exit(1)

    # Determine output path
    if not output_dir:
        output_dir = char_dir / "animation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{character}_{effect}_{fps}fps.gif"

    # Check if file exists
    if output_file.exists() and not force:
        console.print(f"[yellow]GIF already exists: {output_file}[/yellow]")
        console.print("Use --force to overwrite")
        sys.exit(0)

    # Create GIF
    try:
        console.print(f"\n[cyan]Creating GIF...[/cyan]")
        create_gif_from_frames(frames, output_file, duration=duration)
        
        file_size_kb = output_file.stat().st_size / 1024
        console.print(f"[green]✓ GIF created: {output_file}[/green]")
        console.print(f"[dim]File size: {file_size_kb:.1f} KB[/dim]")
        console.print(f"[dim]Frames: {num_frames}, Duration: {duration}s, Effect: {effect}[/dim]")
        console.print(f"[dim]Note: GIF files are not committed to git[/dim]")
    except Exception as e:
        console.print(f"[red]Error creating GIF: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

