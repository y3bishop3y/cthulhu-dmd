# Scripts Directory Reorganization Plan

**Date:** 2025-11-20

## Current Issues

1. **Tests in wrong location**: `scripts/tests/` should be at root level
2. **Too many top-level scripts**: Hard to find and organize
3. **Mixed concerns**: CLI scripts mixed with library code in `parsing/`
4. **Unclear organization**: Scripts scattered at root level

## Proposed Structure

```
cthulhu-dmd/
├── tests/                          # ← MOVE from scripts/tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_character_build.py
│   │   ├── test_character_models.py
│   │   └── ...
│   └── integration/                # Future integration tests
│
├── scripts/
│   ├── models/                     # Data models (library code)
│   │   ├── character.py
│   │   ├── character_build.py
│   │   ├── game_mechanics.py
│   │   └── ...
│   │
│   ├── core/                      # Core library modules
│   │   ├── parsing/               # ← MOVE library code from scripts/parsing/
│   │   │   ├── __init__.py
│   │   │   ├── ocr.py            # ← RENAME from advanced_ocr.py, multi_ocr.py
│   │   │   ├── preprocessing.py  # ← RENAME from font_aware_preprocessing.py
│   │   │   ├── layout.py         # ← RENAME from layout_aware_ocr.py
│   │   │   ├── nlp.py            # ← RENAME from nlp_parser.py, nlp_postprocessing.py
│   │   │   ├── text.py           # ← RENAME from text_parsing.py
│   │   │   ├── dice_detection.py # ← RENAME from dice_swirl_detection.py
│   │   │   └── benchmark.py      # ← RENAME from benchmark_ocr_strategies.py
│   │   │
│   │   ├── analysis/             # ← MOVE from scripts/analysis/
│   │   │   ├── __init__.py
│   │   │   ├── character.py     # ← RENAME from character_analyzer.py
│   │   │   └── power.py          # ← RENAME from power_combiner.py
│   │   │
│   │   └── utils/                # ← KEEP scripts/utils/
│   │       ├── ocr.py
│   │       ├── pdf.py
│   │       └── web.py
│   │
│   ├── cli/                       # All CLI scripts organized by purpose
│   │   ├── download/             # Download scripts
│   │   │   ├── __init__.py
│   │   │   ├── characters.py     # ← RENAME from download_characters.py
│   │   │   └── rulebook.py       # ← RENAME from download_rulebook.py
│   │   │
│   │   ├── parse/                # Parsing CLI scripts
│   │   │   ├── __init__.py
│   │   │   ├── characters.py     # ← MOVE from parsing/parse_characters.py
│   │   │   ├── rulebook.py       # ← MOVE from parsing/parse_rulebook.py
│   │   │   ├── special_powers.py # ← MOVE from parsing/parse_special_powers.py
│   │   │   ├── traits.py         # ← MOVE from parsing/parse_trait_character_assignments.py
│   │   │   └── benchmark.py      # ← MOVE from parsing/benchmark_ocr_strategies.py
│   │   │
│   │   ├── analyze/              # Analysis CLI scripts
│   │   │   ├── __init__.py
│   │   │   ├── powers.py         # ← RENAME from analyze_power_statistics.py
│   │   │   ├── quality.py        # ← RENAME from analyze_common_powers_quality.py
│   │   │   ├── pdf_comparison.py # ← RENAME from analyze_common_powers_from_pdf.py
│   │   │   └── character.py      # ← MOVE from analysis/character_analyzer.py
│   │   │
│   │   ├── update/               # Data update scripts
│   │   │   ├── __init__.py
│   │   │   ├── common_powers.py  # ← RENAME from update_common_powers_with_stats.py
│   │   │   ├── special_powers.py # ← RENAME from update_special_powers_with_stats.py
│   │   │   ├── characters.py    # ← RENAME from update_character_common_powers.py
│   │   │   ├── extract_powers.py # ← RENAME from extract_and_update_common_powers.py
│   │   │   └── cleanup.py        # ← RENAME from cleanup_and_improve_common_powers.py
│   │   │
│   │   └── tools/                # Utility CLI scripts
│   │       ├── __init__.py
│   │       ├── story.py          # ← RENAME from read_story.py
│   │       ├── fix_issues.py     # ← RENAME from fix_remaining_issues.py
│   │       └── nlp_analysis.py   # ← MOVE from parsing/analyze_ocr_with_nlp.py
│   │
│   ├── data/                     # Config files (keep as-is)
│   │   ├── ocr_corrections.toml
│   │   ├── season_urls.json
│   │   └── ...
│   │
│   └── animation/                # Animation feature (keep as-is)
│       ├── extract_character.py
│       └── utils/
│
└── pytest.ini                    # Update testpaths = tests
```

## Migration Steps

### Phase 1: Move Tests (Low Risk)
1. Move `scripts/tests/` → `tests/`
2. Update `pytest.ini`: `testpaths = tests`
3. Update `make/test.mk`: `scripts/tests/` → `tests/`
4. Update imports in test files if needed

### Phase 2: Reorganize Library Code (Medium Risk)
1. Create `scripts/core/` directory
2. Move library code from `scripts/parsing/` → `scripts/core/parsing/`
3. Move `scripts/analysis/` → `scripts/core/analysis/`
4. Rename files for clarity (see above)
5. Update imports across codebase

### Phase 3: Organize CLI Scripts (Medium Risk)
1. Create `scripts/cli/` directory structure
2. Move and rename CLI scripts into appropriate subdirectories
3. Update imports
4. Update any scripts that call these CLI scripts

### Phase 4: Update Documentation
1. Update `scripts/parsing/README.md` → `scripts/core/parsing/README.md`
2. Create `scripts/cli/README.md`
3. Update any other documentation references

## Benefits

1. **Clear separation**: Library code vs CLI scripts
2. **Better discoverability**: Scripts organized by purpose
3. **Standard structure**: Tests at root level (Python convention)
4. **Easier maintenance**: Related code grouped together
5. **Scalability**: Easy to add new CLI scripts or library modules

## Import Changes

### Before:
```python
from scripts.parsing.parse_characters import parse_character_images
from scripts.analysis.character_analyzer import analyze_character
```

### After:
```python
from scripts.core.parsing.text import clean_ocr_text
from scripts.cli.parse.characters import parse_character_images
from scripts.core.analysis.character import analyze_character
```

## Risk Assessment

- **Low Risk**: Moving tests (isolated, easy to verify)
- **Medium Risk**: Reorganizing library code (requires import updates)
- **Medium Risk**: Moving CLI scripts (requires path updates)

## Rollback Plan

- All changes can be reverted via git
- Can do incrementally (one phase at a time)
- Test after each phase

## Alternative: Simpler Approach

If full reorganization is too risky, consider:

```
scripts/
├── models/          # Keep as-is
├── utils/           # Keep as-is
├── core/            # New: library code
│   ├── parsing/     # Move library code from parsing/
│   └── analysis/    # Move from analysis/
├── cli/             # New: all CLI scripts
│   ├── download/
│   ├── parse/
│   ├── analyze/
│   └── update/
├── data/            # Keep as-is
└── animation/       # Keep as-is
```

This keeps `parsing/` and `analysis/` directories but moves CLI scripts out.


