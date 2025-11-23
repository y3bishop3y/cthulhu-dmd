#!/usr/bin/env python3
"""
Create favicon and logo from Cthulhu image.

Generates:
- favicon.ico (16x16, 32x32, 48x48)
- favicon-16x16.png
- favicon-32x32.png
- apple-touch-icon.png (180x180)
- logo.png (for top right corner, ~200px height)
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL/Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SOURCE_IMAGE = PROJECT_ROOT / "sites" / "artifacts" / "images" / "chuthul-image.jpg"
OUTPUT_DIR = PROJECT_ROOT / "sites" / "artifacts" / "images"


def create_favicon_and_logo():
    """Create favicon and logo files from source image."""
    if not SOURCE_IMAGE.exists():
        print(f"Error: Source image not found at {SOURCE_IMAGE}")
        sys.exit(1)

    print(f"Loading source image: {SOURCE_IMAGE}")
    img = Image.open(SOURCE_IMAGE)

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        # Convert to RGB first, then add alpha channel
        if img.mode == 'RGB':
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB').convert('RGBA')

    # Process image: make black parts green, white background transparent
    # Theme green color: #10b981 (RGB: 16, 185, 129)
    green_color = (16, 185, 129, 255)  # RGBA for green
    transparent = (0, 0, 0, 0)  # Transparent
    
    # Create new image with same size
    processed_img = Image.new('RGBA', img.size, transparent)
    pixels = img.load()
    processed_pixels = processed_img.load()
    
    print("Processing image: converting black to green, white to transparent...")
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            # Check if pixel is dark (black/dark gray) - threshold around 128
            # If it's dark, make it green; if it's light (white), make it transparent
            if r < 128 and g < 128 and b < 128:
                # Dark pixel - make it green
                processed_pixels[x, y] = green_color
            else:
                # Light pixel (white background) - make it transparent
                processed_pixels[x, y] = transparent
    
    img = processed_img

    # Create favicon sizes
    favicon_sizes = [16, 32, 48]
    favicon_images = []

    for size in favicon_sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        favicon_images.append(resized)
        # Save individual PNG files
        png_path = OUTPUT_DIR / f"favicon-{size}x{size}.png"
        resized.save(png_path, 'PNG')
        print(f"Created: {png_path}")

    # Create favicon.ico with multiple sizes
    ico_path = OUTPUT_DIR / "favicon.ico"
    favicon_images[0].save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"Created: {ico_path}")

    # Create Apple touch icon (180x180)
    apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
    apple_path = OUTPUT_DIR / "apple-touch-icon.png"
    apple_icon.save(apple_path, 'PNG')
    print(f"Created: {apple_path}")

    # Create logo for top right corner (200px height, maintain aspect ratio)
    logo_height = 200
    aspect_ratio = img.width / img.height
    logo_width = int(logo_height * aspect_ratio)
    logo = img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    logo_path = OUTPUT_DIR / "logo.png"
    logo.save(logo_path, 'PNG')
    print(f"Created: {logo_path}")

    # Also create a smaller version for compact display (100px height)
    logo_small_height = 100
    logo_small_width = int(logo_small_height * aspect_ratio)
    logo_small = img.resize((logo_small_width, logo_small_height), Image.Resampling.LANCZOS)
    logo_small_path = OUTPUT_DIR / "logo-small.png"
    logo_small.save(logo_small_path, 'PNG')
    print(f"Created: {logo_small_path}")

    print("\n✓ All favicon and logo files created successfully!")


if __name__ == "__main__":
    create_favicon_and_logo()

