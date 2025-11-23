#!/usr/bin/env python3
"""Regenerate audio for Elizabeth Ives with corrected text."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.cli.tools.generate_character_audio_simple import (
    load_tts_speakers, load_character_data, format_audio_text, generate_audio_file
)

try:
    from TTS.api import TTS
except ImportError:
    print("Error: TTS library not installed. Install with: pip install TTS")
    sys.exit(1)

# Load speaker config
speakers_config = load_tts_speakers()
female_speaker = speakers_config.get("female", {}).get("speaker_id", "p225")
male_speaker = speakers_config.get("male", {}).get("speaker_id", "p226")
female_name = speakers_config.get("female", {}).get("name", "Lavinia")
male_name = speakers_config.get("male", {}).get("name", "Randolph")

# Character directory
char_dir = project_root / "data" / "season1" / "characters" / "elizabeth"

if not char_dir.exists():
    print(f"Error: {char_dir} does not exist")
    sys.exit(1)

# Load character data
character_data = load_character_data(char_dir)
if not character_data:
    print("Error: Could not load character data")
    sys.exit(1)

# Format text
audio_text = format_audio_text(character_data)
if not audio_text:
    print("Error: Could not format audio text")
    sys.exit(1)

print(f"Character: {character_data.get('name', 'Elizabeth Ives')}")
print(f"Audio text preview: {audio_text[:150]}...")
print()

# Initialize TTS
print("Loading TTS model...")
tts = TTS(model_name="tts_models/en/vctk/vits")
print("✓ Model loaded\n")

# Generate filenames
char_id = "elizabeth"
female_file = char_dir / f"{char_id}_audio_female.wav"
male_file = char_dir / f"{char_id}_audio_male.wav"

# Generate female audio
print(f"Generating female audio ({female_speaker} - {female_name})...")
if generate_audio_file(audio_text, female_file, tts, female_speaker):
    file_size = female_file.stat().st_size / 1024
    print(f"✓ Generated female audio ({file_size:.1f} KB)")
else:
    print("✗ Failed to generate female audio")
    sys.exit(1)

# Generate male audio
print(f"Generating male audio ({male_speaker} - {male_name})...")
if generate_audio_file(audio_text, male_file, tts, male_speaker):
    file_size = male_file.stat().st_size / 1024
    print(f"✓ Generated male audio ({file_size:.1f} KB)")
else:
    print("✗ Failed to generate male audio")
    sys.exit(1)

print("\n✓ Successfully regenerated audio for Elizabeth Ives")
print(f"  Female: {female_file.name} ({female_name})")
print(f"  Male: {male_file.name} ({male_name})")

