# CLI Scripts

This directory contains all command-line interface (CLI) scripts organized by purpose. All scripts use `click` for argument parsing and `rich` for formatted output.

## Quick Reference

| Category | Scripts | Purpose |
|----------|---------|---------|
| **Download** | 2 scripts | Download data from web sources |
| **Parse** | 5 scripts | Extract and parse data from images/PDFs |
| **Analyze** | 4 scripts | Analyze power statistics and data quality |
| **Update** | 5 scripts | Update JSON data files with parsed/calculated data |
| **Tools** | 3 scripts | Utility scripts for TTS, NLP, and fixes |

---

## Download Scripts

Scripts for downloading data from external sources.

| Script | Purpose | Usage |
|--------|---------|-------|
| `download/characters.py` | Download character card images and HTML stories from makecraftgame.com. Organizes images by season/box and character name. | `uv run python scripts/cli/download/characters.py --season season1` |
| `download/rulebook.py` | Download the Death May Die rulebook PDF to the data directory. | `uv run python scripts/cli/download/rulebook.py` |

### Features

**`download/characters.py`**
- Downloads front and back card images for all characters
- Extracts character stories from HTML pages
- Organizes files by season/box and character name
- Creates `character.json` files with extracted story data
- Skips already downloaded images

**`download/rulebook.py`**
- Downloads rulebook PDF from official source
- Saves to `data/DMD_Rulebook_web.pdf`

---

## Parse Scripts

Scripts for extracting and parsing data from images and PDFs using OCR.

| Script | Purpose | Usage |
|--------|---------|-------|
| `parse/characters.py` | Parse character card images to extract character data (name, location, motto, story from front card; powers from back card). | `uv run python scripts/cli/parse/characters.py --character adam --season season1` |
| `parse/rulebook.py` | Parse the rulebook PDF into structured markdown with sections and subsections. | `uv run python scripts/cli/parse/rulebook.py --output-format markdown` |
| `parse/special_powers.py` | Parse and update special powers for characters from back card images. Extracts all 4 power levels. | `uv run python scripts/cli/parse/special_powers.py --character ahmed --season season1` |
| `parse/traits.py` | Parse pages 3-5 of traits_booklet.pdf to extract which characters have which common traits. | `uv run python scripts/cli/parse/traits.py` |
| `parse/benchmark.py` | Benchmark OCR strategies to find the best combination for character data extraction. Scores strategies 1-100. | `uv run python scripts/cli/parse/benchmark.py --character adam --top 10` |

### Features

**`parse/characters.py`**
- Uses optimal OCR strategies per card region (name, location, motto, story, powers)
- Extracts front card: name, location, motto, story
- Extracts back card: special power levels, common powers
- Merges with existing `character.json` data
- Supports layout-aware OCR extraction

**`parse/rulebook.py`**
- Extracts structured content from rulebook PDF
- Outputs markdown or plain text
- Preserves section hierarchy

**`parse/special_powers.py`**
- Parses all 4 levels of special powers
- Validates and cleans OCR text
- Updates `character.json` files
- Handles OCR errors and variations

**`parse/traits.py`**
- Extracts character-trait assignments from PDF
- Creates `trait_character_assignments.json`
- Helps verify character data completeness

**`parse/benchmark.py`**
- Tests 20+ OCR preprocessing + engine combinations
- Scores extraction quality (name, location, motto, story, powers, dice recognition)
- Saves benchmark results to `.generated/benchmark/`
- Automatically updates optimal strategies config
- Supports hybrid strategy analysis

---

## Analyze Scripts

Scripts for analyzing power statistics, data quality, and character builds.

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze/powers.py` | Analyze common powers and calculate their statistical impact on dice rolls (expected successes, tentacle risk, elder sign probability). | `uv run python scripts/cli/analyze/powers.py --power marksman` |
| `analyze/quality.py` | Analyze `common_powers.json` for quality issues (OCR errors, incomplete text, statistics accuracy, missing effects). | `uv run python scripts/cli/analyze/quality.py` |
| `analyze/pdf_comparison.py` | Compare `common_powers.json` against `traits_booklet.pdf` to verify parsing accuracy and identify OCR errors. | `uv run python scripts/cli/analyze/pdf_comparison.py` |
| `analyze/character.py` | Analyze character builds and calculate their effectiveness. Shows play strategy, strengths, weaknesses, and statistics. | `uv run python scripts/cli/analyze/character.py --character amelie --season unknowable-box` |

### Features

**`analyze/powers.py`**
- Calculates dice probability impacts
- Analyzes expected successes per power level
- Calculates tentacle risk
- Determines elder sign conversion effects
- Generates power statistics

**`analyze/quality.py`**
- Detects OCR errors in descriptions
- Identifies incomplete or garbled text
- Validates statistics accuracy
- Checks for missing or incorrect effects
- Suggests improvements

**`analyze/pdf_comparison.py`**
- Extracts power descriptions from PDF
- Compares with JSON descriptions
- Identifies OCR errors and parsing issues
- Validates statistics calculations
- Suggests effect and statistics improvements

**`analyze/character.py`**
- Loads character with powers at specific levels
- Calculates full character statistics
- Determines playstyle (offensive, defensive, balanced, utility)
- Identifies strengths and weaknesses
- Shows power combination effects

---

## Update Scripts

Scripts for updating JSON data files with parsed or calculated data.

| Script | Purpose | Usage |
|--------|---------|-------|
| `update/common_powers.py` | Update `common_powers.json` with statistical analysis for each power level. Adds dice additions, expected successes, tentacle risk. | `uv run python scripts/cli/update/common_powers.py` |
| `update/special_powers.py` | Update character.json files with statistical analysis for special power levels. Adds dice additions, expected successes, tentacle risk, conditional effects. | `uv run python scripts/cli/update/special_powers.py --character ahmed` |
| `update/characters.py` | Update character.json files with correct common power assignments from trait_character_assignments.json. Ensures all characters have exactly 2 common powers. | `uv run python scripts/cli/update/characters.py` |
| `update/extract_powers.py` | Extract common power level descriptions from character cards using OCR. Aggregate results and update common_powers.json and character.json files. | `uv run python scripts/cli/update/extract_powers.py --sample-size 10` |
| `update/cleanup.py` | Comprehensive cleanup and improvement of common_powers.json. Fixes OCR errors, improves extraction, adds enhanced statistics fields. | `uv run python scripts/cli/update/cleanup.py --cleanup --recalculate-stats` |

### Features

**`update/common_powers.py`**
- Analyzes each power level
- Adds statistical data (dice additions, expected successes, tentacle risk)
- Updates `common_powers.json` with calculated statistics
- Validates data integrity

**`update/special_powers.py`**
- Analyzes special power levels
- Extracts conditional effects, reroll effects, healing effects, defensive effects
- Adds statistical data to character.json files
- Supports dry-run mode

**`update/characters.py`**
- Loads trait assignments from JSON
- Updates all character.json files with correct common powers
- Validates exactly 2 common powers per character
- Normalizes character names for matching

**`update/extract_powers.py`**
- Extracts power descriptions from character cards using OCR
- Aggregates results across multiple characters
- Updates `common_powers.json` with extracted descriptions
- Updates character.json files with power assignments

**`update/cleanup.py`**
- Fixes OCR errors in descriptions
- Improves OCR extraction with better preprocessing
- Adds enhanced statistics fields
- Generates cleaned version of `common_powers.json`
- Applies domain-specific corrections

---

## Tools Scripts

Utility scripts for various tasks.

| Script | Purpose | Usage |
|--------|---------|-------|
| `tools/story.py` | Read character stories using Coqui TTS with multi-speaker models. Generates audio files from character story text. | `uv run python scripts/cli/tools/story.py --character adam --season season1` |
| `tools/fix_issues.py` | Apply manual corrections to `common_powers.json` for known problematic descriptions. | `uv run python scripts/cli/tools/fix_issues.py` |
| `tools/nlp_analysis.py` | Analyze OCR output with NLP to extract semantic meaning. Helps understand garbled OCR text. | `uv run python scripts/cli/tools/nlp_analysis.py --character adam` |

### Features

**`tools/story.py`**
- Text-to-speech for character stories
- Multi-speaker support (VCTK speakers)
- Audio file generation
- Speaker selection and listing

**`tools/fix_issues.py`**
- Applies manual corrections for known issues
- Fixes specific power descriptions
- Updates `common_powers.json` with corrections

**`tools/nlp_analysis.py`**
- Extracts semantic meaning from OCR text
- Compares OCR output with ground truth
- Helps understand garbled OCR text
- Uses spaCy for NLP processing

---

## Running Scripts

All scripts can be run using `uv`:

```bash
# Run any script
uv run python scripts/cli/<category>/<script>.py [options]

# Get help
uv run python scripts/cli/<category>/<script>.py --help
```

### Examples

```bash
# Download season 1 characters
uv run python scripts/cli/download/characters.py --season season1

# Parse a character
uv run python scripts/cli/parse/characters.py --character adam --season season1

# Analyze power statistics
uv run python scripts/cli/analyze/powers.py --power marksman

# Update common powers with stats
uv run python scripts/cli/update/common_powers.py

# Read a character story with TTS
uv run python scripts/cli/tools/story.py --character adam --season season1
```

---

## Script Dependencies

All scripts depend on:
- **click** - CLI argument parsing
- **rich** - Formatted terminal output
- **pydantic** - Data validation and models

Additional dependencies vary by script:
- **OCR scripts** require: `pytesseract`, `opencv-python`, `pillow`
- **PDF scripts** require: `pypdf`, `pdfplumber`
- **Web scripts** require: `requests`, `beautifulsoup4`
- **NLP scripts** require: `spacy`, `en-core-web-sm`
- **TTS scripts** require: `coqui-tts`

---

## Related Documentation

- **Library Code:** See `scripts/core/` for parsing and analysis library modules
- **Data Models:** See `scripts/models/` for Pydantic data models
- **Utilities:** See `scripts/utils/` for shared utility functions
- **Parsing Library:** See `scripts/core/parsing/README.md` for parsing module documentation

---

**Last Updated:** 2025-11-20

