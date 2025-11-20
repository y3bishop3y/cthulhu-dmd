#!/usr/bin/env python3
"""
Multi-engine OCR system for iterative refinement.

Tests different preprocessing + OCR engine combinations to find best results.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


class OCRStrategy:
    """Represents a specific OCR strategy (preprocessing + engine)."""

    def __init__(
        self,
        name: str,
        preprocess_fn,
        ocr_fn,
        description: str = "",
    ):
        """Initialize OCR strategy.
        
        Args:
            name: Strategy name
            preprocess_fn: Function(image_path) -> np.ndarray
            ocr_fn: Function(image) -> str
            description: Human-readable description
        """
        self.name = name
        self.preprocess_fn = preprocess_fn
        self.ocr_fn = ocr_fn
        self.description = description or name

    def extract(self, image_path: Path) -> str:
        """Extract text using this strategy.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        try:
            processed = self.preprocess_fn(image_path)
            text = self.ocr_fn(processed)
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


# Strategy combinations
def get_all_strategies() -> List[OCRStrategy]:
    """Get all OCR strategies to test.
    
    Returns:
        List of OCRStrategy objects
    """
    strategies = []
    
    # Tesseract strategies
    strategies.extend([
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
            "tesseract_enhanced_psm11",
            preprocess_enhanced,
            ocr_tesseract_psm11,
            "Enhanced preprocessing + Tesseract PSM 11",
        ),
    ])
    
    # EasyOCR strategies (if available)
    if easyocr is not None:
        strategies.extend([
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
        ])
    
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

