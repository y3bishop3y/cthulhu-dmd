#!/usr/bin/env python3
"""
Advanced NLP post-processing for OCR text correction.

Uses multiple techniques:
- spaCy for semantic understanding
- Fuzzy string matching for corrections
- Domain-specific dictionaries (game terms)
- Context-aware corrections
- Spell checking with domain terms
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from difflib import SequenceMatcher
except ImportError:
    SequenceMatcher = None

try:
    import spacy
except ImportError:
    spacy = None

try:
    import rapidfuzz
    from rapidfuzz import fuzz, process

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    rapidfuzz = None
    fuzz = None
    process = None
    RAPIDFUZZ_AVAILABLE = False

from scripts.core.parsing.text import clean_ocr_text

# Domain-specific dictionary (game terms that OCR might misspell)
DOMAIN_DICTIONARY: Dict[str, List[str]] = {
    # Common powers
    "marksman": ["marksman", "marksmen", "markman"],
    "toughness": ["toughness", "toughnes", "toughnss"],
    "arcane mastery": ["arcane mastery", "arcan mastery", "arcane master"],
    "stealth": ["stealth", "steath", "stelth"],
    "brawling": ["brawling", "brawling", "brawlling"],
    "swiftness": ["swiftness", "swiftnes", "swiftnss"],
    # Game mechanics
    "elder sign": ["elder sign", "elder sign sign", "elder signs"],
    "green dice": ["green dice", "green dice dice", "green die"],
    "black dice": ["black dice", "black dice dice", "black die"],
    "red swirl": ["red swirl", "red swir", "red swil"],
    "sanity": ["sanity", "santiy", "sanitiy", "santity"],
    "stress": ["stress", "stres", "strees"],
    "wound": ["wound", "woundnds", "woundndnds", "wond", "wonds"],
    "investigator": ["investigator", "investigater", "investiduteriawour"],
    # Actions
    "gain": ["gain", "goin", "go in", "goin g"],
    "instead": ["instead", "insted", "in stead"],
    "attack": ["attack", "attak", "atack"],
    "heal": ["heal", "heal", "healing"],
    "reroll": ["reroll", "re roll", "re-roll"],
    # Locations and names (common OCR errors)
    "manchester": ["manchester", "manchest", "manchestor"],
    "england": ["england", "englan", "englad"],
}

# Common OCR character substitutions
CHAR_SUBSTITUTIONS: Dict[str, str] = {
    "0": "O",  # In words
    "1": "I",  # In words (context-dependent)
    "5": "S",
    "8": "B",
    "@": "a",  # In words
    "#": "",  # Remove
    "$": "s",
    "%": "",
    "&": "and",
}

# Load spaCy model (lazy)
_nlp_model: Optional[any] = None


def get_nlp_model():
    """Get or load spaCy NLP model."""
    global _nlp_model
    if spacy is None:
        return None

    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
        except OSError:
            # Model not available, return None
            return None
    return _nlp_model


def fuzzy_match_word(word: str, dictionary: List[str], threshold: float = 0.8) -> Optional[str]:
    """Fuzzy match a word against a dictionary.

    Args:
        word: Word to match
        dictionary: List of possible words
        threshold: Minimum similarity (0-1)

    Returns:
        Best match if above threshold, None otherwise
    """
    if RAPIDFUZZ_AVAILABLE and process and fuzz:
        # Use rapidfuzz for fast fuzzy matching
        try:
            result = process.extractOne(word.lower(), dictionary, scorer=fuzz.ratio)
            if result and result[1] >= threshold * 100:
                return result[0]
        except Exception:
            # Fall through to difflib if rapidfuzz fails
            pass

    if SequenceMatcher:
        # Fallback to difflib
        best_match = None
        best_score = 0.0
        word_lower = word.lower()

        for candidate in dictionary:
            score = SequenceMatcher(None, word_lower, candidate.lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate

        return best_match

    return None


def correct_with_domain_dictionary(text: str) -> str:
    """Correct text using domain-specific dictionary.

    Args:
        text: OCR text

    Returns:
        Corrected text
    """
    corrected = text

    # Split into words, preserving punctuation
    words = re.findall(r"\b\w+\b", text)

    for word in words:
        word_lower = word.lower()

        # Check each dictionary entry
        for correct_term, variants in DOMAIN_DICTIONARY.items():
            # Check if word matches any variant
            match = fuzzy_match_word(word_lower, variants, threshold=0.75)
            if match and match != word_lower:
                # Replace with correct term
                pattern = r"\b" + re.escape(word) + r"\b"
                corrected = re.sub(pattern, correct_term, corrected, flags=re.IGNORECASE)
                break

    return corrected


def correct_character_substitutions(text: str) -> str:
    """Correct common OCR character substitutions.

    Args:
        text: OCR text

    Returns:
        Corrected text
    """
    corrected = text

    # Apply character substitutions (context-aware)
    for wrong_char, correct_char in CHAR_SUBSTITUTIONS.items():
        if correct_char == "":
            # Remove character
            corrected = corrected.replace(wrong_char, "")
        else:
            # Replace in word contexts (not standalone numbers)
            # Pattern: letter-wrong_char-letter or letter-wrong_char-word_boundary
            pattern = r"([a-zA-Z])" + re.escape(wrong_char) + r"([a-zA-Z]|\b)"
            corrected = re.sub(pattern, r"\1" + correct_char + r"\2", corrected)

    return corrected


def correct_with_spacy(text: str) -> str:
    """Use spaCy for context-aware corrections.

    Args:
        text: OCR text

    Returns:
        Corrected text
    """
    nlp = get_nlp_model()
    if nlp is None:
        return text

    try:
        doc = nlp(text)
        corrected_parts = []

        for token in doc:
            # Check for common OCR errors in tokens
            token_text = token.text

            # Fix spacing issues
            if token_text and token_text[0].isupper() and len(corrected_parts) > 0:
                prev_text = corrected_parts[-1] if corrected_parts else ""
                if prev_text and not prev_text.endswith(" ") and not prev_text.endswith("\n"):
                    # Add space before capitalized word if missing
                    if not token_text.startswith(" ") and prev_text[-1].islower():
                        corrected_parts.append(" ")

            corrected_parts.append(token_text)

            # Add space after token if needed
            if token.whitespace_:
                corrected_parts.append(token.whitespace_)

        return "".join(corrected_parts)
    except Exception:
        # If spaCy fails, return original
        return text


def fix_repeated_words(text: str) -> str:
    """Fix repeated words/phrases (common OCR error).

    Args:
        text: OCR text

    Returns:
        Text with repetitions removed
    """
    corrected = text

    # Pattern: word word or phrase phrase
    # Try multiple times to catch nested repetitions
    for _ in range(3):
        # Match repeated words (1-5 words)
        pattern = r"\b(\w+(?:\s+\w+){0,4})\s+\1\b"
        corrected = re.sub(pattern, r"\1", corrected, flags=re.IGNORECASE)

    # Fix specific known repetitions
    known_repetitions = [
        (r"\breduce\s+wounds?\s+reduce\s+wounds?\b", "reduce wounds"),
        (r"\belder\s+sign\s+sign\b", "elder sign"),
        (r"\bgreen\s+dice\s+dice\b", "green dice"),
        (r"\bblack\s+dice\s+dice\b", "black dice"),
        (r"\bANY\s+SOURCE\.\s+ANY\s+SOURCE\.\b", "ANY SOURCE."),
    ]

    for pattern, replacement in known_repetitions:
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    return corrected


def fix_word_boundaries(text: str) -> str:
    """Fix word boundary issues (missing spaces, merged words).

    Args:
        text: OCR text

    Returns:
        Text with fixed word boundaries
    """
    corrected = text

    # Fix common merged words
    merged_words = {
        r"\bAtthe\b": "At the",
        r"\bTistress\b": "stress",
        r"\bweund\b": "wound",
        r"\bgoin\b": "gain",
        r"\bgoin g\b": "gaining",
        r"\bsantiy\b": "sanity",
        r"\bwoundndnds\b": "wounds",
        r"\bwoundnds\b": "wounds",
        r"\bwondnds\b": "wounds",
    }

    for pattern, replacement in merged_words.items():
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    # Add spaces between lowercase-uppercase transitions (if missing)
    corrected = re.sub(r"([a-z])([A-Z])", r"\1 \2", corrected)

    # Normalize whitespace
    corrected = re.sub(r"\s+", " ", corrected)

    return corrected


def advanced_nlp_postprocess(text: str) -> str:
    """Advanced NLP post-processing pipeline.

    Applies multiple correction techniques in order:
    1. Basic OCR cleaning
    2. Character substitutions
    3. Domain dictionary corrections
    4. Word boundary fixes
    5. Repeated word removal
    6. spaCy-based corrections (if available)

    Args:
        text: Raw OCR text

    Returns:
        Corrected text
    """
    # Step 1: Basic OCR cleaning
    corrected = clean_ocr_text(text, preserve_newlines=True)

    # Step 2: Character substitutions
    corrected = correct_character_substitutions(corrected)

    # Step 3: Domain dictionary corrections
    corrected = correct_with_domain_dictionary(corrected)

    # Step 4: Word boundary fixes
    corrected = fix_word_boundaries(corrected)

    # Step 5: Fix repeated words/phrases
    corrected = fix_repeated_words(corrected)

    # Step 6: spaCy-based corrections (if available)
    if spacy:
        corrected = correct_with_spacy(corrected)

    # Final cleanup
    corrected = re.sub(r"\s+", " ", corrected)
    corrected = corrected.strip()

    return corrected


def enhanced_nlp_postprocess(text: str) -> str:
    """Enhanced NLP post-processing with aggressive corrections.

    Uses all techniques plus additional aggressive fixes.

    Args:
        text: Raw OCR text

    Returns:
        Corrected text
    """
    # Start with advanced NLP
    corrected = advanced_nlp_postprocess(text)

    # Additional aggressive corrections
    # Fix common OCR patterns in game text

    # Fix "I" -> "1" in specific contexts (numbers)
    number_contexts = [
        (r"\bI\s+enemy\b", "1 enemy"),
        (r"\bI\s+space\b", "1 space"),
        (r"\bI\s+free\b", "1 free"),
        (r"\bI\s+additional\b", "1 additional"),
        (r"\bI\s+wound\b", "1 wound"),
        (r"\bI\s+green\b", "1 green"),
        (r"\bI\s+black\b", "1 black"),
        (r"\bI\s+elder\b", "1 elder"),
        (r"\bI\s+success\b", "1 success"),
        (r"\bI\s+attack\b", "1 attack"),
        (r"\bI\s+action\b", "1 action"),
        (r"\bI\s+reroll\b", "1 reroll"),
        (r"\bI\s+stress\b", "1 stress"),
        (r"\bI\s+times\b", "1 times"),
        (r"\bI\s+die\b", "1 die"),
        (r"\bI\s+dice\b", "1 dice"),
    ]

    for pattern, replacement in number_contexts:
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    # Fix common power name OCR errors
    power_corrections = {
        r"\bFUELED\s+BY\s+MADNESS\b": "FUELED BY MADNESS",
        r"\bfig\s+vet\s+BY\s+MADNESS\b": "FUELED BY MADNESS",
        r"\bHEALING\s+PRAYER\b": "HEALING PRAYER",
        r"\bhealing\s+prayer\b": "Healing Prayer",
    }

    for pattern, replacement in power_corrections.items():
        corrected = re.sub(pattern, replacement, corrected)

    return corrected
