#!/usr/bin/env python3
"""
Multi-engine OCR system for iterative refinement.

Tests different preprocessing + OCR engine combinations to find best results.
"""

import sys
from pathlib import Path
from typing import Dict, List

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

try:
    import easyocr
except ImportError:
    easyocr = None

from scripts.models.ocr_settings_config import get_ocr_settings

_ocr_settings = get_ocr_settings()

# Try to import font-aware preprocessing
try:
    from scripts.core.parsing.preprocessing import (
        preprocess_adaptive_font_aware,
        preprocess_for_sans_serif_font,
        preprocess_for_serif_font,
        preprocess_for_small_font,
    )

    FONT_AWARE_AVAILABLE = True
except ImportError:
    FONT_AWARE_AVAILABLE = False


class OCRStrategy:
    """Represents a specific OCR strategy (preprocessing + engine)."""

    def __init__(
        self,
        name: str,
        preprocess_fn,
        ocr_fn,
        description: str = "",
        use_nlp_postprocess: bool = False,
        nlp_level: str = "basic",  # "basic", "advanced", "enhanced"
    ):
        """Initialize OCR strategy.

        Args:
            name: Strategy name
            preprocess_fn: Function(image_path) -> np.ndarray
            ocr_fn: Function(image) -> str
            description: Human-readable description
            use_nlp_postprocess: If True, apply NLP post-processing
            nlp_level: NLP post-processing level ("basic", "advanced", "enhanced")
        """
        self.name = name
        self.preprocess_fn = preprocess_fn
        self.ocr_fn = ocr_fn
        self.description = description or name
        self.use_nlp_postprocess = use_nlp_postprocess
        self.nlp_level = nlp_level

    def extract(self, image_path: Path) -> str:
        """Extract text using this strategy.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        try:
            # Convert to PNG if lossy format (improves OCR accuracy)
            # PNG files are saved alongside originals for reuse (not auto-deleted)
            optimized_path = image_path
            try:
                from scripts.utils.image_conversion import get_ocr_optimized_path

                optimized_path = get_ocr_optimized_path(image_path, use_temp=False)
            except ImportError:
                # Fallback if conversion utility not available
                pass

            processed = self.preprocess_fn(optimized_path)
            text = self.ocr_fn(processed)

            # Apply NLP post-processing if enabled
            if self.use_nlp_postprocess:
                if self.nlp_level == "enhanced":
                    text = ocr_with_enhanced_nlp_postprocess(text)
                elif self.nlp_level == "advanced":
                    text = ocr_with_advanced_nlp_postprocess(text)
                else:  # basic
                    text = ocr_with_nlp_postprocess(text)

            return text.strip()
        except Exception as e:
            print(f"Error in strategy {self.name}: {e}", file=sys.stderr)
            return ""


# Preprocessing functions
def preprocess_basic(image_path: Path) -> np.ndarray:
    """Basic preprocessing: grayscale + OTSU."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess_enhanced(image_path: Path) -> np.ndarray:
    """Enhanced preprocessing: CLAHE + OTSU + denoise."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    return denoised


def preprocess_adaptive(image_path: Path) -> np.ndarray:
    """Adaptive preprocessing: adaptive thresholding."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Adaptive thresholding (better for varying lighting)
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return adaptive


def preprocess_color_enhanced(image_path: Path) -> np.ndarray:
    """Color-enhanced preprocessing: keep color info, enhance contrast."""
    img = cv2.imread(str(image_path))

    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Enhance L channel (lightness)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)

    # Merge back
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    bgr_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(bgr_enhanced, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_deskew(image_path: Path) -> np.ndarray:
    """Deskew preprocessing: rotate to align text."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find angle
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) > 0.5:
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            gray = cv2.warpAffine(
                gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def preprocess_sharpened(image_path: Path) -> np.ndarray:
    """Sharpened preprocessing: unsharp mask + CLAHE + OTSU."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur for unsharp mask
    blurred = cv2.GaussianBlur(gray, (0, 0), 2.0)
    # Unsharp mask: original + (original - blurred) * amount
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return cleaned


def preprocess_bilateral(image_path: Path) -> np.ndarray:
    """Bilateral filter preprocessing: edge-preserving denoising."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Bilateral filter (edge-preserving denoising)
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_bilateral_aggressive(image_path: Path) -> np.ndarray:
    """Aggressive bilateral filter preprocessing: stronger denoising."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Stronger bilateral filter
    filtered = cv2.bilateralFilter(gray, 15, 100, 100)

    # CLAHE with higher clip limit
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Light denoising
    denoised = cv2.fastNlMeansDenoising(binary, None, 5, 7, 21)

    return denoised


def preprocess_bilateral_sharpened(image_path: Path) -> np.ndarray:
    """Bilateral filter + sharpening combination."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Bilateral filter
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Unsharp mask
    blurred = cv2.GaussianBlur(filtered, (0, 0), 1.5)
    sharpened = cv2.addWeighted(filtered, 1.8, blurred, -0.8, 0)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_morphological(image_path: Path) -> np.ndarray:
    """Morphological preprocessing: opening/closing operations."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological opening (removes noise)
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Morphological closing (fills gaps)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    return closed


def preprocess_high_res(image_path: Path) -> np.ndarray:
    """High-resolution preprocessing: upscale + enhance."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale by 2x using INTER_CUBIC (better quality than INTER_LINEAR)
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(upscaled)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 8, 7, 21)

    return denoised


def preprocess_histogram_equalized(image_path: Path) -> np.ndarray:
    """Histogram equalization preprocessing."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Histogram equalization
    equalized = cv2.equalizeHist(gray)

    # OTSU thresholding
    _, binary = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_combined_advanced(image_path: Path) -> np.ndarray:
    """Combined advanced preprocessing: multiple techniques."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Bilateral filter for edge-preserving denoising
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Unsharp mask for sharpening
    blurred = cv2.GaussianBlur(filtered, (0, 0), 2.0)
    sharpened = cv2.addWeighted(filtered, 1.5, blurred, -0.5, 0)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological operations
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Final denoise
    denoised = cv2.fastNlMeansDenoising(cleaned, None, 10, 7, 21)

    return denoised


def preprocess_combined_ultra(image_path: Path) -> np.ndarray:
    """Ultra-combined preprocessing: all best techniques."""
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale 2x for better detail
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    # Bilateral filter (edge-preserving)
    filtered = cv2.bilateralFilter(upscaled, 9, 75, 75)

    # Unsharp mask
    blurred = cv2.GaussianBlur(filtered, (0, 0), 1.5)
    sharpened = cv2.addWeighted(filtered, 1.8, blurred, -0.8, 0)

    # CLAHE with higher clip limit
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological cleanup
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return cleaned


# OCR functions
def ocr_tesseract_psm3(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 3 (automatic)."""
    config = "--oem 3 --psm 3"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm6(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 6 (uniform block)."""
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm7(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 7 (single line)."""
    config = "--oem 3 --psm 7"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm11(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 11 (sparse text)."""
    config = "--oem 3 --psm 11"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm4(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 4 (single column)."""
    config = "--oem 3 --psm 4"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm5(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 5 (single uniform block)."""
    config = "--oem 3 --psm 5"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm8(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 8 (single word)."""
    config = "--oem 3 --psm 8"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm12(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 12 (sparse text with OSD)."""
    config = "--oem 3 --psm 12"
    return pytesseract.image_to_string(image, config=config)


def ocr_tesseract_psm13(image: np.ndarray) -> str:
    """Tesseract OCR with PSM mode 13 (raw line, no OSD)."""
    config = "--oem 3 --psm 13"
    return pytesseract.image_to_string(image, config=config)


def ocr_easyocr(image: np.ndarray) -> str:
    """EasyOCR extraction."""
    if easyocr is None:
        return ""

    # EasyOCR expects BGR image
    if len(image.shape) == 2:
        image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        image_bgr = image

    # Initialize reader (cache it)
    if not hasattr(ocr_easyocr, "_reader"):
        ocr_easyocr._reader = easyocr.Reader(["en"], gpu=False)

    results = ocr_easyocr._reader.readtext(image_bgr)

    # Combine text
    text_parts = [result[1] for result in results]
    return "\n".join(text_parts)


def ocr_with_nlp_postprocess(text: str) -> str:
    """Apply basic NLP-based post-processing to OCR text.

    Uses simple pattern matching and corrections based on common OCR errors.
    """
    from scripts.core.parsing.text import clean_ocr_text

    # Apply standard OCR cleaning
    cleaned = clean_ocr_text(text, preserve_newlines=True)

    # Additional NLP-based corrections
    # Fix common word boundary issues
    corrections = {
        r"\bgoin\b": "gain",
        r"\bgoin g\b": "gaining",
        r"\bsantiy\b": "sanity",
        r"\bwoundndnds\b": "wounds",
        r"\bwoundnds\b": "wounds",
        r"\bwondnds\b": "wounds",
        r"\belder\s+sign\s+sign\b": "elder sign",
        r"\bgreen\s+dice\s+dice\b": "green dice",
        r"\bblack\s+dice\s+dice\b": "black dice",
    }

    import re

    for pattern, replacement in corrections.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned


def ocr_with_advanced_nlp_postprocess(text: str) -> str:
    """Apply advanced NLP-based post-processing to OCR text.

    Uses multiple NLP techniques: spaCy, fuzzy matching, domain dictionaries.
    """
    try:
        from scripts.parsing.nlp_postprocessing import advanced_nlp_postprocess

        return advanced_nlp_postprocess(text)
    except ImportError:
        # Fallback to basic NLP if advanced not available
        return ocr_with_nlp_postprocess(text)


def ocr_with_enhanced_nlp_postprocess(text: str) -> str:
    """Apply enhanced NLP-based post-processing to OCR text.

    Uses all advanced techniques plus aggressive corrections.
    """
    try:
        from scripts.parsing.nlp_postprocessing import enhanced_nlp_postprocess

        return enhanced_nlp_postprocess(text)
    except ImportError:
        # Fallback to advanced NLP if enhanced not available
        return ocr_with_advanced_nlp_postprocess(text)


# Strategy combinations
def get_all_strategies() -> List[OCRStrategy]:
    """Get all OCR strategies to test.

    Returns:
        List of OCRStrategy objects
    """
    strategies = []

    # Tesseract strategies - Basic
    strategies.extend(
        [
            OCRStrategy(
                "tesseract_basic_psm3",
                preprocess_basic,
                ocr_tesseract_psm3,
                "Basic preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm3",
                preprocess_enhanced,
                ocr_tesseract_psm3,
                "Enhanced preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_adaptive_psm3",
                preprocess_adaptive,
                ocr_tesseract_psm3,
                "Adaptive preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_color_psm3",
                preprocess_color_enhanced,
                ocr_tesseract_psm3,
                "Color-enhanced preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_deskew_psm3",
                preprocess_deskew,
                ocr_tesseract_psm3,
                "Deskew preprocessing + Tesseract PSM 3",
            ),
        ]
    )

    # Tesseract strategies - Advanced preprocessing
    strategies.extend(
        [
            OCRStrategy(
                "tesseract_sharpened_psm3",
                preprocess_sharpened,
                ocr_tesseract_psm3,
                "Sharpened preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_bilateral_psm3",
                preprocess_bilateral,
                ocr_tesseract_psm3,
                "Bilateral filter preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_morphological_psm3",
                preprocess_morphological,
                ocr_tesseract_psm3,
                "Morphological preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_high_res_psm3",
                preprocess_high_res,
                ocr_tesseract_psm3,
                "High-resolution preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_histogram_eq_psm3",
                preprocess_histogram_equalized,
                ocr_tesseract_psm3,
                "Histogram equalization + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_combined_advanced_psm3",
                preprocess_combined_advanced,
                ocr_tesseract_psm3,
                "Combined advanced preprocessing + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_bilateral_aggressive_psm3",
                preprocess_bilateral_aggressive,
                ocr_tesseract_psm3,
                "Aggressive bilateral filter + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_bilateral_sharpened_psm3",
                preprocess_bilateral_sharpened,
                ocr_tesseract_psm3,
                "Bilateral + sharpening + Tesseract PSM 3",
            ),
            OCRStrategy(
                "tesseract_combined_ultra_psm3",
                preprocess_combined_ultra,
                ocr_tesseract_psm3,
                "Ultra-combined preprocessing + Tesseract PSM 3",
            ),
        ]
    )

    # Tesseract strategies - Enhanced with NLP post-processing
    strategies.extend(
        [
            OCRStrategy(
                "tesseract_enhanced_psm3_nlp",
                preprocess_enhanced,
                ocr_tesseract_psm3,
                "Enhanced preprocessing + Tesseract PSM 3 + NLP",
                use_nlp_postprocess=True,
            ),
            OCRStrategy(
                "tesseract_sharpened_psm3_nlp",
                preprocess_sharpened,
                ocr_tesseract_psm3,
                "Sharpened preprocessing + Tesseract PSM 3 + NLP",
                use_nlp_postprocess=True,
            ),
            OCRStrategy(
                "tesseract_combined_advanced_psm3_nlp",
                preprocess_combined_advanced,
                ocr_tesseract_psm3,
                "Combined advanced preprocessing + Tesseract PSM 3 + NLP",
                use_nlp_postprocess=True,
            ),
            OCRStrategy(
                "tesseract_bilateral_psm3_nlp",
                preprocess_bilateral,
                ocr_tesseract_psm3,
                "Bilateral filter + Tesseract PSM 3 + NLP",
                use_nlp_postprocess=True,
            ),
            OCRStrategy(
                "tesseract_bilateral_sharpened_psm3_nlp",
                preprocess_bilateral_sharpened,
                ocr_tesseract_psm3,
                "Bilateral + sharpening + Tesseract PSM 3 + NLP",
                use_nlp_postprocess=True,
            ),
            OCRStrategy(
                "tesseract_bilateral_psm3_advanced_nlp",
                preprocess_bilateral,
                ocr_tesseract_psm3,
                "Bilateral filter + Tesseract PSM 3 + Advanced NLP",
                use_nlp_postprocess=True,
                nlp_level="advanced",
            ),
            OCRStrategy(
                "tesseract_bilateral_psm3_enhanced_nlp",
                preprocess_bilateral,
                ocr_tesseract_psm3,
                "Bilateral filter + Tesseract PSM 3 + Enhanced NLP",
                use_nlp_postprocess=True,
                nlp_level="enhanced",
            ),
            OCRStrategy(
                "tesseract_bilateral_sharpened_psm3_enhanced_nlp",
                preprocess_bilateral_sharpened,
                ocr_tesseract_psm3,
                "Bilateral + sharpening + Tesseract PSM 3 + Enhanced NLP",
                use_nlp_postprocess=True,
                nlp_level="enhanced",
            ),
        ]
    )

    # Tesseract strategies - Different PSM modes with enhanced preprocessing
    strategies.extend(
        [
            OCRStrategy(
                "tesseract_enhanced_psm4",
                preprocess_enhanced,
                ocr_tesseract_psm4,
                "Enhanced preprocessing + Tesseract PSM 4",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm5",
                preprocess_enhanced,
                ocr_tesseract_psm5,
                "Enhanced preprocessing + Tesseract PSM 5",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm6",
                preprocess_enhanced,
                ocr_tesseract_psm6,
                "Enhanced preprocessing + Tesseract PSM 6",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm7",
                preprocess_enhanced,
                ocr_tesseract_psm7,
                "Enhanced preprocessing + Tesseract PSM 7",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm8",
                preprocess_enhanced,
                ocr_tesseract_psm8,
                "Enhanced preprocessing + Tesseract PSM 8",
            ),
            OCRStrategy(
                "tesseract_enhanced_psm11",
                preprocess_enhanced,
                ocr_tesseract_psm11,
                "Enhanced preprocessing + Tesseract PSM 11",
            ),
            OCRStrategy(
                "tesseract_sharpened_psm6",
                preprocess_sharpened,
                ocr_tesseract_psm6,
                "Sharpened preprocessing + Tesseract PSM 6",
            ),
            OCRStrategy(
                "tesseract_combined_advanced_psm6",
                preprocess_combined_advanced,
                ocr_tesseract_psm6,
                "Combined advanced preprocessing + Tesseract PSM 6",
            ),
            OCRStrategy(
                "tesseract_bilateral_psm6",
                preprocess_bilateral,
                ocr_tesseract_psm6,
                "Bilateral filter + Tesseract PSM 6",
            ),
            OCRStrategy(
                "tesseract_bilateral_sharpened_psm6",
                preprocess_bilateral_sharpened,
                ocr_tesseract_psm6,
                "Bilateral + sharpening + Tesseract PSM 6",
            ),
        ]
    )

    # Font-aware strategies (if available)
    if FONT_AWARE_AVAILABLE:
        strategies.extend(
            [
                OCRStrategy(
                    "tesseract_serif_font_psm3",
                    preprocess_for_serif_font,
                    ocr_tesseract_psm3,
                    "Serif font preprocessing + Tesseract PSM 3",
                ),
                OCRStrategy(
                    "tesseract_sans_serif_font_psm3",
                    preprocess_for_sans_serif_font,
                    ocr_tesseract_psm3,
                    "Sans-serif font preprocessing + Tesseract PSM 3",
                ),
                OCRStrategy(
                    "tesseract_small_font_psm3",
                    preprocess_for_small_font,
                    ocr_tesseract_psm3,
                    "Small font preprocessing + Tesseract PSM 3",
                ),
                OCRStrategy(
                    "tesseract_adaptive_font_aware_psm3",
                    preprocess_adaptive_font_aware,
                    ocr_tesseract_psm3,
                    "Adaptive font-aware preprocessing + Tesseract PSM 3",
                ),
                OCRStrategy(
                    "tesseract_adaptive_font_aware_psm3_nlp",
                    preprocess_adaptive_font_aware,
                    ocr_tesseract_psm3,
                    "Adaptive font-aware + Tesseract PSM 3 + Enhanced NLP",
                    use_nlp_postprocess=True,
                    nlp_level="enhanced",
                ),
            ]
        )

    # EasyOCR strategies (if available)
    if easyocr is not None:
        strategies.extend(
            [
                OCRStrategy(
                    "easyocr_basic",
                    preprocess_basic,
                    ocr_easyocr,
                    "Basic preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_enhanced",
                    preprocess_enhanced,
                    ocr_easyocr,
                    "Enhanced preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_color",
                    preprocess_color_enhanced,
                    ocr_easyocr,
                    "Color-enhanced preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_sharpened",
                    preprocess_sharpened,
                    ocr_easyocr,
                    "Sharpened preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_bilateral",
                    preprocess_bilateral,
                    ocr_easyocr,
                    "Bilateral filter preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_combined_advanced",
                    preprocess_combined_advanced,
                    ocr_easyocr,
                    "Combined advanced preprocessing + EasyOCR",
                ),
                OCRStrategy(
                    "easyocr_enhanced_nlp",
                    preprocess_enhanced,
                    ocr_easyocr,
                    "Enhanced preprocessing + EasyOCR + NLP",
                    use_nlp_postprocess=True,
                ),
            ]
        )

    return strategies


def test_all_strategies(image_path: Path) -> Dict[str, str]:
    """Test all OCR strategies on an image.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary mapping strategy name to extracted text
    """
    strategies = get_all_strategies()
    results = {}

    for strategy in strategies:
        try:
            text = strategy.extract(image_path)
            results[strategy.name] = text
        except Exception as e:
            print(f"Error testing {strategy.name}: {e}", file=sys.stderr)
            results[strategy.name] = ""

    return results


def combine_results(results: Dict[str, str], method: str = "longest") -> str:
    """Combine multiple OCR results.

    Args:
        results: Dictionary of strategy name -> text
        method: Combination method ("longest", "vote", "merge")

    Returns:
        Combined text
    """
    if not results:
        return ""

    # Filter empty results
    valid_results = {k: v for k, v in results.items() if v.strip()}

    if not valid_results:
        return ""

    if method == "longest":
        # Return longest result (likely most complete)
        return max(valid_results.values(), key=len)

    elif method == "vote":
        # Simple voting: prefer text that appears in multiple results
        # For now, just return longest
        return max(valid_results.values(), key=len)

    elif method == "merge":
        # Merge all results (with deduplication)
        all_text = "\n".join(valid_results.values())
        # Simple deduplication: split by lines, keep unique
        lines = all_text.split("\n")
        seen = set()
        unique_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower and line_lower not in seen:
                seen.add(line_lower)
                unique_lines.append(line)
        return "\n".join(unique_lines)

    return list(valid_results.values())[0]
