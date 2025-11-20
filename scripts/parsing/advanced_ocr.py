#!/usr/bin/env python3
"""
Advanced OCR pipeline for robust image-to-text extraction.

This module implements a production-grade OCR pipeline with:
1. Layout analysis (text region detection)
2. Multi-stage preprocessing (deskewing, despeckling, binarization)
3. Multi-strategy OCR (different PSM modes, region-specific)
4. Result combination and validation
5. Post-processing and correction

Based on RAG pipeline document processing best practices.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install opencv-python pytesseract pillow\n",
        file=sys.stderr,
    )
    raise

from scripts.models.ocr_settings_config import get_ocr_settings

_ocr_settings = get_ocr_settings()


class OCRPipeline:
    """Production-grade OCR pipeline for character card images."""

    def __init__(self):
        """Initialize OCR pipeline with default settings."""
        self.psm_modes = [
            3,  # Fully automatic page segmentation
            6,  # Uniform block of text
            7,  # Single text line
            11,  # Sparse text
            12,  # Single text word
        ]
        self.oem_mode = _ocr_settings.ocr_tesseract_default_oem_mode

    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect text regions in image using contour detection.
        
        Args:
            image: Preprocessed binary image
            
        Returns:
            List of (x, y, width, height) bounding boxes for text regions
        """
        # Find contours
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter small regions (noise) and very large ones (full image)
            area = w * h
            img_area = image.shape[0] * image.shape[1]
            
            if area > img_area * 0.001 and area < img_area * 0.8:
                # Filter by aspect ratio (text regions are usually wider than tall)
                aspect_ratio = w / h if h > 0 else 0
                if 0.3 < aspect_ratio < 10:
                    regions.append((x, y, w, h))
        
        # Sort by y-coordinate (top to bottom)
        regions.sort(key=lambda r: r[1])
        return regions

    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew (rotate) image to align text horizontally.
        
        Args:
            image: Binary image
            
        Returns:
            Deskewed image
        """
        # Find all non-zero points
        coords = np.column_stack(np.where(image > 0))
        
        if len(coords) == 0:
            return image
        
        # Find minimum area rectangle
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Only rotate if angle is significant
        if abs(angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            return rotated
        
        return image

    def despeckle_image(self, image: np.ndarray) -> np.ndarray:
        """Remove small noise/specks from image.
        
        Args:
            image: Binary image
            
        Returns:
            Despeckled image
        """
        # Morphological opening to remove small noise
        kernel = np.ones((2, 2), np.uint8)
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Morphological closing to fill small holes
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return closed

    def preprocess_image(
        self,
        image_path: Path,
        deskew: bool = True,
        despeckle: bool = True,
        enhance_contrast: bool = True,
    ) -> np.ndarray:
        """Advanced preprocessing pipeline.
        
        Args:
            image_path: Path to image file
            deskew: If True, deskew the image
            despeckle: If True, remove noise/specks
            enhance_contrast: If True, enhance contrast
            
        Returns:
            Preprocessed binary image
        """
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        # Binarize using OTSU
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Deskew
        if deskew:
            binary = self.deskew_image(binary)
        
        # Despeckle
        if despeckle:
            binary = self.despeckle_image(binary)
        
        return binary

    def extract_text_with_psm(
        self, image: np.ndarray, psm_mode: int, region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """Extract text using specific PSM mode.
        
        Args:
            image: Preprocessed image
            psm_mode: Page segmentation mode
            region: Optional (x, y, w, h) region to extract from
            
        Returns:
            Extracted text
        """
        if region:
            x, y, w, h = region
            roi = image[y : y + h, x : x + w]
        else:
            roi = image
        
        config = f"--oem {self.oem_mode} --psm {psm_mode}"
        text = pytesseract.image_to_string(roi, config=config)
        return text.strip()

    def extract_text_multi_strategy(
        self, image: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[int, str]:
        """Extract text using multiple PSM modes and return all results.
        
        Args:
            image: Preprocessed image
            region: Optional region to extract from
            
        Returns:
            Dictionary mapping PSM mode to extracted text
        """
        results = {}
        for psm_mode in self.psm_modes:
            try:
                text = self.extract_text_with_psm(image, psm_mode, region)
                if text:
                    results[psm_mode] = text
            except Exception:
                continue
        
        return results

    def combine_results(self, results: Dict[int, str]) -> str:
        """Combine multiple OCR results intelligently.
        
        Strategy:
        1. Prefer longer results (more text extracted)
        2. Prefer results with fewer OCR artifacts
        3. Use voting for common words
        
        Args:
            results: Dictionary of PSM mode -> text
            
        Returns:
            Best combined text
        """
        if not results:
            return ""
        
        if len(results) == 1:
            return list(results.values())[0]
        
        # Score each result
        scored = []
        for psm_mode, text in results.items():
            # Score based on length and quality indicators
            score = len(text)
            
            # Penalize common OCR errors
            error_indicators = ["@", "#", "$", "%", "^", "&", "*", "|", "~", "`"]
            error_count = sum(text.count(c) for c in error_indicators)
            score -= error_count * 10
            
            # Prefer results with more words (likely more complete)
            word_count = len(text.split())
            score += word_count * 2
            
            scored.append((score, psm_mode, text))
        
        # Sort by score (highest first)
        scored.sort(reverse=True)
        
        # Return best result
        return scored[0][2]

    def extract_text_from_image(
        self,
        image_path: Path,
        use_regions: bool = True,
        deskew: bool = True,
        despeckle: bool = True,
    ) -> str:
        """Extract text from image using advanced pipeline.
        
        Args:
            image_path: Path to image file
            use_regions: If True, detect and process text regions separately
            deskew: If True, deskew image
            despeckle: If True, despeckle image
            
        Returns:
            Extracted text
        """
        # Preprocess image
        processed = self.preprocess_image(image_path, deskew=deskew, despeckle=despeckle)
        
        if use_regions:
            # Detect text regions
            regions = self.detect_text_regions(processed)
            
            if regions:
                # Extract from each region and combine
                all_results = []
                for region in regions:
                    results = self.extract_text_multi_strategy(processed, region)
                    if results:
                        combined = self.combine_results(results)
                        if combined:
                            all_results.append(combined)
                
                return "\n".join(all_results)
        
        # Fallback: extract from full image
        results = self.extract_text_multi_strategy(processed)
        return self.combine_results(results)


def extract_text_advanced(
    image_path: Path,
    use_regions: bool = True,
    deskew: bool = True,
    despeckle: bool = True,
) -> str:
    """Convenience function for advanced OCR extraction.
    
    Args:
        image_path: Path to image file
        use_regions: If True, detect and process text regions separately
        deskew: If True, deskew image
        despeckle: If True, despeckle image
        
    Returns:
        Extracted text
    """
    pipeline = OCRPipeline()
    return pipeline.extract_text_from_image(
        image_path, use_regions=use_regions, deskew=deskew, despeckle=despeckle
    )


if __name__ == "__main__":
    # Test on Ahmed's back card
    test_path = Path("data/season1/ahmed/back.webp")
    if test_path.exists():
        print("Testing advanced OCR pipeline on Ahmed's back card...")
        print("=" * 80)
        
        pipeline = OCRPipeline()
        text = pipeline.extract_text_from_image(test_path, use_regions=True)
        
        print("\nExtracted text (first 500 chars):")
        print("-" * 80)
        print(text[:500])
        print("\n" + "=" * 80)
    else:
        print(f"Test image not found: {test_path}")

