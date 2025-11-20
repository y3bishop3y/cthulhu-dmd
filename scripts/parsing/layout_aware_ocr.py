#!/usr/bin/env python3
"""
Layout-aware OCR extraction for character cards.

Character cards have a fixed layout:
- Top: Name (all caps, large font)
- Below name: Location (all caps, smaller font)
- Middle: Motto (below decorative symbol, short phrase, may be in quotes)
- Bottom: Description/Story (white text on black background, longer paragraph)

This module extracts text from specific regions based on the known card structure.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install opencv-python pytesseract\n",
        file=sys.stderr,
    )
    raise

from pydantic import BaseModel, Field

from scripts.models.ocr_settings_config import get_ocr_settings

_ocr_settings = get_ocr_settings()


class LayoutExtractionResults(BaseModel):
    """Results from layout-aware OCR extraction."""

    name: str = Field(default="", description="Extracted character name")
    location: str = Field(default="", description="Extracted character location")
    motto: str = Field(default="", description="Extracted character motto")
    description: str = Field(default="", description="Extracted character description/story")


class CardLayoutExtractor:
    """Extract text from character card using known layout structure."""

    def __init__(self):
        """Initialize layout extractor."""
        self.psm_mode = _ocr_settings.ocr_tesseract_default_psm_mode
        self.oem_mode = _ocr_settings.ocr_tesseract_default_oem_mode

    def preprocess_image(self, image_path: Path) -> np.ndarray:
        """Preprocess image for OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Preprocessed grayscale image
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        return gray

    def detect_text_regions_by_color(
        self, image: np.ndarray, is_white_text: bool = True
    ) -> List[Tuple[int, int, int, int]]:
        """Detect text regions based on text color (white or black).
        
        Args:
            image: Grayscale image
            is_white_text: If True, detect white text on dark background
            
        Returns:
            List of (x, y, width, height) bounding boxes
        """
        # Binarize: white text on black = high values, black text on white = low values
        if is_white_text:
            # White text: threshold high values
            _, binary = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
        else:
            # Black text: threshold low values and invert
            _, binary = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        img_height, img_width = image.shape[:2]
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            img_area = img_height * img_width
            
            # Filter small regions (noise) and very large ones
            if area > img_area * 0.0005 and area < img_area * 0.5:
                # Filter by aspect ratio (text regions are usually wider than tall)
                aspect_ratio = w / h if h > 0 else 0
                if 0.2 < aspect_ratio < 15:
                    regions.append((x, y, w, h))
        
        # Sort by y-coordinate (top to bottom)
        regions.sort(key=lambda r: r[1])
        return regions

    def extract_text_from_region(
        self, image: np.ndarray, region: Tuple[int, int, int, int], psm_mode: Optional[int] = None
    ) -> str:
        """Extract text from a specific region.
        
        Args:
            image: Preprocessed image
            region: (x, y, width, height) bounding box
            psm_mode: Optional PSM mode override
            
        Returns:
            Extracted text
        """
        x, y, w, h = region
        roi = image[y : y + h, x : x + w]
        
        psm = psm_mode or self.psm_mode
        config = f"--oem {self.oem_mode} --psm {psm}"
        
        text = pytesseract.image_to_string(roi, config=config)
        return text.strip()

    def extract_name_location_region(
        self, image: np.ndarray, top_percent: float = 0.25
    ) -> Tuple[str, str]:
        """Extract name and location from top region.
        
        Args:
            image: Preprocessed image
            top_percent: Percentage of image height to use for top region (default 25%)
            
        Returns:
            Tuple of (name, location) text
        """
        img_height, img_width = image.shape[:2]
        top_height = int(img_height * top_percent)
        
        # Extract from top region
        top_region = (0, 0, img_width, top_height)
        text = self.extract_text_from_region(image, top_region, psm_mode=6)  # Uniform block
        
        # Split into lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Name is usually first line (all caps, longer)
        # Location is usually second line (all caps, shorter, may have comma)
        name = ""
        location = ""
        
        for i, line in enumerate(lines):
            if not name and line.isupper() and len(line) > 5:
                name = line
            elif name and not location and line.isupper() and len(line) > 3:
                location = line
                break
        
        return name, location

    def extract_motto_region(
        self, image: np.ndarray, top_percent: float = 0.25, bottom_percent: float = 0.35
    ) -> str:
        """Extract motto from middle region (between name/location and description).
        
        Args:
            image: Preprocessed image
            top_percent: Percentage to skip from top (name/location area)
            bottom_percent: Percentage to skip from bottom (description area)
            
        Returns:
            Extracted motto text
        """
        img_height, img_width = image.shape[:2]
        top_y = int(img_height * top_percent)
        bottom_y = int(img_height * (1 - bottom_percent))
        middle_height = bottom_y - top_y
        
        # Extract from middle region
        middle_region = (0, top_y, img_width, middle_height)
        text = self.extract_text_from_region(image, middle_region, psm_mode=7)  # Single line
        
        # Clean and find motto (short phrase, may span 2 lines)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Look for short phrases (2-10 words) that look like mottos
        motto_candidates = []
        for i, line in enumerate(lines):
            word_count = len(line.split())
            # Check if it looks like a motto
            if 2 <= word_count <= 10 and len(line) < 100:
                motto_candidates.append(line)
                # Check if next line completes it
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_word_count = len(next_line.split())
                    if 2 <= next_word_count <= 5:
                        combined = f"{line} {next_line}".strip()
                        if len(combined) < 100:
                            motto_candidates.append(combined)
        
        # Return first reasonable candidate
        if motto_candidates:
            return motto_candidates[0]
        
        return ""

    def extract_description_region(
        self, image: np.ndarray, bottom_percent: float = 0.35
    ) -> str:
        """Extract description/story from bottom region (white text on black background).
        
        Args:
            image: Preprocessed image
            bottom_percent: Percentage of image height to use for bottom region
            
        Returns:
            Extracted description text
        """
        img_height, img_width = image.shape[:2]
        bottom_y = int(img_height * (1 - bottom_percent))
        bottom_height = int(img_height * bottom_percent)
        
        # Extract from bottom region (white text on black)
        bottom_region = (0, bottom_y, img_width, bottom_height)
        
        # Try both white text detection and regular extraction
        text1 = self.extract_text_from_region(image, bottom_region, psm_mode=6)  # Uniform block
        
        # Also try detecting white text regions specifically
        white_text_regions = self.detect_text_regions_by_color(
            image[bottom_y : bottom_y + bottom_height, :], is_white_text=True
        )
        
        if white_text_regions:
            # Extract from each white text region
            all_text = []
            for region in white_text_regions:
                x, y, w, h = region
                # Adjust y to be relative to full image
                full_region = (x, bottom_y + y, w, h)
                region_text = self.extract_text_from_region(image, full_region, psm_mode=6)
                if region_text:
                    all_text.append(region_text)
            
            if all_text:
                text2 = "\n".join(all_text)
                # Prefer longer text (more complete extraction)
                return text1 if len(text1) > len(text2) else text2
        
        return text1

    def extract_from_card(self, image_path: Path) -> LayoutExtractionResults:
        """Extract all text fields from character card using layout awareness.
        
        Args:
            image_path: Path to character card image
            
        Returns:
            LayoutExtractionResults with extracted text fields
        """
        image = self.preprocess_image(image_path)
        
        # Extract from known regions
        name, location = self.extract_name_location_region(image)
        motto = self.extract_motto_region(image)
        description = self.extract_description_region(image)
        
        return LayoutExtractionResults(
            name=name,
            location=location,
            motto=motto,
            description=description,
        )


def extract_text_layout_aware(image_path: Path) -> LayoutExtractionResults:
    """Convenience function for layout-aware extraction.
    
    Args:
        image_path: Path to character card image
        
    Returns:
        LayoutExtractionResults with extracted text fields
    """
    extractor = CardLayoutExtractor()
    return extractor.extract_from_card(image_path)


if __name__ == "__main__":
    # Test on Adam's front card
    test_path = Path("data/season1/adam/front.webp")
    if test_path.exists():
        print("Testing layout-aware OCR on Adam's front card...")
        print("=" * 80)
        
        extractor = CardLayoutExtractor()
        results = extractor.extract_from_card(test_path)
        
        print("\nExtracted fields:")
        print("-" * 80)
        for key, value in results.items():
            print(f"{key.capitalize()}: {value}")
        print("=" * 80)
    else:
        print(f"Test image not found: {test_path}")

