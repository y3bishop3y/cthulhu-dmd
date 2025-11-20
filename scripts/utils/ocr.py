#!/usr/bin/env python3
"""
Shared OCR utilities for image preprocessing and text extraction.

This module provides common OCR functions used across parsing scripts.
"""

import sys
from pathlib import Path
from typing import Final, Optional

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install opencv-python pytesseract pillow\n"
        "Also install Tesseract OCR:\n"
        "  macOS: brew install tesseract\n"
        "  Linux: sudo apt-get install tesseract-ocr\n",
        file=sys.stderr,
    )
    raise

from scripts.models.ocr_settings_config import get_ocr_settings

# Load OCR settings from TOML config
_ocr_settings = get_ocr_settings()
DEFAULT_PSM_MODE: Final[int] = _ocr_settings.ocr_tesseract_default_psm_mode
DEFAULT_OEM_MODE: Final[int] = _ocr_settings.ocr_tesseract_default_oem_mode


def preprocess_image_for_ocr(
    image_path: Path,
    enhance_contrast: Optional[bool] = None,
    denoise_strength: Optional[int] = None,
) -> np.ndarray:
    """Preprocess image to improve OCR accuracy.
    
    This function applies an enhanced preprocessing pipeline:
    1. Convert to grayscale
    2. Apply contrast enhancement (optional, defaults to TOML config)
    3. Apply thresholding (OTSU)
    4. Denoise with configurable strength (defaults to TOML config)
    
    Args:
        image_path: Path to image file
        enhance_contrast: If True, apply CLAHE contrast enhancement (defaults to TOML config)
        denoise_strength: Denoising strength (higher = more aggressive, defaults to TOML config)
        
    Returns:
        Preprocessed image as numpy array
        
    Raises:
        ValueError: If image cannot be read
    """
    # Use TOML config defaults if not provided
    if enhance_contrast is None:
        enhance_contrast = _ocr_settings.ocr_preprocessing_enhance_contrast
    if denoise_strength is None:
        denoise_strength = _ocr_settings.ocr_preprocessing_denoise_strength

    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Optional: Apply contrast enhancement using CLAHE
    if enhance_contrast:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    # Apply thresholding to get binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Apply denoising with configurable strength
    denoised = cv2.fastNlMeansDenoising(thresh, None, denoise_strength, 7, 21)

    return denoised


def extract_text_from_image(
    image_path: Path,
    psm_mode: int = DEFAULT_PSM_MODE,
    oem_mode: int = DEFAULT_OEM_MODE,
    enhance_contrast: bool = True,
    denoise_strength: int = 10,
) -> str:
    """Extract text from image using OCR.
    
    Args:
        image_path: Path to image file
        psm_mode: Page segmentation mode (default: 3 for automatic)
        oem_mode: OCR engine mode (default: 3 for default)
        enhance_contrast: If True, apply contrast enhancement before OCR
        denoise_strength: Denoising strength (higher = more aggressive)
        
    Returns:
        Extracted text as string
        
    Raises:
        ValueError: If image cannot be read or processed
    """
    try:
        # Preprocess image with enhanced settings
        processed_img = preprocess_image_for_ocr(
            image_path, enhance_contrast=enhance_contrast, denoise_strength=denoise_strength
        )

        # Use pytesseract to extract text
        custom_config = f"--oem {oem_mode} --psm {psm_mode}"
        text: str = pytesseract.image_to_string(processed_img, config=custom_config)

        return text.strip()
    except Exception as e:
        raise ValueError(f"Error extracting text from {image_path}: {e}") from e


def extract_text_from_image_region(
    image_path: Path,
    x: int,
    y: int,
    width: int,
    height: int,
    psm_mode: int = DEFAULT_PSM_MODE,
) -> str:
    """Extract text from a specific region of an image.
    
    Useful for extracting text from specific card sections.
    
    Args:
        image_path: Path to image file
        x: X coordinate of region start
        y: Y coordinate of region start
        width: Width of region
        height: Height of region
        psm_mode: Page segmentation mode
        
    Returns:
        Extracted text from region
    """
    # Read and preprocess full image
    processed_img = preprocess_image_for_ocr(image_path)
    
    # Extract region
    region = processed_img[y : y + height, x : x + width]
    
    # Extract text from region
    custom_config = f"--oem {DEFAULT_OEM_MODE} --psm {psm_mode}"
    text: str = pytesseract.image_to_string(region, config=custom_config)
    
    return text.strip()

