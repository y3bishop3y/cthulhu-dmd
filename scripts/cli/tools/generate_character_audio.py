#!/usr/bin/env python3
"""
Generate character audio files with format: name, pause, location, pause, story.

Generates both male and female voice versions.
"""

import json
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from TTS.api import TTS
except ImportError as e:
    print(f"Error: Missing required library: {e}", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TTS_SPEAKERS_FILE = DATA_DIR / "tts_speakers.json"
DEFAULT_TTS_MODEL = "tts_models/en/vctk/vits"

console = Console()


def load_tts_speakers() -> Dict[str, Any]:
    """Load TTS speaker configuration from JSON file."""
    if not TTS_SPEAKERS_FILE.exists():
        # Fallback defaults
        return {
            "female": {"speaker_id": "p225", "name": "Lavinia"},
            "male": {"speaker_id": "p226", "name": "Randolph"},
        }

    try:
        with open(TTS_SPEAKERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning: Error loading TTS speakers config: {e}[/yellow]")
        return {
            "female": {"speaker_id": "p225", "name": "Lavinia"},
            "male": {"speaker_id": "p226", "name": "Randolph"},
        }


def load_character_data(char_dir: Path) -> Optional[dict]:
    """Load character.json and return data."""
    char_json = char_dir / "character.json"
    if not char_json.exists():
        return None

    try:
        with open(char_json, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading {char_json}: {e}[/red]")
        return None


def format_audio_text(character_data: dict) -> str:
    """Format text for audio: name, pause, location, pause, story."""
    name = character_data.get("name", "")
    location_obj = character_data.get("location", {})
    location_original = location_obj.get("original") or ""
    story = character_data.get("story", "")

    # Format: "Name. [pause] Location. [pause] Story"
    # Using periods and commas for natural pauses
    parts = []

    if name:
        parts.append(name)

    if location_original:
        parts.append(location_original)

    if story:
        parts.append(story)

    # Join with periods and spaces for natural pauses
    return ". ".join(parts) + "."


def generate_audio_file(
    text: str, output_path: Path, tts, speaker: Optional[str] = None, model: str = DEFAULT_TTS_MODEL
) -> bool:
    """Generate audio file from text."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if speaker:
            tts.tts_to_file(text=text, speaker=speaker, file_path=str(output_path))
        else:
            tts.tts_to_file(text=text, file_path=str(output_path))

        return True
    except Exception as e:
        console.print(f"[red]Error generating audio: {e}[/red]")
        return False


def get_speaker_gender(speaker_id: str) -> str:
    """Determine speaker gender from ID (simple heuristic)."""
    # VCTK speakers: p225-p376
    # Common female: p225, p226, p227, p228, p229, p230, p231, p232, p233, p234, p236, p237, p238, p239, p240, p241, p243, p244, p245, p246, p247, p248, p249, p250, p251, p252, p253, p254, p255, p256, p257, p258, p259, p260, p261, p262, p263, p264, p265, p266, p267, p268, p269, p270, p271, p272, p273, p274, p275, p276, p277, p278, p279, p280, p281, p282, p283, p284, p285, p286, p287, p288, p289, p290, p291, p292, p293, p294, p295, p296, p297, p298, p299, p300, p301, p302, p303, p304, p305, p306, p307, p308, p309, p310, p311, p312, p313, p314, p315, p316, p317, p318, p319, p320, p321, p322, p323, p324, p325, p326, p327, p328, p329, p330, p331, p332, p333, p334, p335, p336, p337, p338, p339, p340, p341, p342, p343, p344, p345, p346, p347, p348, p349, p350, p351, p352, p353, p354, p355, p356, p357, p358, p359, p360, p361, p362, p363, p364, p365, p366, p367, p368, p369, p370, p371, p372, p373, p374, p375, p376
    # This is a simplified approach - in practice you'd check metadata
    # For now, use common known speakers
    female_speakers = [
        "p225",
        "p226",
        "p227",
        "p229",
        "p230",
        "p231",
        "p232",
        "p233",
        "p234",
        "p236",
        "p237",
        "p238",
        "p239",
        "p240",
        "p241",
        "p243",
        "p244",
        "p245",
        "p246",
        "p247",
        "p248",
        "p249",
        "p250",
        "p251",
        "p252",
        "p253",
        "p254",
        "p255",
        "p256",
        "p257",
        "p258",
        "p259",
        "p260",
        "p261",
        "p262",
        "p263",
        "p264",
        "p265",
        "p266",
        "p267",
        "p268",
        "p269",
        "p270",
        "p271",
        "p272",
        "p273",
        "p274",
        "p275",
        "p276",
        "p277",
        "p278",
        "p279",
        "p280",
        "p281",
        "p282",
        "p283",
        "p284",
        "p285",
        "p286",
        "p287",
        "p288",
        "p289",
        "p290",
        "p291",
        "p292",
        "p293",
        "p294",
        "p295",
        "p296",
        "p297",
        "p298",
        "p299",
        "p300",
        "p301",
        "p302",
        "p303",
        "p304",
        "p305",
        "p306",
        "p307",
        "p308",
        "p309",
        "p310",
        "p311",
        "p312",
        "p313",
        "p314",
        "p315",
        "p316",
        "p317",
        "p318",
        "p319",
        "p320",
        "p321",
        "p322",
        "p323",
        "p324",
        "p325",
        "p326",
        "p327",
        "p328",
        "p329",
        "p330",
        "p331",
        "p332",
        "p333",
        "p334",
        "p335",
        "p336",
        "p337",
        "p338",
        "p339",
        "p340",
        "p341",
        "p342",
        "p343",
        "p344",
        "p345",
        "p346",
        "p347",
        "p348",
        "p349",
        "p350",
        "p351",
        "p352",
        "p353",
        "p354",
        "p355",
        "p356",
        "p357",
        "p358",
        "p359",
        "p360",
        "p361",
        "p362",
        "p363",
        "p364",
        "p365",
        "p366",
        "p367",
        "p368",
        "p369",
        "p370",
        "p371",
        "p372",
        "p373",
        "p374",
        "p375",
        "p376",
    ]

    if speaker_id in female_speakers:
        return "female"
    return "male"


def main():
    """Generate audio files for characters."""
    import argparse

    # Load speaker configuration
    speakers_config = load_tts_speakers()
    default_female = speakers_config.get("female", {}).get("speaker_id", "p225")
    default_male = speakers_config.get("male", {}).get("speaker_id", "p226")
    female_name = speakers_config.get("female", {}).get("name", "Lavinia")
    male_name = speakers_config.get("male", {}).get("name", "Randolph")

    parser = argparse.ArgumentParser(description="Generate character audio files")
    parser.add_argument("--season", default="season1", help="Season ID (default: season1)")
    parser.add_argument("--model", default=DEFAULT_TTS_MODEL, help="TTS model")
    parser.add_argument(
        "--female-speaker",
        default=default_female,
        help=f"Female speaker ID (default: {default_female} - {female_name})",
    )
    parser.add_argument(
        "--male-speaker",
        default=default_male,
        help=f"Male speaker ID (default: {default_male} - {male_name})",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate existing files")
    args = parser.parse_args()

    season_dir = DATA_DIR / args.season / "characters"

    if not season_dir.exists():
        console.print(f"[red]Error: {season_dir} does not exist[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Generating audio for {args.season}[/bold cyan]")
    console.print(f"Model: {args.model}")
    console.print(f"Female speaker: {args.female_speaker} ({female_name})")
    console.print(f"Male speaker: {args.male_speaker} ({male_name})\n")

    # Initialize TTS
    try:
        console.print("[cyan]Loading TTS model...[/cyan]")
        tts = TTS(model_name=args.model)
        console.print("[green]✓ Model loaded[/green]\n")
    except Exception as e:
        console.print(f"[red]Error loading TTS model: {e}[/red]")
        sys.exit(1)

    # Get character directories
    character_dirs = [d for d in season_dir.iterdir() if d.is_dir()]

    console.print(f"Found {len(character_dirs)} characters\n")

    success_count = 0
    skipped_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating audio...", total=len(character_dirs))

        for char_dir in sorted(character_dirs):
            char_id = char_dir.name
            progress.update(task, description=f"Processing {char_id}...")

            # Load character data
            character_data = load_character_data(char_dir)
            if not character_data:
                progress.update(task, advance=1)
                continue

            # Format text
            audio_text = format_audio_text(character_data)

            if not audio_text or audio_text == ".":
                console.print(f"  ⚠ {char_id}: No text to generate")
                progress.update(task, advance=1)
                continue

            # Generate filenames
            female_file = char_dir / f"{char_id}_audio_female.wav"
            male_file = char_dir / f"{char_id}_audio_male.wav"

            # Generate female audio
            if not female_file.exists() or args.force:
                if generate_audio_file(audio_text, female_file, tts, args.female_speaker):
                    console.print(f"  ✓ {char_id}: Generated female audio")
                else:
                    console.print(f"  ✗ {char_id}: Failed to generate female audio")
            else:
                skipped_count += 1
                console.print(f"  ⊘ {char_id}: Female audio exists (skipped)")

            # Generate male audio
            if not male_file.exists() or args.force:
                if generate_audio_file(audio_text, male_file, tts, args.male_speaker):
                    console.print(f"  ✓ {char_id}: Generated male audio")
                else:
                    console.print(f"  ✗ {char_id}: Failed to generate male audio")
            else:
                console.print(f"  ⊘ {char_id}: Male audio exists (skipped)")

            success_count += 1
            progress.update(task, advance=1)

    console.print(f"\n[green]✓ Generated audio for {success_count} characters[/green]")
    if skipped_count > 0:
        console.print(f"[yellow]⊘ Skipped {skipped_count} existing files[/yellow]")


if __name__ == "__main__":
    main()
