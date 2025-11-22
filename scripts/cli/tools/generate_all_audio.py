#!/usr/bin/env python3
"""
Batch generate audio files for all characters in a season.

This script iterates through all characters in a season and generates
audio files using the story.py script functionality.
"""

import sys
from pathlib import Path
from typing import Final, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}", file=sys.stderr)
    sys.exit(1)

# Import story script functions
from scripts.cli.tools.story import (
    find_character_directory,
    list_characters,
    get_character_name,
    get_character_story,
    DEFAULT_TTS_MODEL,
    DEFAULT_ENGLISH_FEMALE_SPEAKER,
    OUTPUT_AUDIO_EXT,
    load_speaker_metadata,
    get_speaker_description,
    list_available_speakers,
)
from scripts.models.tts_settings_config import get_tts_settings

console = Console()

# Constants
FILENAME_CHARACTER_JSON: Final[str] = "character.json"


def generate_audio_for_character(
    char_dir: Path,
    character: str,
    model: str,
    speaker: Optional[str],
    output_dir: Optional[Path],
    tts,
) -> tuple[bool, Optional[Path], Optional[str]]:
    """Generate audio for a single character.
    
    Returns:
        Tuple of (success, output_file_path, error_message)
    """
    try:
        # Get character name and story
        character_name = get_character_name(char_dir)
        story_text = get_character_story(char_dir)
        
        if not story_text:
            return False, None, "No story found"
        
        # Format text: "Character Name. Story text..."
        if character_name:
            full_text = f"{character_name}. {story_text}"
        else:
            full_text = story_text
        
        # Determine output directory
        output_path = output_dir if output_dir else char_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        file_character_name = character_name.lower().replace(" ", "_") if character_name else character
        speaker_suffix = f"_{speaker}" if speaker else ""
        output_file = output_path / f"{file_character_name}_audio{speaker_suffix}{OUTPUT_AUDIO_EXT}"
        
        # Check if already exists
        if output_file.exists():
            return True, output_file, None  # Already exists, skip
        
        # Get available speakers
        available_speakers = list_available_speakers(tts)
        if speaker and speaker not in available_speakers:
            speaker = None
        
        # Generate audio
        if speaker:
            tts.tts_to_file(text=full_text, speaker=speaker, file_path=str(output_file))
        else:
            tts.tts_to_file(text=full_text, file_path=str(output_file))
        
        return True, output_file, None
        
    except Exception as e:
        return False, None, str(e)


@click.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Root data directory",
)
@click.option(
    "--season",
    required=True,
    help="Season/box name (e.g., 'season1', 'unspeakable-box')",
)
@click.option(
    "--model",
    default=DEFAULT_TTS_MODEL,
    help=f"TTS model to use (default: {DEFAULT_TTS_MODEL})",
)
@click.option(
    "--speaker",
    default=DEFAULT_ENGLISH_FEMALE_SPEAKER,
    help=f"Speaker ID to use (e.g., 'p225'). Default: {DEFAULT_ENGLISH_FEMALE_SPEAKER}",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Directory to save audio files (default: each character's directory)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Regenerate audio even if file already exists",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=True,
    help="Skip characters that already have audio files (default: True)",
)
def main(
    data_dir: Path,
    season: str,
    model: str,
    speaker: Optional[str],
    output_dir: Optional[Path],
    force: bool,
    skip_existing: bool,
):
    """Generate audio files for all characters in a season."""
    console.print(
        Panel.fit(
            "[bold cyan]Batch Audio Generator[/bold cyan]\n"
            f"Generating audio for all characters in {season}",
            border_style="cyan",
        )
    )
    
    # Get list of characters
    characters = list_characters(data_dir, season)
    if not characters:
        console.print(f"[red]No characters found in {season}[/red]")
        sys.exit(1)
    
    console.print(f"\n[green]Found {len(characters)} characters[/green]")
    
    # Initialize TTS
    try:
        console.print(f"\n[cyan]Loading TTS model: {model}[/cyan]")
        from TTS.api import TTS
        tts = TTS(model_name=model)
        console.print("[green]✓ Model loaded[/green]")
    except Exception as e:
        console.print(f"[red]Error loading TTS model: {e}[/red]")
        sys.exit(1)
    
    # Get speaker info
    if speaker:
        try:
            metadata = load_speaker_metadata()
            speaker_name, speaker_desc = get_speaker_description(speaker, metadata)
            console.print(f"[cyan]Using speaker: {speaker} ({speaker_desc})[/cyan]")
        except Exception:
            console.print(f"[yellow]Warning: Could not load speaker metadata[/yellow]")
    
    # Process each character
    results = []
    skipped = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating audio...", total=len(characters))
        
        for character in characters:
            progress.update(task, description=f"Processing {character}...")
            
            char_dir = find_character_directory(data_dir, season, character)
            if not char_dir:
                results.append((character, False, None, "Directory not found"))
                progress.update(task, advance=1)
                continue
            
            # Check if already exists
            if skip_existing and not force:
                file_character_name = character.lower().replace(" ", "_")
                speaker_suffix = f"_{speaker}" if speaker else ""
                output_file = (output_dir if output_dir else char_dir) / f"{file_character_name}_audio{speaker_suffix}{OUTPUT_AUDIO_EXT}"
                if output_file.exists():
                    skipped.append(character)
                    results.append((character, True, output_file, None))
                    progress.update(task, advance=1)
                    continue
            
            # Generate audio
            success, output_file, error = generate_audio_for_character(
                char_dir, character, model, speaker, output_dir, tts
            )
            
            results.append((character, success, output_file, error))
            progress.update(task, advance=1)
    
    # Display results
    console.print("\n")
    table = Table(title="Audio Generation Results")
    table.add_column("Character", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("File", style="dim")
    table.add_column("Error", style="red")
    
    success_count = 0
    for character, success, output_file, error in results:
        if success:
            status = "✓ Generated" if output_file else "✓ Exists"
            file_str = str(output_file.name) if output_file else "N/A"
            table.add_row(character, status, file_str, "")
            success_count += 1
        else:
            table.add_row(character, "✗ Failed", "", error or "Unknown error")
    
    console.print(table)
    
    console.print(f"\n[green]✓ Successfully generated/verified: {success_count}/{len(characters)}[/green]")
    if skipped:
        console.print(f"[dim]Skipped (already exist): {len(skipped)}[/dim]")
    if success_count < len(characters):
        console.print(f"[yellow]Failed: {len(characters) - success_count}[/yellow]")
    console.print(f"[dim]Note: Audio files are not committed to git[/dim]")


if __name__ == "__main__":
    main()

