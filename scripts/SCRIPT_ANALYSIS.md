# Script Analysis and Cleanup Plan

## Core Scraping/Downloading Scripts (KEEP)

1. **`download_characters.py`** ✅
   - Downloads character images and HTML stories from website
   - Core functionality: web scraping
   - Status: KEEP

2. **`download_rulebook.py`** ✅
   - Downloads rulebook PDF
   - Core functionality: PDF download
   - Status: KEEP

3. **`parse_characters.py`** ✅
   - Parses character card images using OCR
   - Core functionality: OCR parsing
   - Status: KEEP (needs refactoring to use utils)

4. **`parse_rulebook.py`** ✅
   - Parses rulebook PDF into structured markdown
   - Core functionality: PDF parsing
   - Status: KEEP

5. **`parse_trait_character_assignments.py`** ✅
   - Parses PDF to extract character-trait mappings
   - Core functionality: PDF parsing for verification
   - Status: KEEP

## Power Analysis Scripts (KEEP, consolidate)

6. **`analyze_power_statistics.py`** ✅
   - Analyzes power statistics and calculates dice impact
   - Core functionality: statistics calculation
   - Status: KEEP (core model)

7. **`extract_and_update_common_powers.py`** ✅
   - Extracts common powers from OCR of character cards
   - Core functionality: OCR extraction
   - Status: KEEP (consolidate with parse_characters.py)

8. **`update_common_powers_with_stats.py`** ✅
   - Updates common_powers.json with calculated statistics
   - Core functionality: data update
   - Status: KEEP (could be integrated into analyze_power_statistics.py)

## Scripts to DELETE (one-time use or redundant)

9. **`convert_to_webp.py`** ❌ DELETE
   - Converts JPEG to WebP
   - Status: One-time conversion already done

10. **`convert_to_webp_demo.py`** ❌ DELETE
    - Demo script for WebP conversion
    - Status: Demo script, no longer needed

11. **`create_common_powers.py`** ❌ DELETE
    - Creates initial common_powers.json
    - Status: One-time initialization, already done

12. **`improve_common_powers_extraction.py`** ❌ DELETE
    - Older version of common powers extraction
    - Status: Redundant with extract_and_update_common_powers.py

13. **`parse_common_powers_from_booklet.py`** ❌ DELETE
    - Attempts to parse PDF for common powers (didn't work well)
    - Status: Redundant, PDF structure not suitable

14. **`parse_traits_booklet.py`** ❌ DELETE
    - Parses traits booklet PDF
    - Status: Similar to parse_common_powers_from_booklet.py, redundant

15. **`update_stories_from_files.py`** ❌ DELETE
    - Syncs story.txt with character.json
    - Status: One-time sync script, functionality in download_characters.py

16. **`update_speaker_metadata.py`** ❌ DELETE
    - Updates TTS speaker metadata
    - Status: One-time metadata update, already done

17. **`review_all_powers.py`** ❌ DELETE
    - Reviews all powers (utility script)
    - Status: Can be integrated into analyze_power_statistics.py

## Utility Scripts (KEEP)

18. **`read_story.py`** ✅
    - TTS for character stories
    - Status: KEEP (useful utility, not core scraping)

19. **`test_parsing_improvements.py`** ✅
    - Test script for parsing improvements
    - Status: KEEP (move to tests/ directory)

## Refactoring Plan

### Phase 1: Delete redundant scripts
- Remove all scripts marked ❌ DELETE

### Phase 2: Consolidate common functionality
- Extract OCR preprocessing to `utils/ocr.py`
- Extract PDF parsing utilities to `utils/pdf.py`
- Extract web scraping utilities to `utils/web.py`
- Create shared models in `models/` for:
  - Character data
  - Power data
  - PDF parsing results

### Phase 3: Refactor scripts to use utils/models
- `parse_characters.py` → use `utils/parsing.py` and `utils/ocr.py`
- `extract_and_update_common_powers.py` → consolidate with `parse_characters.py`
- `download_characters.py` → use `utils/web.py`
- `parse_rulebook.py` → use `utils/pdf.py`
- `parse_trait_character_assignments.py` → use `utils/pdf.py`

### Phase 4: Integrate related scripts
- Merge `update_common_powers_with_stats.py` into `analyze_power_statistics.py`
- Add review functionality to `analyze_power_statistics.py`

