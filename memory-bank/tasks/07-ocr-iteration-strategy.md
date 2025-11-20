# OCR Iteration Strategy Plan

## Goal

Systematically test and compare different OCR preprocessing + engine combinations to find the best approach for extracting text from character card images.

## Current Problem

- **Low OCR accuracy**: ~15-35% similarity with ground truth
- **Garbled text**: OCR artifacts, missing words, character confusion
- **Inconsistent results**: Different preprocessing strategies yield different outputs

## Strategy: Iterative Testing & Comparison

### Phase 1: Multi-Strategy Testing (Current)

**Status**: ✅ Implemented

**What we're doing**:
- Testing 11+ different preprocessing + OCR engine combinations
- Comparing results against ground truth (character.json)
- Scoring strategies by similarity and key phrase detection

**Current Results** (Ahmed's back card):
- **Best**: Deskew preprocessing + Tesseract PSM 3 (35.14% similarity)
- **Key Phrases Found**: 6/6 (heal, stress, wound, investigator, instead, end of your turn)
- **Score**: 0.651

**Strategies Tested**:
1. Basic preprocessing + Tesseract PSM 3
2. Enhanced preprocessing (CLAHE + denoise) + Tesseract PSM 3
3. Adaptive preprocessing + Tesseract PSM 3
4. Color-enhanced preprocessing + Tesseract PSM 3
5. Deskew preprocessing + Tesseract PSM 3 ⭐ **Best**
6. Enhanced + Tesseract PSM 6
7. Enhanced + Tesseract PSM 7
8. Enhanced + Tesseract PSM 11
9. Basic + EasyOCR
10. Enhanced + EasyOCR
11. Color-enhanced + EasyOCR

### Phase 2: Additional OCR Engines

**Status**: ⏳ Planned

**Engines to Test**:

1. **PaddleOCR**
   - Good for structured documents
   - Better Chinese/English mixed text
   - Installation: `pip install paddlepaddle paddleocr`

2. **Google Cloud Vision API**
   - High accuracy
   - Requires API key
   - Cost: ~$1.50 per 1,000 images
   - Best for validation/fallback

3. **AWS Textract**
   - Good for structured documents
   - Requires AWS account
   - Cost: ~$1.50 per 1,000 pages
   - Best for production fallback

4. **Azure Computer Vision**
   - Good OCR accuracy
   - Requires Azure account
   - Cost: ~$1.00 per 1,000 transactions

5. **Tesseract 5.x** (if available)
   - Newer version may have improvements
   - Check if newer than current version

### Phase 3: Advanced Preprocessing

**Status**: ⏳ Planned

**Techniques to Test**:

1. **Super-resolution**
   - Upscale images before OCR
   - May improve accuracy for small text
   - Tools: ESRGAN, Real-ESRGAN

2. **Region-specific preprocessing**
   - Different preprocessing for different card regions
   - Name region: different strategy than power description
   - Layout-aware processing

3. **Multi-scale processing**
   - Process at different resolutions
   - Combine results

4. **Color space optimization**
   - Test LAB, HSV, YUV color spaces
   - Find best for character cards

5. **Morphological operations**
   - Dilation/erosion to connect broken characters
   - May help with OCR artifacts

### Phase 4: Result Combination Strategies

**Status**: ⏳ Planned

**Combination Methods**:

1. **Voting**
   - Majority vote on words/phrases
   - Weight by confidence scores

2. **Confidence-based selection**
   - Use OCR confidence scores
   - Select highest confidence words

3. **Hybrid approach**
   - Use best engine for each region
   - Combine region results

4. **NLP-based validation**
   - Use spaCy to validate extracted text
   - Fix common OCR errors automatically

### Phase 5: Post-Processing & Correction

**Status**: ⏳ Planned

**Correction Strategies**:

1. **Domain-specific spell checking**
   - Game terminology dictionary
   - Power names, action names

2. **Context-aware correction**
   - Use NLP to understand context
   - Fix semantic errors

3. **Rule-based corrections**
   - Common OCR errors (O/0, I/1, etc.)
   - Pattern-based fixes

4. **Machine learning correction**
   - Train model on OCR errors
   - Learn from corrections

## Testing Framework

### Current Implementation

**Script**: `scripts/iterate_ocr_strategies.py`

**Features**:
- Tests all strategies automatically
- Compares against ground truth
- Scores by similarity + key phrase detection
- Shows top N results
- Tests combination strategies

**Usage**:
```bash
# Test single character
uv run python scripts/iterate_ocr_strategies.py --character ahmed --top-n 10

# Test with combination
uv run python scripts/iterate_ocr_strategies.py --character ahmed --combine
```

### Metrics We Track

1. **Similarity Score**: Word overlap (Jaccard similarity)
2. **Key Phrase Count**: How many important phrases found
3. **Text Length**: Completeness indicator
4. **Combined Score**: Similarity + phrase bonus

### Ground Truth Source

- **File**: `data/season1/{character}/character.json`
- **Fields**: `special_power.levels[].description`
- **Characters with ground truth**: Ahmed (all 4 levels), Adam (all 4 levels)

## Implementation Plan

### Step 1: Expand Current Testing ✅

- [x] Create multi-strategy testing framework
- [x] Add EasyOCR support
- [x] Implement scoring system
- [x] Test on Ahmed

### Step 2: Test on More Characters

- [ ] Test on Adam (has ground truth)
- [ ] Test on other season1 characters
- [ ] Build ground truth for more characters
- [ ] Identify patterns (which strategies work for which image types)

### Step 3: Add More OCR Engines

- [ ] Add PaddleOCR
- [ ] Add Google Cloud Vision API (optional, requires API key)
- [ ] Add AWS Textract (optional, requires AWS account)
- [ ] Compare results across all engines

### Step 4: Advanced Preprocessing

- [ ] Test super-resolution
- [ ] Implement region-specific preprocessing
- [ ] Test multi-scale processing
- [ ] Optimize color space selection

### Step 5: Result Combination

- [ ] Implement voting strategy
- [ ] Implement confidence-based selection
- [ ] Test hybrid approaches
- [ ] Measure improvement from combination

### Step 6: Post-Processing

- [ ] Build domain-specific dictionary
- [ ] Implement context-aware correction
- [ ] Add rule-based corrections
- [ ] Measure improvement from correction

## Success Criteria

### Short-term (Phase 1-2)
- [ ] Achieve >50% similarity with ground truth
- [ ] Extract all key phrases correctly
- [ ] Identify best strategy per character/image type

### Medium-term (Phase 3-4)
- [ ] Achieve >70% similarity with ground truth
- [ ] Automatically combine results from multiple engines
- [ ] Reduce manual correction needed

### Long-term (Phase 5-6)
- [ ] Achieve >85% similarity with ground truth
- [ ] Fully automated extraction with minimal errors
- [ ] Production-ready pipeline

## Next Actions

1. **Immediate**: Test current best strategy (Deskew + Tesseract PSM 3) on Adam
2. **Short-term**: Add PaddleOCR and compare results
3. **Medium-term**: Implement result combination strategies
4. **Long-term**: Build production pipeline with fallback to cloud APIs

## Files Created

- `scripts/utils/multi_ocr.py`: Multi-engine OCR system
- `scripts/iterate_ocr_strategies.py`: Testing and comparison tool
- `scripts/utils/advanced_ocr.py`: Advanced preprocessing pipeline
- `scripts/test_ocr_pipeline.py`: Basic comparison tool
- `docs/ocr-pipeline-strategy.md`: Strategy documentation

## Notes

- **Current best**: Deskew preprocessing + Tesseract PSM 3 (35% similarity)
- **EasyOCR**: Not significantly better than Tesseract for these images
- **Key insight**: Deskewing helps significantly (text alignment matters)
- **Next step**: Test PaddleOCR, then consider cloud APIs for difficult cases

## References

- RAG Pipeline Article: Iterative refinement approach
- OCR Best Practices: Preprocessing, multi-engine, validation
- Production OCR: Cloud APIs for difficult cases, local engines for bulk

