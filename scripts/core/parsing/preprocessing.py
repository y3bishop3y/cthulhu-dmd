#!/usr/bin/env python3
"""
Font-aware preprocessing for OCR.

Different fonts require different preprocessing strategies:
- Serif fonts: May need different sharpening
- Sans-serif fonts: May need different contrast
- Decorative fonts: May need aggressive preprocessing
- Small fonts: May need upscaling
"""

import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def detect_font_characteristics(image: np.ndarray) -> dict:
    """Detect font characteristics from image.

    Returns:
        Dictionary with font characteristics:
        - is_serif: bool (estimated)
        - font_size: str ('small', 'medium', 'large')
        - contrast: float (0-1)
        - stroke_width: float (estimated)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Estimate contrast
    contrast = np.std(gray) / 255.0

    # Estimate font size (based on text region height)
    # Use edge detection to find text regions
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    heights = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h > 5 and h < 100:  # Reasonable text height range
            heights.append(h)

    avg_height = np.mean(heights) if heights else 20
    if avg_height < 15:
        font_size = "small"
    elif avg_height < 25:
        font_size = "medium"
    else:
        font_size = "large"

    # Estimate serif (simplified - check for serif-like features)
    # Serif fonts tend to have more variation in stroke width
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # Count transitions (serif fonts have more transitions)
    transitions = np.sum(np.diff(binary, axis=1) != 0)
    is_serif = transitions > (gray.shape[0] * gray.shape[1] * 0.1)

    return {
        "is_serif": is_serif,
        "font_size": font_size,
        "contrast": contrast,
        "avg_height": avg_height,
    }


def preprocess_for_serif_font(image_path: Path) -> np.ndarray:
    """Preprocessing optimized for serif fonts.

    Serif fonts benefit from:
    - Less aggressive sharpening (preserve serif details)
    - Moderate contrast enhancement
    - Bilateral filtering to preserve edges
    """
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Bilateral filter (preserve serif details)
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Moderate CLAHE (don't over-enhance)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_for_sans_serif_font(image_path: Path) -> np.ndarray:
    """Preprocessing optimized for sans-serif fonts.

    Sans-serif fonts benefit from:
    - More aggressive sharpening
    - Higher contrast enhancement
    - Cleaner edges
    """
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Unsharp mask for sharpening
    blurred = cv2.GaussianBlur(gray, (0, 0), 1.5)
    sharpened = cv2.addWeighted(gray, 1.8, blurred, -0.8, 0)

    # Higher CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological cleanup
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return cleaned


def preprocess_for_small_font(image_path: Path) -> np.ndarray:
    """Preprocessing optimized for small fonts.

    Small fonts benefit from:
    - Upscaling (2x or 3x)
    - Aggressive sharpening
    - High contrast
    """
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale 3x for small fonts
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

    # Aggressive sharpening
    blurred = cv2.GaussianBlur(upscaled, (0, 0), 1.0)
    sharpened = cv2.addWeighted(upscaled, 2.0, blurred, -1.0, 0)

    # High contrast CLAHE
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)

    # OTSU thresholding
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def preprocess_adaptive_font_aware(image_path: Path) -> np.ndarray:
    """Adaptive preprocessing based on detected font characteristics."""
    img = cv2.imread(str(image_path))

    # Detect font characteristics
    characteristics = detect_font_characteristics(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Choose preprocessing based on characteristics
    if characteristics["font_size"] == "small":
        # Use small font preprocessing
        h, w = gray.shape
        upscaled = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(upscaled, (0, 0), 1.0)
        sharpened = cv2.addWeighted(upscaled, 2.0, blurred, -1.0, 0)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif characteristics["is_serif"]:
        # Use serif font preprocessing
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    else:
        # Use sans-serif font preprocessing
        blurred = cv2.GaussianBlur(gray, (0, 0), 1.5)
        sharpened = cv2.addWeighted(gray, 1.8, blurred, -0.8, 0)
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned
