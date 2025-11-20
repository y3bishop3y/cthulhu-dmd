#!/usr/bin/env python3
"""
NLP-based parser for extracting power descriptions using spaCy.

This module uses spaCy for semantic understanding of power descriptions,
handling OCR errors and extracting structured information.
"""

import re
import sys
from pathlib import Path
from typing import List, Optional

try:
    import spacy
    from spacy import displacy
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: uv add spacy\n"
        "Then download model: uv run python -m spacy download en_core_web_sm\n",
        file=sys.stderr,
    )
    raise

# Load spaCy model (lazy loading)
_nlp_model: Optional[spacy.Language] = None


def get_nlp_model() -> spacy.Language:
    """Get or load spaCy NLP model."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
        except OSError:
            print(
                "Error: spaCy model 'en_core_web_sm' not found.\n"
                "Download with: uv run python -m spacy download en_core_web_sm\n",
                file=sys.stderr,
            )
            raise
    return _nlp_model


def clean_ocr_for_nlp(text: str) -> str:
    """Clean OCR text for better NLP processing.

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    # Fix common OCR errors
    corrections = {
        "Atthe": "At the",
        "Tistress": "stress",
        "weund": "wound",
        "investiduteriawour": "investigator",
        "investigater": "investigator",
        "tistress": "stress",
        "weund": "wound",
        "wond": "wound",
        "wonds": "wounds",
    }

    cleaned = text
    for error, correction in corrections.items():
        cleaned = re.sub(rf"\b{error}\b", correction, cleaned, flags=re.I)

    # Fix spacing issues
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)  # Add space between words
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace

    return cleaned.strip()


def extract_healing_info(doc: spacy.tokens.Doc) -> dict:
    """Extract healing information from a spaCy document.

    Args:
        doc: spaCy document

    Returns:
        Dictionary with healing information
    """
    info = {
        "has_healing": False,
        "stress_healed": 0,
        "wounds_healed": 0,
        "is_flexible": False,  # "in any combination"
        "is_each": False,  # "EACH investigator"
        "has_or": False,  # "stress OR wound"
        "has_and": False,  # "stress AND wound"
        "target": None,  # "investigator", "yourself", etc.
    }

    text_lower = doc.text.lower()

    # Look for "heal" verb
    heal_tokens = [token for token in doc if token.lemma_.lower() == "heal"]

    if heal_tokens:
        info["has_healing"] = True

        # Find all numbers in the sentence
        numbers = [
            token
            for token in doc
            if token.pos_ == "NUM" or (token.text.isdigit() and len(token.text) <= 2)
        ]

        # Extract numeric values
        amounts = []
        for num_token in numbers:
            try:
                amount = int(num_token.text)
                amounts.append(amount)
            except ValueError:
                continue

        # Check for "in any combination" - flexible healing
        if "combination" in text_lower or "any combination" in text_lower:
            info["is_flexible"] = True
            if amounts:
                info["stress_healed"] = amounts[0]
                info["wounds_healed"] = amounts[0]

        # Check for "OR" - choice between stress OR wound
        elif " or " in text_lower:
            info["has_or"] = True
            if amounts:
                amount = amounts[0]
                # Both are options, so store amount for both
                info["stress_healed"] = amount
                info["wounds_healed"] = amount

        # Check for "AND" - both stress AND wounds
        elif " and " in text_lower:
            info["has_and"] = True
            if len(amounts) >= 2:
                # Multiple numbers - assume first is stress, second is wounds
                info["stress_healed"] = amounts[0]
                info["wounds_healed"] = amounts[1]
            elif len(amounts) == 1:
                # Single number - check if repeated in text
                amount = amounts[0]
                if f"{amount} stress" in text_lower and f"{amount} wound" in text_lower:
                    info["stress_healed"] = amount
                    info["wounds_healed"] = amount
                else:
                    # Might be just one type
                    if "stress" in text_lower:
                        info["stress_healed"] = amount
                    if "wound" in text_lower:
                        info["wounds_healed"] = amount

        # If no pattern matched but we have amounts, try default extraction
        if info["stress_healed"] == 0 and info["wounds_healed"] == 0 and amounts:
            amount = amounts[0]
            if "stress" in text_lower or "wound" in text_lower:
                info["stress_healed"] = amount
                info["wounds_healed"] = amount

        # Check for "EACH"
        if "each" in text_lower:
            info["is_each"] = True

        # Find target
        for token in doc:
            if "investigator" in token.text.lower():
                info["target"] = "investigator"
                break
        if "yourself" in text_lower or "your space" in text_lower:
            if info["target"] is None:
                info["target"] = "investigator in your space"

    return info


def parse_power_levels_with_nlp(text: str) -> List[dict]:
    """Parse power levels from text using NLP.

    Args:
        text: OCR text containing power descriptions

    Returns:
        List of level dictionaries with parsed information
    """
    nlp = get_nlp_model()

    # Clean OCR text
    cleaned_text = clean_ocr_for_nlp(text)

    # Find the power section - look for "At the end" or "heal" patterns
    lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]

    # Find where the power section starts
    power_start_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Look for start of power: "At the end" or "heal" with "turn" or "investigator"
        if ("at the end" in line_lower or "atthe end" in line_lower) and "turn" in line_lower:
            power_start_idx = i
            break
        elif "heal" in line_lower and (
            "turn" in line_lower or "investigator" in line_lower or "space" in line_lower
        ):
            if power_start_idx is None:
                power_start_idx = i

    if power_start_idx is None:
        # Try to find any section with "heal"
        for i, line in enumerate(lines):
            if "heal" in line.lower():
                power_start_idx = i
                break

    if power_start_idx is None:
        return []

    # Extract power section (next 20-30 lines should contain all 4 levels)
    power_lines = lines[power_start_idx : power_start_idx + 30]

    # Process line by line first to detect level boundaries
    # Then use NLP for semantic analysis
    levels = []
    current_level_lines = []

    for i, line in enumerate(power_lines):
        line_lower = line.lower().strip()

        # Skip very short or irrelevant lines
        if len(line.split()) < 2:
            continue

        # Check if this starts a new level
        starts_with_instead = bool(re.search(r"^[^a-z]*instead[,\s]+", line_lower))
        has_heal_and_turn = "heal" in line_lower and (
            "turn" in line_lower or "end" in line_lower or "investigator" in line_lower
        )

        if starts_with_instead and current_level_lines:
            # Save previous level
            level_text = " ".join(current_level_lines).strip()
            if level_text:
                level_doc = nlp(level_text)
                levels.append(
                    {
                        "level": len(levels) + 1,
                        "description": level_text,
                        "nlp_analysis": extract_healing_info(level_doc),
                    }
                )
            # Start new level - clean up "Instead" prefix
            clean_line = re.sub(r"^[^a-z]*instead[,\s]+", "", line, flags=re.I).strip()
            current_level_lines = [clean_line if clean_line else line]
        elif has_heal_and_turn and not current_level_lines:
            # First level
            current_level_lines = [line]
        elif current_level_lines:
            # Continue current level if it looks like continuation
            # Check if line contains healing-related keywords or is short continuation
            if (
                any(
                    keyword in line_lower
                    for keyword in [
                        "heal",
                        "stress",
                        "wound",
                        "investigator",
                        "space",
                        "each",
                        "and",
                        "or",
                    ]
                )
                or len(line.split()) <= 12
            ):
                current_level_lines.append(line)

    # Don't forget last level
    if current_level_lines:
        level_text = " ".join(current_level_lines).strip()
        if level_text:
            level_doc = nlp(level_text)
            levels.append(
                {
                    "level": len(levels) + 1,
                    "description": level_text,
                    "nlp_analysis": extract_healing_info(level_doc),
                }
            )

    return levels


def analyze_ahmed_power() -> None:
    """Analyze Ahmed's power using NLP."""
    from scripts.utils.ocr import extract_text_from_image

    # Get OCR text
    back_path = Path("data/season1/ahmed/back_ocr_preprocessed.png")
    if not back_path.exists():
        back_path = Path("data/season1/ahmed/back.webp")

    if not back_path.exists():
        print(f"Error: {back_path} not found")
        return

    print("=" * 80)
    print("NLP Analysis of Ahmed's Special Power")
    print("=" * 80)
    print()

    # Extract OCR text
    ocr_text = extract_text_from_image(back_path)
    print("Raw OCR Text (first 500 chars):")
    print("-" * 80)
    print(ocr_text[:500])
    print()

    # Clean and parse with NLP
    cleaned = clean_ocr_for_nlp(ocr_text)
    print("Cleaned Text (first 500 chars):")
    print("-" * 80)
    print(cleaned[:500])
    print()

    # Parse levels
    levels = parse_power_levels_with_nlp(ocr_text)

    print(f"Extracted {len(levels)} levels:")
    print("-" * 80)
    for level in levels:
        print(f"\nLevel {level['level']}:")
        print(f"  Description: {level['description'][:100]}...")
        analysis = level.get("nlp_analysis", {})
        print("  NLP Analysis:")
        print(f"    Has healing: {analysis.get('has_healing')}")
        print(f"    Stress healed: {analysis.get('stress_healed')}")
        print(f"    Wounds healed: {analysis.get('wounds_healed')}")
        print(f"    Is flexible: {analysis.get('is_flexible')}")
        print(f"    Is each: {analysis.get('is_each')}")
        print(f"    Target: {analysis.get('target')}")

    # Also try parsing the correct text to see what NLP extracts
    print("\n" + "=" * 80)
    print("NLP Analysis of CORRECT Text (for comparison)")
    print("=" * 80)

    correct_text = """At the end of your turn, you may heal 1 stress OR wound on an investigator in your space (it may be yourself)
Instead, heal 2 in any combination of stress and wounds
Instead, heal 2 stress AND 2 wounds
Heal 2 stress AND 2 wounds on EACH investigator in your space"""

    correct_levels = parse_power_levels_with_nlp(correct_text)

    for level in correct_levels:
        print(f"\nLevel {level['level']}:")
        print(f"  Description: {level['description']}")
        analysis = level.get("nlp_analysis", {})
        print("  NLP Analysis:")
        print(f"    Has healing: {analysis.get('has_healing')}")
        print(f"    Stress healed: {analysis.get('stress_healed')}")
        print(f"    Wounds healed: {analysis.get('wounds_healed')}")
        print(f"    Is flexible: {analysis.get('is_flexible')}")
        print(f"    Is each: {analysis.get('is_each')}")
        print(f"    Target: {analysis.get('target')}")


if __name__ == "__main__":
    analyze_ahmed_power()
