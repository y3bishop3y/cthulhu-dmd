#!/usr/bin/env python3
"""
Unit tests for NLP-based OCR analysis.

Tests semantic extraction from OCR text using NLP.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

try:
    import spacy
except ImportError:
    pytest.skip("spaCy not installed", allow_module_level=True)

from scripts.parsing.nlp_parser import extract_healing_info, get_nlp_model
from scripts.parsing.analyze_ocr_with_nlp import extract_semantic_info, compare_semantic_info


class TestHealingInfoExtraction:
    """Test healing information extraction from text."""

    def test_extract_healing_or(self):
        """Test extraction of 'heal X stress OR wound' pattern."""
        nlp = get_nlp_model()
        text = "At the end of your turn, you may heal 1 stress OR wound on an investigator"
        doc = nlp(text)
        info = extract_healing_info(doc)
        
        assert info["has_healing"] is True
        assert info["stress_healed"] == 1
        assert info["wounds_healed"] == 1
        assert info["has_or"] is True
        assert info["has_and"] is False

    def test_extract_healing_flexible(self):
        """Test extraction of 'heal X in any combination' pattern."""
        nlp = get_nlp_model()
        text = "Instead, heal 2 in any combination of stress and wounds"
        doc = nlp(text)
        info = extract_healing_info(doc)
        
        assert info["has_healing"] is True
        assert info["is_flexible"] is True
        assert info["stress_healed"] == 2
        assert info["wounds_healed"] == 2

    def test_extract_healing_and(self):
        """Test extraction of 'heal X stress AND Y wounds' pattern."""
        nlp = get_nlp_model()
        text = "Instead, heal 2 stress AND 2 wounds"
        doc = nlp(text)
        info = extract_healing_info(doc)
        
        assert info["has_healing"] is True
        assert info["has_and"] is True
        assert info["stress_healed"] == 2
        assert info["wounds_healed"] == 2

    def test_extract_healing_each(self):
        """Test extraction of 'EACH investigator' pattern."""
        nlp = get_nlp_model()
        text = "Heal 2 stress AND 2 wounds on EACH investigator in your space"
        doc = nlp(text)
        info = extract_healing_info(doc)
        
        assert info["has_healing"] is True
        assert info["is_each"] is True
        assert info["stress_healed"] == 2
        assert info["wounds_healed"] == 2

    def test_no_healing(self):
        """Test that non-healing text returns False."""
        nlp = get_nlp_model()
        text = "Gain a Green Dice while your sanity is on a Red Swirl"
        doc = nlp(text)
        info = extract_healing_info(doc)
        
        assert info["has_healing"] is False
        assert info["stress_healed"] == 0
        assert info["wounds_healed"] == 0


class TestSemanticInfoExtraction:
    """Test semantic information extraction."""

    def test_extract_key_phrases(self):
        """Test extraction of key phrases."""
        nlp = get_nlp_model()
        text = "At the end of your turn, you may heal 1 stress OR wound on an investigator"
        info = extract_semantic_info(text, nlp)
        
        assert info["key_phrases"]["heal"] is True
        assert info["key_phrases"]["stress"] is True
        assert info["key_phrases"]["wound"] is True
        assert info["key_phrases"]["investigator"] is True
        assert info["key_phrases"]["or"] is True

    def test_extract_verbs(self):
        """Test verb extraction."""
        nlp = get_nlp_model()
        text = "At the end of your turn, you may heal 1 stress"
        info = extract_semantic_info(text, nlp)
        
        assert "heal" in info["verbs"]
        assert len(info["verbs"]) > 0

    def test_extract_numbers(self):
        """Test number extraction."""
        nlp = get_nlp_model()
        text = "heal 2 stress AND 2 wounds"
        info = extract_semantic_info(text, nlp)
        
        assert "2" in info["numbers"]
        assert len(info["numbers"]) >= 1

    def test_extract_sentences(self):
        """Test sentence extraction."""
        nlp = get_nlp_model()
        text = "At the end of your turn, you may heal 1 stress. Instead, heal 2 wounds."
        info = extract_semantic_info(text, nlp)
        
        assert len(info["sentences"]) >= 2
        assert any("heal" in s.lower() for s in info["sentences"])


class TestSemanticComparison:
    """Test semantic information comparison."""

    def test_compare_key_phrases(self):
        """Test key phrase comparison."""
        gt_info = {
            "key_phrases": {
                "heal": True,
                "stress": True,
                "wound": True,
                "instead": True,
            }
        }
        
        ocr_info = {
            "key_phrases": {
                "heal": True,
                "stress": True,
                "wound": False,  # OCR missed this
                "instead": True,
            }
        }
        
        comparison = compare_semantic_info(gt_info, ocr_info)
        
        assert comparison["key_phrases_match"]["heal"]["match"] is True
        assert comparison["key_phrases_match"]["stress"]["match"] is True
        assert comparison["key_phrases_match"]["wound"]["match"] is False
        assert comparison["key_phrases_match"]["instead"]["match"] is True

    def test_compare_verbs(self):
        """Test verb comparison."""
        gt_info = {
            "verbs": ["heal", "reduce"]
        }
        
        ocr_info = {
            "verbs": ["heal", "attack", "move"]
        }
        
        comparison = compare_semantic_info(gt_info, ocr_info)
        
        assert "heal" in comparison["verbs_match"]["common"]
        assert "reduce" in comparison["verbs_match"]["missing"]
        assert len(comparison["verbs_match"]["common"]) == 1

    def test_compare_numbers(self):
        """Test number comparison."""
        gt_info = {
            "numbers": ["1", "2"]
        }
        
        ocr_info = {
            "numbers": ["2", "3"]
        }
        
        comparison = compare_semantic_info(gt_info, ocr_info)
        
        assert "2" in comparison["numbers_match"]["common"]
        assert "1" in comparison["numbers_match"]["missing"]
        assert len(comparison["numbers_match"]["common"]) == 1

    def test_compare_healing_info(self):
        """Test healing information comparison."""
        gt_info = {
            "healing_info": {
                "has_healing": True,
                "stress_healed": 2,
                "wounds_healed": 2,
            }
        }
        
        ocr_info = {
            "healing_info": {
                "has_healing": True,
                "stress_healed": 2,
                "wounds_healed": 1,  # OCR got this wrong
            }
        }
        
        comparison = compare_semantic_info(gt_info, ocr_info)
        
        assert comparison["healing_info_match"]["stress_match"] is True
        assert comparison["healing_info_match"]["wounds_match"] is False


class TestGarbledOCRHandling:
    """Test handling of garbled OCR text."""

    def test_garbled_text_still_extracts_concepts(self):
        """Test that garbled OCR text can still extract some concepts."""
        nlp = get_nlp_model()
        # Simulate garbled OCR text
        text = "At the end of your tufn;! may hea! 'strese-OR wey on an invesitgatdr"
        info = extract_semantic_info(text, nlp)
        
        # Should still detect some key phrases
        assert info["key_phrases"]["heal"] is True or "hea" in text.lower()
        assert info["key_phrases"]["stress"] is True or "strese" in text.lower()
        assert info["key_phrases"]["or"] is True or "OR" in text

    def test_mixed_card_text(self):
        """Test handling text that mixes different card sections."""
        nlp = get_nlp_model()
        # Text that mixes game rules with power description
        text = "YOUR TURN 1. TAKE 3 ACTIONS heal 3 stress/health Instead, gain a Green Dice"
        info = extract_semantic_info(text, nlp)
        
        # Should extract multiple concepts
        assert info["key_phrases"]["heal"] is True
        assert info["key_phrases"]["instead"] is True
        assert len(info["verbs"]) > 0

