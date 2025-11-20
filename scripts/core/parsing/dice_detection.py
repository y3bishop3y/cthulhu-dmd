#!/usr/bin/env python3
"""
Visual detection of dice symbols and red swirls in character card images.

Since we know what these symbols look like, we can use computer vision
to detect them directly in the images rather than relying on OCR text.
"""

import sys
from pathlib import Path
from typing import Tuple

try:
    import cv2
    import numpy as np
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install opencv-python\n",
        file=sys.stderr,
    )
    raise


def detect_dice_symbols(image_path: Path) -> Tuple[int, int]:
    """Detect dice symbols (@, #) in the image.

    Args:
        image_path: Path to character card image

    Returns:
        Tuple of (green_dice_count, black_dice_count)
        Note: Currently returns total dice symbols found (distinguishing
        green vs black would require color detection or template matching)
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return (0, 0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Dice symbols are typically circular or square shapes
    # Look for small circular/rectangular regions that might be dice symbols

    # Method 1: Template matching (if we had dice symbol templates)
    # For now, we'll use contour detection to find small symbol-like shapes

    # Threshold to find bright symbols on dark background
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dice_count = 0
    img_area = gray.shape[0] * gray.shape[1]

    for contour in contours:
        area = cv2.contourArea(contour)
        # Dice symbols are small (typically 50-500 pixels in area)
        if 50 < area < 500:
            # Check aspect ratio (dice symbols are roughly square or circular)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            if 0.5 < aspect_ratio < 2.0:  # Roughly square/circular
                # Check if it's in a reasonable location (not edges, likely in power descriptions)
                img_height, img_width = gray.shape[:2]
                if (
                    img_width * 0.1 < x < img_width * 0.9
                    and img_height * 0.2 < y < img_height * 0.9
                ):
                    dice_count += 1

    # Return as both green and black for now (we'd need color detection to distinguish)
    # In practice, if we find dice symbols, we know they're mentioned
    return (dice_count, dice_count)


def detect_red_swirls(image_path: Path) -> int:
    """Detect red swirl symbols in the image.

    Args:
        image_path: Path to character card image

    Returns:
        Number of red swirl symbols found
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return 0

    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Red swirls are typically red/orange colored
    # Define red color range in HSV
    # Red wraps around 180, so we need two ranges
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Find contours in red regions
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    swirl_count = 0
    img_area = img.shape[0] * img.shape[1]

    for contour in contours:
        area = cv2.contourArea(contour)
        # Red swirls are typically medium-sized symbols (100-2000 pixels)
        if 100 < area < 2000:
            # Check if it's roughly circular/swirl-shaped
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            if 0.6 < aspect_ratio < 1.5:  # Roughly circular
                # Check if it's in a reasonable location (insanity track area, typically top)
                img_height, img_width = img.shape[:2]
                if (
                    img_width * 0.1 < x < img_width * 0.9
                    and img_height * 0.05 < y < img_height * 0.4
                ):  # Top portion (insanity track)
                    swirl_count += 1

    return swirl_count


def detect_dice_and_swirls(image_path: Path) -> dict:
    """Detect both dice symbols and red swirls in the image.

    Args:
        image_path: Path to character card image

    Returns:
        Dictionary with detection results:
        {
            "dice_found": bool,
            "dice_count": int,
            "red_swirl_found": bool,
            "red_swirl_count": int,
        }
    """
    green_dice, black_dice = detect_dice_symbols(image_path)
    red_swirls = detect_red_swirls(image_path)

    return {
        "dice_found": (green_dice + black_dice) > 0,
        "dice_count": green_dice + black_dice,
        "green_dice_count": green_dice,
        "black_dice_count": black_dice,
        "red_swirl_found": red_swirls > 0,
        "red_swirl_count": red_swirls,
    }


if __name__ == "__main__":
    # Test on Adam's back card
    test_path = Path("data/season1/adam/back.webp")
    if not test_path.exists():
        test_path = Path("data/season1/adam/back.jpg")

    if test_path.exists():
        print("Testing dice and red swirl detection on Adam's back card...")
        print("=" * 80)

        results = detect_dice_and_swirls(test_path)

        print("\nDetection Results:")
        print("-" * 80)
        print(f"Dice found: {results['dice_found']} (count: {results['dice_count']})")
        print(f"  Green dice: {results['green_dice_count']}")
        print(f"  Black dice: {results['black_dice_count']}")
        print(
            f"Red swirls found: {results['red_swirl_found']} (count: {results['red_swirl_count']})"
        )
        print("=" * 80)
    else:
        print(f"Test image not found: {test_path}")
