#!/usr/bin/env python3
"""
Read character stories using Coqui TTS with multi-speaker models.
Generates audio files from character story text.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from TTS.api import TTS  # coqui-tts package
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run python scripts/cli/tools/story.py [options]\n"
        "  2. source .venv/bin/activate && python scripts/cli/tools/story.py [options]\n"
        "  3. make setup (to install dependencies) then run directly\n\n"
        "Recommended: uv run python scripts/cli/tools/story.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.models.tts_settings_config import get_tts_settings

console = Console()

# Constants
FILENAME_STORY_TXT: Final[str] = "story.txt"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"
# Load TTS model from TOML config
_tts_settings = get_tts_settings()
DEFAULT_TTS_MODEL: Final[str] = (
    _tts_settings.tts_default_model
    if _tts_settings.tts_default_model
    else "tts_models/en/vctk/vits"
)
OUTPUT_AUDIO_EXT: Final[str] = ".wav"
SPEAKER_METADATA_FILE: Final[str] = "scripts/data/vctk_speakers.json"
# Default English female speaker (p225 is a good choice - age 23, Southern England)
DEFAULT_ENGLISH_FEMALE_SPEAKER: Final[str] = "p225"


def find_character_directory(data_dir: Path, season: str, character: str) -> Optional[Path]:
    """Find the character directory given season and character name."""
    season_dir = data_dir / season
    if not season_dir.exists():
        return None

    # Try exact match first
    char_dir = season_dir / character.lower()
    if char_dir.exists():
        return char_dir

    # Try to find by partial match
    for subdir in season_dir.iterdir():
        if subdir.is_dir() and character.lower() in subdir.name.lower():
            return subdir

    return None


def get_character_name(char_dir: Path) -> Optional[str]:
    """Get the character name from character.json."""
    json_file = char_dir / FILENAME_CHARACTER_JSON
    if json_file.exists():
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            return data.get("name")
        except (json.JSONDecodeError, Exception):
            pass
    return None


def get_character_story(char_dir: Path) -> Optional[str]:
    """Get the character story from story.txt or character.json."""
    # Try story.txt first
    story_file = char_dir / FILENAME_STORY_TXT
    if story_file.exists():
        return story_file.read_text(encoding="utf-8").strip()

    # Fallback to character.json
    json_file = char_dir / FILENAME_CHARACTER_JSON
    if json_file.exists():
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            return data.get("story")
        except (json.JSONDecodeError, Exception):
            pass

    return None


def load_speaker_metadata() -> Dict[str, Dict[str, Any]]:
    """Load speaker metadata from JSON file."""
    metadata_path = Path(SPEAKER_METADATA_FILE)
    if not metadata_path.exists():
        console.print(f"[yellow]Warning: Speaker metadata file not found: {metadata_path}[/yellow]")
        return {}

    try:
        with open(metadata_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        console.print(f"[yellow]Warning: Could not load speaker metadata: {e}[/yellow]")
        return {}


def get_speaker_description(
    speaker_id: str, metadata: Dict[str, Dict[str, Any]]
) -> Tuple[str, str]:
    """Get name and description for a VCTK speaker ID."""
    if speaker_id in metadata:
        meta = metadata[speaker_id]
        name = meta.get("name", speaker_id)
        description = meta.get("description", "")
        return name, description
    else:
        # Generic description for unknown speakers
        if speaker_id.startswith("p"):
            name = f"Speaker {speaker_id[1:]}"
            description = "English accent"
        else:
            name = speaker_id
            description = "Unknown speaker"
        return name, description


def list_available_speakers(tts: TTS) -> List[str]:
    """List all available speakers for the TTS model."""
    try:
        speakers = tts.speakers
        if speakers:
            return list(speakers)
    except (AttributeError, Exception):
        pass
    return []


def list_seasons(data_dir: Path) -> List[str]:
    """List all available seasons/boxes in the data directory."""
    seasons = []
    for item in data_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            seasons.append(item.name)
    return sorted(seasons)


def list_characters(data_dir: Path, season: str) -> List[str]:
    """List all characters in a season."""
    season_dir = data_dir / season
    if not season_dir.exists():
        return []

    characters = []
    for item in season_dir.iterdir():
        if item.is_dir():
            characters.append(item.name)
    return sorted(characters)


@click.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Root data directory",
)
@click.option(
    "--season",
    help="Season/box name (e.g., 'season1', 'unspeakable-box')",
)
@click.option(
    "--character",
    help="Character name (e.g., 'adam', 'al')",
)
@click.option(
    "--model",
    default=DEFAULT_TTS_MODEL,
    help=f"TTS model to use (default: {DEFAULT_TTS_MODEL})",
)
@click.option(
    "--speaker",
    default=DEFAULT_ENGLISH_FEMALE_SPEAKER,
    help=f"Speaker ID to use (e.g., 'p225'). Default: {DEFAULT_ENGLISH_FEMALE_SPEAKER} (English female). Use --list-speakers to see available options",
)
@click.option(
    "--list-seasons",
    is_flag=True,
    help="List all available seasons/boxes",
)
@click.option(
    "--list-characters",
    help="List all characters in the specified season",
)
@click.option(
    "--list-speakers",
    is_flag=True,
    help="List all available speakers for the TTS model",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Directory to save audio files (default: character directory)",
)
def main(
    data_dir: Path,
    season: Optional[str],
    character: Optional[str],
    model: str,
    speaker: Optional[str],
    list_seasons: bool,
    list_characters: Optional[str],
    list_speakers: bool,
    output_dir: Optional[Path],
):
    """Read character stories using Coqui TTS with multi-speaker models."""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Story Reader[/bold cyan]\n"
            "Generates audio from character stories using Coqui TTS",
            border_style="cyan",
        )
    )

    # List seasons if requested
    if list_seasons:
        seasons = list_seasons(data_dir)
        if seasons:
            console.print("\n[cyan]Available seasons/boxes:[/cyan]")
            for s in seasons:
                console.print(f"  • {s}")
        else:
            console.print("[yellow]No seasons found[/yellow]")
        return

    # List characters if requested
    if list_characters:
        characters = list_characters(data_dir, list_characters)
        if characters:
            console.print(f"\n[cyan]Characters in '{list_characters}':[/cyan]")
            for c in characters:
                console.print(f"  • {c}")
        else:
            console.print(f"[yellow]No characters found in '{list_characters}'[/yellow]")
        return

    # Initialize TTS
    try:
        console.print(f"\n[cyan]Loading TTS model: {model}[/cyan]")
        tts = TTS(model)
        console.print("[green]✓ Model loaded successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error loading TTS model:[/red] {e}")
        console.print(
            "\n[yellow]Note: First run may download the model (~500MB). "
            "This may take a few minutes.[/yellow]"
        )
        sys.exit(1)

    # List speakers if requested
    if list_speakers:
        speakers = list_available_speakers(tts)
        if speakers:
            # Load speaker metadata
            metadata = load_speaker_metadata()

            # Create table
            table = Table(
                title=f"Available Speakers for {model}",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan",
            )
            table.add_column("ID", style="cyan", no_wrap=True, width=8)
            table.add_column("Name", style="magenta", width=20)
            table.add_column("Description", style="white", width=60)

            # Add all speakers to table
            for speaker_id in sorted(speakers):
                name, desc = get_speaker_description(speaker_id, metadata)
                table.add_row(speaker_id, name, desc)

            console.print()
            console.print(table)
            console.print(f"\n[dim]Total: {len(speakers)} speakers[/dim]")
        else:
            console.print(f"[yellow]No speakers found for model {model}[/yellow]")
        return

    # Validate required arguments
    if not season or not character:
        console.print(
            "[red]Error: --season and --character are required[/red]\n"
            "Use --list-seasons to see available seasons\n"
            "Use --list-characters <season> to see available characters"
        )
        sys.exit(1)

    # Find character directory
    char_dir = find_character_directory(data_dir, season, character)
    if not char_dir:
        console.print(f"[red]Character '{character}' not found in season '{season}'[/red]")
        console.print(f"\nAvailable seasons: {', '.join(list_seasons(data_dir))}")
        if (data_dir / season).exists():
            console.print(
                f"\nAvailable characters in '{season}': "
                f"{', '.join(list_characters(data_dir, season))}"
            )
        sys.exit(1)

    # Get character name and story
    character_name = get_character_name(char_dir)
    story_text = get_character_story(char_dir)
    
    if not story_text:
        console.print(f"[red]No story found for {character}[/red]")
        console.print(f"Checked: {char_dir / FILENAME_STORY_TXT}")
        console.print(f"Checked: {char_dir / FILENAME_CHARACTER_JSON}")
        sys.exit(1)

    # Format text: "Character Name. Story text..."
    if character_name:
        full_text = f"{character_name}. {story_text}"
        console.print(f"\n[green]Found character: {character_name}[/green]")
    else:
        full_text = story_text
    console.print(f"\n[green]Found story for {character}[/green]")
    
    console.print(f"[dim]Text length: {len(full_text)} characters[/dim]")

    # Determine output directory
    output_path = output_dir if output_dir else char_dir
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename (use character name if available, otherwise use directory name)
    file_character_name = character_name.lower().replace(" ", "_") if character_name else character
    speaker_suffix = f"_{speaker}" if speaker else ""
    output_file = output_path / f"{file_character_name}_audio{speaker_suffix}{OUTPUT_AUDIO_EXT}"

    # Get available speakers
    available_speakers = list_available_speakers(tts)
    if not available_speakers:
        console.print("[yellow]Warning: No speakers available for this model[/yellow]")
        speaker = None
    elif speaker and speaker not in available_speakers:
        console.print(f"[yellow]Warning: Speaker '{speaker}' not found[/yellow]")
        console.print(f"[cyan]Available speakers: {', '.join(available_speakers[:10])}...[/cyan]")
        speaker = None

    # Generate audio
    try:
        console.print("\n[cyan]Generating audio...[/cyan]")
        if speaker:
            # Get speaker description
            metadata = load_speaker_metadata()
            speaker_name, speaker_desc = get_speaker_description(speaker, metadata)
            console.print(f"  Using speaker: {speaker} ({speaker_desc})")
            tts.tts_to_file(text=full_text, speaker=speaker, file_path=str(output_file))
        else:
            console.print("  Using default speaker")
            tts.tts_to_file(text=full_text, file_path=str(output_file))

        console.print(f"[green]✓ Audio saved to: {output_file}[/green]")
        console.print(f"[dim]File size: {output_file.stat().st_size / 1024:.1f} KB[/dim]")
        console.print(f"[dim]Note: Audio files are not committed to git[/dim]")

    except Exception as e:
        console.print(f"[red]Error generating audio:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
