#!/usr/bin/env python3
"""
AI-powered animation generator using Stable Video Diffusion.

This script uses AI models to generate walking/running animations from static character images.
Requires GPU for best performance, but can run on CPU (slower).
"""

import sys
from pathlib import Path
from typing import Final, Optional

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

# Constants
DEFAULT_MODEL: Final[str] = "stabilityai/stable-video-diffusion-img2vid"
DEFAULT_FPS: Final[int] = 8
DEFAULT_NUM_FRAMES: Final[int] = 14


def check_dependencies() -> tuple[bool, Optional[str]]:
    """Check if AI animation dependencies are available.
    
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        import torch
        import diffusers
        return True, None
    except ImportError as e:
        return False, str(e)


def generate_video_with_svd(
    image_path: Path,
    output_path: Path,
    motion_prompt: str = "walking",
    num_frames: int = DEFAULT_NUM_FRAMES,
    fps: int = DEFAULT_FPS,
) -> bool:
    """Generate video animation using Stable Video Diffusion.
    
    Args:
        image_path: Path to character image
        output_path: Path to save output video/GIF
        motion_prompt: Motion description (e.g., "walking", "running")
        num_frames: Number of video frames to generate
        fps: Frames per second
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from diffusers import StableVideoDiffusionPipeline
        from diffusers.utils import load_image, export_to_video
        import torch
    except ImportError as e:
        console.print(f"[red]Error: Missing dependency: {e}[/red]")
        console.print("\n[yellow]Install with:[/yellow]")
        console.print("  pip install diffusers transformers accelerate torch torchvision")
        return False
    
    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        console.print("[yellow]Warning: GPU not available, using CPU (will be slow)[/yellow]")
    
    try:
        console.print(f"\n[cyan]Loading model: {DEFAULT_MODEL}[/cyan]")
        console.print("[dim]This may take a few minutes on first run (downloading model)...[/dim]")
        
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            DEFAULT_MODEL,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        pipe = pipe.to(device)
        pipe.unet.enable_forward_chunking()
        
        console.print("[green]✓ Model loaded[/green]")
        
        # Load and prepare image
        console.print(f"\n[cyan]Loading image: {image_path}[/cyan]")
        image = load_image(str(image_path))
        image = image.resize((1024, 576))  # SVD recommended size
        
        # Generate video
        # Note: Stable Video Diffusion doesn't support text prompts, it generates motion automatically
        console.print(f"\n[cyan]Generating {num_frames} frames...[/cyan]")
        console.print(f"[dim]Motion type: {motion_prompt} (note: SVD generates motion automatically)[/dim]")
        console.print("[dim]This may take several minutes (especially on CPU)...[/dim]")
        
        # Adjust motion_bucket_id: lower = subtle motion, higher = more motion
        # For character animations, lower values (50-100) often work better
        motion_bucket = 75  # Reduced for more subtle, realistic motion
        
        frames = pipe(
            image,
            decode_chunk_size=2,
            num_frames=num_frames,
            generator=torch.manual_seed(42),
            motion_bucket_id=motion_bucket,
        ).frames[0]
        
        # Export to video
        console.print(f"\n[cyan]Saving video...[/cyan]")
        export_to_video(frames, str(output_path), fps=fps)
        
        console.print(f"[green]✓ Video saved: {output_path}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Error generating video: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def convert_video_to_gif(video_path: Path, gif_path: Path, fps: int = DEFAULT_FPS) -> bool:
    """Convert video to animated GIF.
    
    Args:
        video_path: Path to input video
        gif_path: Path to save GIF
        fps: Frames per second for GIF
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import imageio
        import imageio.v2 as imageio_v2
    except ImportError:
        console.print("[yellow]Warning: imageio not installed, skipping GIF conversion[/yellow]")
        console.print("Install with: pip install imageio imageio-ffmpeg")
        return False
    
    try:
        console.print(f"\n[cyan]Converting video to GIF...[/cyan]")
        
        # Read video frames
        reader = imageio_v2.get_reader(str(video_path))
        frames = [frame for frame in reader]
        
        # Write as GIF
        imageio.mimsave(str(gif_path), frames, fps=fps, loop=0)
        
        console.print(f"[green]✓ GIF saved: {gif_path}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Error converting to GIF: {e}[/red]")
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
    type=click.Choice(["front", "back"]),
    default="back",
    help="Which card image to use",
)
@click.option(
    "--coordinates",
    type=str,
    help="Character extraction coordinates as 'x,y,width,height' percentages (e.g., '15%,17%,28%,58%')",
)
@click.option(
    "--motion-prompt",
    type=str,
    default="walking",
    help="Motion description (e.g., 'walking', 'running', 'idle')",
)
@click.option(
    "--num-frames",
    type=int,
    default=DEFAULT_NUM_FRAMES,
    help=f"Number of video frames to generate (default: {DEFAULT_NUM_FRAMES})",
)
@click.option(
    "--fps",
    type=int,
    default=DEFAULT_FPS,
    help=f"Frames per second (default: {DEFAULT_FPS})",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory (default: character_dir/animation)",
)
@click.option(
    "--output-format",
    type=click.Choice(["gif", "mp4", "both"]),
    default="gif",
    help="Output format (default: gif)",
)
def main(
    season: str,
    character: str,
    data_dir: Path,
    image_type: str,
    coordinates: Optional[str],
    motion_prompt: str,
    num_frames: int,
    fps: int,
    output_dir: Optional[Path],
    output_format: str,
):
    """Generate AI-powered animation from character image using Stable Video Diffusion."""
    console.print(
        Panel.fit(
            "[bold cyan]AI Character Animation Generator[/bold cyan]\n"
            "Uses Stable Video Diffusion to create walking/running animations",
            border_style="cyan",
        )
    )
    
    # Check dependencies
    has_deps, error = check_dependencies()
    if not has_deps:
        console.print(f"[red]Error: Missing dependencies[/red]")
        console.print(f"[yellow]{error}[/yellow]")
        console.print("\n[yellow]Install with:[/yellow]")
        console.print("  pip install diffusers transformers accelerate torch torchvision")
        console.print("\n[yellow]For GIF conversion:[/yellow]")
        console.print("  pip install imageio imageio-ffmpeg")
        sys.exit(1)
    
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
            f"[red]Error: No {image_type} image found in {char_dir}[/red]"
        )
        sys.exit(1)
    
    # Extract character if coordinates provided
    if coordinates:
        try:
            # Import helper function from create_gif
            create_gif_module_path = Path(__file__).parent / "create_gif.py"
            if not create_gif_module_path.exists():
                console.print(f"[red]Error: create_gif.py not found at {create_gif_module_path}[/red]")
                sys.exit(1)
            
            # Import the module directly
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
            
            console.print(f"[cyan]Extracting character with coordinates...[/cyan]")
            character_image, _ = extract_character_with_coordinates(image_path, coords, coords_percent)
            
            # Save extracted character to temp file
            temp_image = char_dir / "animation" / "temp_character.png"
            temp_image.parent.mkdir(parents=True, exist_ok=True)
            character_image.save(temp_image)
            image_path = temp_image
            console.print(f"[green]✓ Character extracted[/green]")
        except Exception as e:
            console.print(f"[red]Error extracting character: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            sys.exit(1)
    
    # Determine output directory
    if not output_dir:
        output_dir = char_dir / "animation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate video
    video_output = output_dir / f"{character}_ai_{motion_prompt}_{fps}fps.mp4"
    
    success = generate_video_with_svd(
        image_path,
        video_output,
        motion_prompt=motion_prompt,
        num_frames=num_frames,
        fps=fps,
    )
    
    if not success:
        sys.exit(1)
    
    # Convert to GIF if requested
    if output_format in ["gif", "both"]:
        gif_output = output_dir / f"{character}_ai_{motion_prompt}_{fps}fps.gif"
        convert_video_to_gif(video_output, gif_output, fps=fps)
    
    if output_format == "gif":
        # Remove video file if only GIF requested
        video_output.unlink()
    
    console.print(f"\n[green]✓ Animation complete![/green]")
    console.print(f"[dim]Note: AI-generated files are not committed to git[/dim]")


if __name__ == "__main__":
    main()

