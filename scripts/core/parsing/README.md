# Parsing Module

This directory contains all parsing-related code for extracting and analyzing text from character card images.

## Overview

The parsing module provides:
- **Multi-engine OCR**: Test different OCR engines (Tesseract, EasyOCR) with various preprocessing strategies
- **NLP Analysis**: Extract semantic meaning from OCR text using spaCy
- **Text Processing**: Clean and normalize OCR text, extract structured data
- **Comparison Tools**: Compare OCR results against ground truth

## Structure

```
scripts/parsing/
├── README.md                    # This file
├── __init__.py                  # Package exports
├── multi_ocr.py                 # Multi-engine OCR strategies
├── advanced_ocr.py              # Advanced preprocessing pipeline
├── nlp_parser.py                # NLP-based semantic extraction
├── text_parsing.py              # Text cleaning and normalization utilities
├── parse_characters.py          # CLI: Parse character card images
├── parse_special_powers.py      # CLI: Parse special powers from back cards
├── parse_trait_character_assignments.py  # CLI: Parse trait assignments from PDF
├── parse_rulebook.py            # CLI: Parse rulebook PDF
└── analyze_ocr_with_nlp.py      # CLI: NLP analysis of OCR output
```

## Modules

### `multi_ocr.py`

Multi-engine OCR system that tests different preprocessing + OCR engine combinations.

**Key Features**:
- 11+ preprocessing strategies (basic, enhanced, adaptive, color-enhanced, deskew)
- Multiple OCR engines (Tesseract with different PSM modes, EasyOCR)
- Result combination strategies
- Strategy scoring and comparison

**Usage**:
```python
from scripts.core.parsing.ocr_engines import get_all_strategies, test_all_strategies

# Get all available strategies
strategies = get_all_strategies()

# Test all strategies on an image
results = test_all_strategies(image_path)
```

### `advanced_ocr.py`

Advanced OCR pipeline with layout analysis and multi-strategy extraction.

**Key Features**:
- Text region detection
- Deskewing and despeckling
- Multi-PSM mode testing
- Intelligent result combination

**Usage**:
```python
from scripts.core.parsing.ocr import extract_text_advanced

# Extract text with advanced pipeline
text = extract_text_advanced(image_path, use_regions=True, deskew=True)
```

### `nlp_parser.py`

NLP-based parser for extracting semantic meaning from OCR text.

**Key Features**:
- Healing information extraction (stress, wounds, OR/AND logic)
- Power level parsing
- Semantic concept extraction
- Handles garbled OCR text

**Usage**:
```python
from scripts.core.parsing.nlp import extract_healing_info, get_nlp_model

nlp = get_nlp_model()
doc = nlp("At the end of your turn, you may heal 1 stress OR wound")
info = extract_healing_info(doc)
# Returns: {"has_healing": True, "stress_healed": 1, "wounds_healed": 1, "has_or": True, ...}
```

### `text_parsing.py`

Text cleaning and normalization utilities for OCR output.

**Key Features**:
- OCR error correction
- Dice symbol normalization
- Power level pattern matching
- Text cleaning and artifact removal

**Usage**:
```python
from scripts.core.parsing.text import clean_ocr_text, normalize_dice_symbols

# Clean OCR text
cleaned = clean_ocr_text(raw_ocr_text, preserve_symbols=True)

# Normalize dice symbols
normalized = normalize_dice_symbols(text)
```

### `analyze_ocr_with_nlp.py`

CLI tool for analyzing OCR output with NLP to extract semantic meaning.

**Usage**:
```bash
# Analyze OCR output with NLP
uv run python scripts/parsing/analyze_ocr_with_nlp.py --character adam

# Test specific OCR strategy
uv run python scripts/parsing/analyze_ocr_with_nlp.py --character ahmed --strategy tesseract_deskew_psm3
```

## OCR Strategies

### Preprocessing Strategies

1. **Basic**: Grayscale + OTSU thresholding
2. **Enhanced**: CLAHE contrast enhancement + denoising
3. **Adaptive**: Adaptive thresholding for varying lighting
4. **Color-enhanced**: LAB color space enhancement
5. **Deskew**: Rotate image to align text horizontally

### OCR Engines

1. **Tesseract PSM 3**: Fully automatic page segmentation
2. **Tesseract PSM 6**: Uniform block of text
3. **Tesseract PSM 7**: Single text line
4. **Tesseract PSM 11**: Sparse text
5. **EasyOCR**: Deep learning-based OCR

### Best Results

- **Ahmed**: Deskew + Tesseract PSM 3 (35% similarity)
- **Adam**: Basic + Tesseract PSM 3 (5.5% similarity)

*Note: Different images may need different strategies*

## Testing

Run unit tests:
```bash
uv run pytest scripts/tests/unit/test_nlp_ocr_analysis.py -v
```

## CLI Scripts

### `parse_characters.py`

Parse character card images to extract character data.

**Usage**:
```bash
# Parse single character
uv run python scripts/parsing/parse_characters.py --character adam

# Parse all characters
uv run python scripts/parsing/parse_characters.py --data-dir data
```

**Extracts**:
- Name, location, motto, story from front card
- Special power and common powers from back card
- Merges with existing character.json data

### `parse_special_powers.py`

Parse and update special powers for characters.

**Usage**:
```bash
# Parse special powers for all characters
uv run python scripts/parsing/parse_special_powers.py

# Parse specific character
uv run python scripts/parsing/parse_special_powers.py --character ahmed --season season1
```

**Features**:
- Extracts special power descriptions from back cards
- Updates character.json files
- Validates and cleans OCR text

### `parse_trait_character_assignments.py`

Parse PDF to extract which characters have which common traits.

**Usage**:
```bash
uv run python scripts/parsing/parse_trait_character_assignments.py
```

**Output**: Character-trait assignments JSON

### `parse_rulebook.py`

Parse rulebook PDF into structured markdown/text.

**Usage**:
```bash
uv run python scripts/parsing/parse_rulebook.py --output-format markdown
```

## Related Scripts (in scripts/ root)

- `scripts/compare_ocr_results.py`: Compare OCR results side-by-side with ground truth
- `scripts/iterate_ocr_strategies.py`: Test all OCR strategies and find best ones
- `scripts/test_ocr_pipeline.py`: Basic OCR pipeline testing

## Dependencies

- `spacy`: NLP processing
- `pytesseract`: Tesseract OCR
- `easyocr`: EasyOCR engine
- `opencv-python`: Image preprocessing
- `numpy`: Image processing

## Future Improvements

- [ ] Add PaddleOCR support
- [ ] Cloud OCR API integration (Google Vision, AWS Textract)
- [ ] Super-resolution preprocessing
- [ ] Region-specific preprocessing
- [ ] Machine learning-based OCR error correction
- [ ] Layout-aware text extraction

## See Also

- `memory-bank/tasks/07-ocr-iteration-strategy.md`: Comprehensive OCR strategy plan
- `docs/ocr-pipeline-strategy.md`: OCR pipeline documentation

