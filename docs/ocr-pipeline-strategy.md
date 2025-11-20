# OCR Pipeline Strategy for Character Card Processing

## Current Problem

We're getting garbled OCR output from character card images, making semantic parsing difficult. The core issue is **image-to-text extraction quality**, not parsing logic.

## Production-Grade Approach (Based on RAG Pipeline Best Practices)

### 1. **Multi-Stage Preprocessing Pipeline**

```
Raw Image → Enhancement → Layout Detection → Region Extraction → OCR → Validation
```

**Key Improvements:**
- **Deskewing**: Rotate images to align text horizontally
- **Despeckling**: Remove noise and artifacts
- **Adaptive Binarization**: Better than OTSU for varied lighting
- **Region Detection**: Isolate text blocks (name, powers, etc.)
- **Resolution Optimization**: Scale to optimal DPI (300 DPI ideal)

### 2. **Multi-Engine OCR Strategy**

Don't rely on a single OCR engine. Use multiple engines and combine results:

**Option A: Multiple Tesseract Configurations**
- Different PSM modes (3, 6, 7, 11, 12)
- Different preprocessing strategies
- Vote/combine best results

**Option B: Multiple OCR Engines**
- Tesseract (current)
- EasyOCR (better for printed text)
- PaddleOCR (good for structured documents)
- Cloud APIs (Google Vision, AWS Textract) for validation

**Option C: Hybrid Approach**
- Use Tesseract for bulk processing
- Use cloud APIs for difficult/problematic images
- Combine results intelligently

### 3. **Layout-Aware Processing**

Character cards have predictable layouts:
- **Top**: Character name
- **Middle**: Special power description
- **Bottom**: Common powers

**Strategy:**
1. Detect card boundaries
2. Extract regions based on known layout
3. Apply region-specific OCR strategies
4. Validate against expected patterns

### 4. **Post-Processing and Validation**

**Text Cleaning:**
- Remove OCR artifacts (@, #, $, etc.)
- Fix common character confusions (O/0, I/1, etc.)
- Normalize whitespace

**Validation:**
- Check against known power names
- Validate against game terminology dictionary
- Use NLP to detect semantic errors

**Correction:**
- Use spell-checking with domain dictionary
- Apply rule-based corrections (common OCR errors)
- Use context-aware corrections (NLP)

### 5. **Iterative Refinement**

Like the RAG pipeline article suggests:
1. **Measure**: Track OCR accuracy per character/image
2. **Identify**: Find problematic images/regions
3. **Refine**: Adjust preprocessing for specific cases
4. **Validate**: Compare against ground truth
5. **Iterate**: Continuous improvement

## Recommended Implementation Plan

### Phase 1: Improve Preprocessing (Current Focus)
- ✅ Deskewing
- ✅ Despeckling  
- ✅ Better binarization
- ⏳ Layout detection
- ⏳ Region-specific processing

### Phase 2: Multi-Engine OCR
- ⏳ Add EasyOCR as alternative
- ⏳ Implement result combination logic
- ⏳ Add cloud API fallback for difficult cases

### Phase 3: Layout-Aware Processing
- ⏳ Train/configure layout detector
- ⏳ Region-specific OCR strategies
- ⏳ Validation against expected patterns

### Phase 4: Advanced Post-Processing
- ⏳ Domain-specific spell checking
- ⏳ Context-aware corrections
- ⏳ NLP-based validation

## Immediate Next Steps

1. **Test current advanced pipeline** on Ahmed and Adam
2. **Compare results** with original OCR
3. **Identify specific failure modes** (what text is garbled?)
4. **Add EasyOCR** as alternative engine
5. **Implement result combination** logic

## Key Insight from RAG Pipeline Article

The article emphasizes **iterative refinement** and **measuring what matters**. For us:
- **Measure**: OCR accuracy per character/image
- **Identify**: Which preprocessing steps help most
- **Refine**: Adjust pipeline based on results
- **Validate**: Compare against known correct text

We should build a **test harness** that:
1. Runs OCR with different configurations
2. Compares against known correct text (Ahmed's corrected descriptions)
3. Scores accuracy
4. Identifies best configuration per image type

