#!/usr/bin/env python3
"""
Image format conversion utilities for OCR preprocessing.

Converts lossy formats (JPG, JPEG) to lossless formats (PNG) to improve OCR accuracy.
JPG compression artifacts can degrade OCR results, so converting to PNG before
processing can improve extraction quality.
"""

import sys
import tempfile
from pathlib import Path
from typing import Final, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

# File extension constants
EXT_JPG: Final[str] = ".jpg"
EXT_JPEG: Final[str] = ".jpeg"
EXT_PNG: Final[str] = ".png"
EXT_WEBP: Final[str] = ".webp"

# Lossy formats that should be converted
LOSSY_FORMATS: Final[tuple] = (EXT_JPG, EXT_JPEG, EXT_WEBP)

# Lossless format for OCR
OCR_FORMAT: Final[str] = EXT_PNG


def convert_to_png_for_ocr(image_path: Path, output_path: Optional[Path] = None) -> Path:
    """Convert image to PNG format for better OCR accuracy.

    Converts lossy formats (JPG, JPEG, WebP) to PNG to avoid compression artifacts.
    If image is already PNG, returns original path.

    Args:
        image_path: Path to source image
        output_path: Optional output path (defaults to same directory with .png extension)

    Returns:
        Path to PNG image (original if already PNG, converted otherwise)

    Raises:
        ValueError: If image cannot be read or converted
        ImportError: If cv2/numpy are not available
    """
    if cv2 is None or np is None:
        raise ImportError("cv2 and numpy required for image conversion")

    if not image_path.exists():
        raise ValueError(f"Image file does not exist: {image_path}")

    # Check if already PNG (lossless, no conversion needed)
    if image_path.suffix.lower() == EXT_PNG:
        return image_path

    # Note: WEBP can be lossy or lossless, but we treat it as lossy
    # since most WEBP files are lossy and we can't easily detect it
    # Converting to PNG ensures lossless quality for OCR

    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Determine output path
    if output_path is None:
        # Use same directory, change extension to .png
        output_path = image_path.parent / f"{image_path.stem}{EXT_PNG}"
    else:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PNG (lossless)
    success = cv2.imwrite(str(output_path), img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    if not success:
        raise ValueError(f"Could not write PNG image: {output_path}")

    return output_path


def get_ocr_optimized_path(image_path: Path, use_temp: bool = False) -> Path:
    """Get OCR-optimized image path (converts to PNG if needed).

    For lossy formats, converts to PNG and saves alongside original.
    If PNG already exists, reuses it. For PNG, returns original.
    
    PNG files are saved in the same directory as the original image
    with the same name but .png extension. These are kept for reuse
    across multiple OCR runs (not auto-deleted).

    Args:
        image_path: Path to source image
        use_temp: If True, use temporary file (auto-deleted after use).
                  If False (default), save PNG alongside original for reuse.

    Returns:
        Path to OCR-optimized image (PNG format)

    Raises:
        ValueError: If image cannot be read or converted
        ImportError: If cv2/numpy are not available
    """
    if cv2 is None or np is None:
        raise ImportError("cv2 and numpy required for image conversion")

    # If already PNG, return original
    if image_path.suffix.lower() == EXT_PNG:
        return image_path

    # If lossy format, convert to PNG
    if image_path.suffix.lower() in LOSSY_FORMATS:
        if use_temp:
            # Use temporary file (caller responsible for cleanup)
            temp_file = tempfile.NamedTemporaryFile(suffix=EXT_PNG, delete=False)
            temp_path = Path(temp_file.name)
            temp_file.close()

            # Convert to PNG
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            success = cv2.imwrite(str(temp_path), img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            if not success:
                raise ValueError(f"Could not write temporary PNG: {temp_path}")

            return temp_path
        else:
            # Save PNG alongside original (for reuse across OCR runs)
            png_path = image_path.parent / f"{image_path.stem}{EXT_PNG}"
            
            # If PNG already exists, reuse it
            if png_path.exists():
                return png_path
            
            # Convert to PNG and save
            return convert_to_png_for_ocr(image_path, png_path)
    else:
        # Unknown format, try to use as-is
        return image_path


def convert_directory_images(
    directory: Path, pattern: str = "*.jpg", recursive: bool = True, dry_run: bool = False
) -> int:
    """Convert all images in a directory from lossy to PNG format.

    Args:
        directory: Directory to process
        pattern: File pattern to match (default: "*.jpg")
        recursive: If True, process subdirectories
        dry_run: If True, only report what would be converted

    Returns:
        Number of images converted

    Raises:
        ImportError: If cv2/numpy are not available
    """
    if cv2 is None or np is None:
        raise ImportError("cv2 and numpy required for image conversion")

    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    converted_count = 0

    # Find all matching images
    if recursive:
        image_files = list(directory.rglob(pattern))
    else:
        image_files = list(directory.glob(pattern))

    for image_path in image_files:
        # Skip if already PNG
        if image_path.suffix.lower() == EXT_PNG:
            continue

        # Skip if not a lossy format we want to convert
        if image_path.suffix.lower() not in LOSSY_FORMATS:
            continue

        png_path = image_path.parent / f"{image_path.stem}{EXT_PNG}"

        # Skip if PNG already exists
        if png_path.exists():
            continue

        if dry_run:
            print(f"Would convert: {image_path} -> {png_path}")
            converted_count += 1
        else:
            try:
                convert_to_png_for_ocr(image_path, png_path)
                print(f"Converted: {image_path} -> {png_path}")
                converted_count += 1
            except Exception as e:
                print(f"Error converting {image_path}: {e}", file=sys.stderr)

    return converted_count

