#!/usr/bin/env python3
"""
Image preprocessing utilities for animation generation.

This module provides helper functions for image manipulation, enhancement,
and format conversion used across animation scripts.
"""

import sys
from pathlib import Path
from typing import Final, Optional

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install opencv-python pillow numpy\n",
        file=sys.stderr,
    )
    raise

# Constants
DEFAULT_UPSCALE_FACTOR: Final[int] = 2
DEFAULT_QUALITY: Final[int] = 95

# File extension constants
EXT_JPG: Final[str] = ".jpg"
EXT_JPEG: Final[str] = ".jpeg"
EXT_PNG: Final[str] = ".png"
EXT_WEBP: Final[str] = ".webp"

# Image format constants
FORMAT_JPEG: Final[str] = "JPEG"
FORMAT_PNG: Final[str] = "PNG"
FORMAT_WEBP: Final[str] = "WEBP"
MODE_RGB: Final[str] = "RGB"
MODE_RGBA: Final[str] = "RGBA"


def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    """Enhance image contrast using CLAHE.

    Args:
        image: Input image as numpy array (grayscale or BGR)
        clip_limit: CLAHE clip limit (higher = more contrast)
        tile_size: Tile grid size for CLAHE

    Returns:
        Enhanced image as numpy array
    """
    if len(image.shape) == 2:
        # Grayscale
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        return clahe.apply(image)
    else:
        # Color image - apply to each channel
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lightness, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        lightness = clahe.apply(lightness)
        lab = cv2.merge([lightness, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def denoise_image(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """Remove noise from image.

    Args:
        image: Input image as numpy array
        strength: Denoising strength (higher = more aggressive)

    Returns:
        Denoised image as numpy array
    """
    if len(image.shape) == 2:
        # Grayscale
        return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
    else:
        # Color
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)


def resize_image(
    image: Image.Image,
    target_size: Optional[tuple[int, int]] = None,
    scale_factor: Optional[float] = None,
) -> Image.Image:
    """Resize image maintaining aspect ratio.

    Args:
        image: PIL Image to resize
        target_size: Target (width, height) - one dimension can be None to maintain aspect ratio
        scale_factor: Scale factor (e.g., 2.0 for 2x upscale)

    Returns:
        Resized PIL Image
    """
    if target_size:
        return image.resize(target_size, Image.Resampling.LANCZOS)
    elif scale_factor:
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        return image.resize(new_size, Image.Resampling.LANCZOS)
    else:
        return image


def pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format (BGR).

    Args:
        image: PIL Image (RGB)

    Returns:
        OpenCV image (BGR) as numpy array
    """
    # Convert PIL RGB to OpenCV BGR
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    """Convert OpenCV image (BGR) to PIL Image (RGB).

    Args:
        image: OpenCV image (BGR) as numpy array

    Returns:
        PIL Image (RGB)
    """
    # Convert OpenCV BGR to PIL RGB
    if len(image.shape) == 2:
        # Grayscale
        return Image.fromarray(image)
    else:
        # Color
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is in RGB mode.

    Args:
        image: PIL Image

    Returns:
        PIL Image in RGB mode
    """
    if image.mode != MODE_RGB:
        return image.convert(MODE_RGB)
    return image


def ensure_rgba(image: Image.Image) -> Image.Image:
    """Ensure image is in RGBA mode (with alpha channel).

    Args:
        image: PIL Image

    Returns:
        PIL Image in RGBA mode
    """
    if image.mode != MODE_RGBA:
        return image.convert(MODE_RGBA)
    return image


def save_image(image: Image.Image, output_path: Path, quality: int = DEFAULT_QUALITY) -> None:
    """Save PIL Image to file with appropriate format.

    Args:
        image: PIL Image to save
        output_path: Output file path
        quality: JPEG quality (1-100, default: 95)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = output_path.suffix.lower()
    if ext in [EXT_JPG, EXT_JPEG]:
        image.save(output_path, FORMAT_JPEG, quality=quality, optimize=True)
    elif ext == EXT_PNG:
        image.save(output_path, FORMAT_PNG, optimize=True)
    elif ext == EXT_WEBP:
        image.save(output_path, FORMAT_WEBP, quality=quality, method=6)
    else:
        # Default to PNG
        image.save(output_path, FORMAT_PNG, optimize=True)
