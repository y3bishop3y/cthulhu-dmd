#!/usr/bin/env python3
"""
Generate character audio files with format: name, pause, location, pause, story.

Generates both male and female voice versions using HP Lovecraft character names.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TTS_SPEAKERS_FILE = DATA_DIR / "tts_speakers.json"
DEFAULT_TTS_MODEL = "tts_models/en/vctk/vits"


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
        print(f"Warning: Error loading TTS speakers config: {e}")
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
        print(f"Error loading {char_json}: {e}")
        return None


def format_audio_text(character_data: dict) -> Optional[str]:
    """Format text for audio: name, pause, location, pause, story."""
    name = character_data.get("name", "")
    location_obj = character_data.get("location", {})
    location_original = location_obj.get("original") or ""
    story = character_data.get("story", "")

    # Need at least name to generate audio
    if not name:
        return None

    # Format: "Name. [pause] Location. [pause] Story"
    parts = []

    if name:
        parts.append(name)

    if location_original:
        parts.append(location_original)

    if story:
        parts.append(story)

    # Join with periods and spaces for natural pauses
    return ". ".join(parts) + "."


def generate_audio_file(text: str, output_path: Path, tts, speaker: Optional[str] = None) -> bool:
    """Generate audio file from text."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if speaker:
            tts.tts_to_file(text=text, speaker=speaker, file_path=str(output_path))
        else:
            tts.tts_to_file(text=text, file_path=str(output_path))

        return True
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False


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
        print(f"Error: {season_dir} does not exist")
        sys.exit(1)

    print("=" * 70)
    print(f"Generating audio for {args.season}")
    print("=" * 70)
    print(f"Model: {args.model}")
    print(f"Female speaker: {args.female_speaker} ({female_name})")
    print(f"Male speaker: {args.male_speaker} ({male_name})\n")

    # Initialize TTS
    try:
        print("Loading TTS model...")
        from TTS.api import TTS

        tts = TTS(model_name=args.model)
        print("✓ Model loaded\n")
    except ImportError:
        print("Error: TTS library not available. Install with: pip install TTS")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading TTS model: {e}")
        sys.exit(1)

    # Get character directories
    character_dirs = [d for d in season_dir.iterdir() if d.is_dir()]
    print(f"Found {len(character_dirs)} characters\n")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for char_dir in sorted(character_dirs):
        char_id = char_dir.name
        print(f"[{char_id}]")

        # Load character data
        character_data = load_character_data(char_dir)
        if not character_data:
            print("  ⚠ No character data found")
            failed_count += 1
            continue

        # Format text
        audio_text = format_audio_text(character_data)

        if not audio_text or audio_text == ".":
            print("  ⚠ No text to generate (missing name)")
            failed_count += 1
            continue

        # Generate filenames
        female_file = char_dir / f"{char_id}_audio_female.wav"
        male_file = char_dir / f"{char_id}_audio_male.wav"

        # Generate female audio
        if not female_file.exists() or args.force:
            if generate_audio_file(audio_text, female_file, tts, args.female_speaker):
                file_size = female_file.stat().st_size / 1024
                print(f"  ✓ Generated female audio ({file_size:.1f} KB)")
            else:
                print("  ✗ Failed to generate female audio")
                failed_count += 1
        else:
            skipped_count += 1
            print("  ⊘ Female audio exists (skipped)")

        # Generate male audio
        if not male_file.exists() or args.force:
            if generate_audio_file(audio_text, male_file, tts, args.male_speaker):
                file_size = male_file.stat().st_size / 1024
                print(f"  ✓ Generated male audio ({file_size:.1f} KB)")
            else:
                print("  ✗ Failed to generate male audio")
                failed_count += 1
        else:
            print("  ⊘ Male audio exists (skipped)")

        success_count += 1
        print()

    print("=" * 70)
    print(f"✓ Generated audio for {success_count} characters")
    if skipped_count > 0:
        print(f"⊘ Skipped {skipped_count} existing files")
    if failed_count > 0:
        print(f"✗ Failed {failed_count} characters")
    print("=" * 70)


if __name__ == "__main__":
    main()
