#!/usr/bin/env python3
"""Diagnostic script to investigate common power extraction issues."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import cv2

from scripts.cli.parse.parsing_constants import COMMON_POWER_REGIONS
from scripts.models.character import BackCardData
from scripts.utils.optimal_ocr import (
    _check_line_has_description_keywords,
    _extract_common_powers_from_region,
    _is_line_likely_description,
    _reject_partial_match,
    _validate_power_match_quality,
    extract_common_powers_from_back_card,
    extract_text_from_region_with_strategy,
    get_optimal_strategy_for_category,
    load_optimal_strategies,
)

try:
    from rapidfuzz import fuzz as rapidfuzz_fuzz
except ImportError:
    rapidfuzz_fuzz = None


def diagnose_character(char_name: str, season: str = "season1") -> None:
    """Diagnose common power extraction for a single character.

    Args:
        char_name: Character name (e.g., 'ian')
        season: Season directory name
    """
    char_dir = Path(f"data/{season}/{char_name}")
    back_path = char_dir / "back.webp"
    if not back_path.exists():
        back_path = char_dir / "back.jpg"
    if not back_path.exists():
        print(f"❌ {char_name}: No back card found")
        return

    print(f"\n{'=' * 80}")
    print(f"DIAGNOSING: {char_name.upper()}")
    print(f"{'=' * 80}")

    # Get expected powers from JSON if available
    char_json = char_dir / "character.json"
    expected_powers = []
    if char_json.exists():
        import json

        data = json.loads(char_json.read_text())
        expected_powers = data.get("common_powers", [])

    if expected_powers:
        print(f"Expected powers: {', '.join(expected_powers)}")
    else:
        print("Expected powers: [unknown]")

    # Get final extraction result
    final_powers = extract_common_powers_from_back_card(back_path)
    print(f"\nFinal extracted powers: {final_powers}")

    if len(final_powers) != 2:
        print(f"⚠️  ISSUE: Found {len(final_powers)} power(s), expected 2")

    # Load image and config
    img = cv2.imread(str(back_path))
    h, w = img.shape[:2]
    config = load_optimal_strategies()
    power_strategy = (
        get_optimal_strategy_for_category("special_power", config) or "tesseract_bilateral_psm3"
    )

    # Analyze each region
    for idx, (x_pct, y_pct, width_pct, height_pct) in enumerate(COMMON_POWER_REGIONS):
        x = int(w * x_pct)
        y = int(h * y_pct)
        width = int(w * width_pct)
        height = int(h * height_pct)
        region = (x, y, width, height)

        print(f"\n--- Region {idx + 1} (X={x}, Y={y}, W={width}, H={height}) ---")

        # Extract text
        region_text = extract_text_from_region_with_strategy(back_path, region, power_strategy)
        lines = [l.strip() for l in region_text.split("\n") if l.strip()]

        print(f"Extracted {len(lines)} lines:")
        for i, line in enumerate(lines[:8]):
            print(f"  {i}: {repr(line[:70])}")

        # Test extraction function
        region_powers = _extract_common_powers_from_region(back_path, region, power_strategy)
        print(f"\nRegion {idx + 1} extraction result: {region_powers}")

        # Detailed analysis of each line
        print("\nPower detection analysis:")
        for i, line in enumerate(lines):
            power = BackCardData._detect_common_power(line)
            if power:
                print(f"\n  Line {i}: {repr(line[:60])}")
                print(f"    Detected as: {power}")
                print(f"    Length: {len(line)}, Power length: {len(power)}")

                # Check validation steps
                is_desc = _is_line_likely_description(line)
                reject = _reject_partial_match(line, power, rapidfuzz_fuzz)
                good = _validate_power_match_quality(line, power, rapidfuzz_fuzz)
                has_keywords = _check_line_has_description_keywords(line)

                print(f"    Is description: {is_desc}")
                print(f"    Reject partial: {reject}")
                print(f"    Good quality: {good}")
                print(f"    Has description keywords: {has_keywords}")

                # Determine why it might be rejected
                reasons = []
                if len(line) < 4:
                    reasons.append(f"Too short ({len(line)} < 4)")
                if len(line) < len(power) * 0.6:
                    reasons.append(f"Too short vs power ({len(line)} < {len(power) * 0.6})")
                if is_desc and not power:
                    reasons.append("Looks like description")
                if reject:
                    reasons.append("Partial match rejected")
                if not good:
                    reasons.append("Poor match quality")
                if has_keywords:
                    reasons.append("Contains description keywords")

                if reasons:
                    print(f"    ⚠️  Would be rejected: {', '.join(reasons)}")
                else:
                    print("    ✓ Would be accepted")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python diagnose_common_powers.py <character_name> [season]")
        print("Example: python diagnose_common_powers.py ian season1")
        sys.exit(1)

    char_name = sys.argv[1]
    season = sys.argv[2] if len(sys.argv) > 2 else "season1"

    diagnose_character(char_name, season)


if __name__ == "__main__":
    main()
