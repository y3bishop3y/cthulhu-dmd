# Data Cleanup & Validation

## Overview

Before we can fully utilize the character build and team composition analysis, we need to ensure:
1. **Common Powers** are correctly parsed and validated
2. **Character Data** is complete and accurate
3. **Power Descriptions** are properly extracted from PDFs

---

## Remaining Tasks

### Task 1: Finalize Common Powers Parsing ⏳
**Priority:** High
**Status:** Needs Review

**Current State:**
- `data/common_powers.json` exists with power data
- OCR parsing scripts exist but may need refinement
- Some descriptions may have OCR errors

**Tasks:**
- [ ] Review all power descriptions in `common_powers.json`
- [ ] Verify against PDF source (`traits_booklet.pdf`)
- [ ] Fix any OCR errors
- [ ] Ensure all 4 levels are present for each power
- [ ] Validate statistics calculations are correct
- [ ] Ensure effect descriptions are accurate

**Scripts Available:**
- `scripts/analyze_common_powers_from_pdf.py` - Compare JSON with PDF
- `scripts/analyze_common_powers_quality.py` - Quality analysis
- `scripts/cleanup_and_improve_common_powers.py` - Cleanup tool
- `scripts/fix_remaining_issues.py` - Manual corrections
- `scripts/extract_and_update_common_powers.py` - Extract from PDF

**Files to Review:**
- `data/common_powers.json`
- `data/traits_booklet.pdf`

---

### Task 2: Validate Character Data ⏳
**Priority:** High
**Status:** Needs Review

**Current State:**
- Characters exist in `data/` directory structure
- Some characters may have incomplete data
- Common powers may not be assigned correctly

**Tasks:**
- [ ] Verify all characters have `character.json` files
- [ ] Ensure character names are consistent
- [ ] Verify common powers are correctly assigned
- [ ] Check for missing character data (location, motto, story)
- [ ] Validate special powers are parsed correctly
- [ ] Ensure all seasons have complete character sets

**Scripts Available:**
- `scripts/parse_characters.py` - Parse character images
- `scripts/download_characters.py` - Download and extract data

**Files to Review:**
- `data/season1/*/character.json`
- `data/season2/*/character.json`
- `data/season3/*/character.json`
- `data/season4/*/character.json`
- `data/unknowable-box/*/character.json`
- `data/comic-book-v2/*/character.json`

---

### Task 3: Improve OCR Parsing ⏳
**Priority:** Medium
**Status:** Needs Improvement

**Current State:**
- OCR parsing works but may have errors
- Some patterns may be brittle
- OCR corrections exist but may need expansion

**Tasks:**
- [ ] Review OCR error patterns
- [ ] Expand OCR corrections dictionary
- [ ] Improve image preprocessing
- [ ] Test parsing accuracy
- [ ] Add validation checks

**Scripts Available:**
- `scripts/utils/ocr.py` - OCR utilities
- `scripts/utils/parsing.py` - Parsing utilities
- `scripts/models/ocr_config.py` - OCR settings

**Files to Review:**
- `scripts/data/ocr_corrections.toml`
- `scripts/data/ocr_settings.toml`
- `scripts/data/parsing_patterns.toml`

---

### Task 4: Validate Power Statistics ⏳
**Priority:** Medium
**Status:** Needs Review

**Current State:**
- Power statistics are calculated
- Some calculations may need verification
- Elder sign conversions need validation

**Tasks:**
- [ ] Review all power statistics
- [ ] Verify dice probability calculations
- [ ] Validate elder sign conversion logic
- [ ] Check conditional effects are captured
- [ ] Verify reroll effects are correct
- [ ] Validate healing/defensive effects

**Scripts Available:**
- `scripts/analyze_power_statistics.py` - Calculate statistics
- `scripts/update_common_powers_with_stats.py` - Update JSON with stats
- `scripts/analyze_common_powers_quality.py` - Quality checks

**Files to Review:**
- `data/common_powers.json` (statistics field)

---

## Validation Checklist

### Common Powers
- [ ] All 6 common powers present (Arcane Mastery, Brawling, Marksman, Stealth, Swiftness, Toughness)
- [ ] Each power has 4 levels
- [ ] All descriptions are readable (no major OCR errors)
- [ ] Statistics are calculated for all levels
- [ ] Effect descriptions are accurate
- [ ] Rulebook references are correct

### Character Data
- [ ] All characters have `character.json` files
- [ ] Character names are consistent
- [ ] Common powers are correctly assigned (2 per character)
- [ ] Special powers are parsed (if applicable)
- [ ] Stories are extracted from HTML (where available)
- [ ] Locations and mottos are present (where applicable)

### Parsing Quality
- [ ] OCR accuracy is acceptable (>90%)
- [ ] Power level numbers are correct
- [ ] Dice symbols are recognized correctly
- [ ] Red swirl symbols are recognized
- [ ] Conditional effects are captured
- [ ] Reroll effects are captured
- [ ] Healing effects are captured
- [ ] Defensive effects are captured

---

## Workflow

### Step 1: Review Common Powers
```bash
# Analyze quality
uv run python scripts/analyze_common_powers_quality.py

# Compare with PDF
uv run python scripts/analyze_common_powers_from_pdf.py

# Clean up if needed
uv run python scripts/cleanup_and_improve_common_powers.py --cleanup --recalculate-stats
```

### Step 2: Validate Characters
```bash
# Parse all characters
uv run python scripts/parse_characters.py --data-dir data

# Check for issues
# Review character.json files manually
```

### Step 3: Fix Issues
```bash
# Apply manual corrections
uv run python scripts/fix_remaining_issues.py

# Re-run quality analysis
uv run python scripts/analyze_common_powers_quality.py
```

---

## Success Criteria

- ✅ All common powers have complete, accurate descriptions
- ✅ All characters have complete data files
- ✅ OCR parsing accuracy >90%
- ✅ Power statistics are validated
- ✅ No critical parsing errors
- ✅ All data is consistent and validated

---

**Status:** Planning Phase  
**Last Updated:** 2024-12-19

