# OCR Integration Issue: Benchmark vs Production

## Problem

The benchmark found optimal OCR strategies with high scores (85-100%), but the actual parsing results are much worse. This is because:

### Current Implementation Gap

1. **Benchmark Approach**: Tests whole-card extraction with different strategies, then scores individual fields after parsing
2. **Production Code**: Extracts whole card with ONE strategy (optimized for story), then parses all fields from that text
3. **Missing**: Field-specific extraction with optimal strategies per field

### The Issue

The benchmark found:
- **Name**: `tesseract_bilateral_psm3` (100% score)
- **Location**: `tesseract_bilateral_psm3` (100% score)  
- **Motto**: `tesseract_bilateral_psm3` (95.8% score)
- **Story**: `tesseract_enhanced_psm3` (99.8% score)
- **Special Power**: `tesseract_bilateral_psm3` (85.2% score)

But the production code uses:
- **Front card**: `tesseract_enhanced_psm3` (optimized for story only)
- **Back card**: `tesseract_bilateral_psm3` (optimized for special power only)

### Why This Fails

1. **Different preprocessing needs**: Story is white text on black background, name/location are black on light background
2. **Single strategy limitation**: One preprocessing approach can't optimize for all field types
3. **Parsing from suboptimal text**: If name/location extraction is poor, parsing can't recover

## Solution: Field-Specific Extraction

We need to implement layout-aware extraction with field-specific optimal strategies:

### Approach 1: Layout-Aware + Optimal Strategies (Recommended)

1. Use `CardLayoutExtractor` to identify field regions
2. Extract each field region separately with its optimal strategy:
   - Name region → `tesseract_bilateral_psm3`
   - Location region → `tesseract_bilateral_psm3`
   - Motto region → `tesseract_bilateral_psm3`
   - Story region → `tesseract_enhanced_psm3` (needs white-on-black preprocessing)
3. Combine results into `CharacterData`

### Approach 2: Multi-Strategy Extraction + Voting

1. Extract whole card with multiple optimal strategies
2. Parse each extraction separately
3. Vote/combine best results per field

### Approach 3: Hybrid Layout + Whole Card

1. Extract name/location/motto using layout-aware + optimal strategies
2. Extract story using whole-card with story-optimized strategy
3. Combine results

## Implementation Plan

### Phase 1: Field-Specific Extraction Function

Create `extract_front_card_fields_with_optimal_strategies()` that:
- Uses layout detection to find regions
- Applies optimal strategy per field
- Returns structured `FrontCardData`

### Phase 2: Update Parsing Code

Modify `parse_character_images()` to:
- Use field-specific extraction when `use_optimal_strategies=True`
- Fall back to whole-card extraction if layout detection fails

### Phase 3: Benchmark Field-Specific Approach

Re-run benchmark with field-specific extraction to verify improvement

## Current Status

- ✅ Optimal strategies config exists (`scripts/data/optimal_ocr_strategies.json`)
- ✅ Layout-aware extraction code exists (`scripts/core/parsing/layout.py`)
- ✅ Benchmark found optimal strategies
- ❌ Field-specific extraction not implemented
- ❌ Layout-aware extraction not integrated with optimal strategies
- ❌ Production code uses whole-card extraction only

## Next Steps

1. Implement field-specific extraction function
2. Integrate with `parse_character_images()`
3. Test on season2 characters
4. Compare results with current approach

