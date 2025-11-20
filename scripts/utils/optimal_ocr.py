#!/usr/bin/env python3
"""
Utilities for using optimal OCR strategies based on benchmark results.

This module provides functions to extract text using the best OCR strategy
for each category (name, location, motto, story, special_power, etc.)
as determined by benchmark testing.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from scripts.parsing.multi_ocr import get_all_strategies, OCRStrategy
except ImportError as e:
    print(f"Error: Missing required import: {e}\n", file=sys.stderr)
    raise


def load_optimal_strategies(config_path: Optional[Path] = None) -> Dict[str, Dict]:
    """Load optimal OCR strategies from config file.
    
    Args:
        config_path: Optional path to config file (defaults to scripts/data/optimal_ocr_strategies.json)
        
    Returns:
        Dictionary with optimal strategy configuration
    """
    if config_path is None:
        config_path = project_root / "scripts" / "data" / "optimal_ocr_strategies.json"
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Optimal strategies config not found: {config_path}\n"
            "Run benchmark first to generate optimal strategies."
        )
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config


def get_optimal_strategy_for_category(
    category: str, config: Optional[Dict[str, Dict]] = None
) -> Optional[str]:
    """Get the optimal strategy name for a specific category.
    
    Args:
        category: Category name (name, location, motto, story, special_power, etc.)
        config: Optional pre-loaded config (will load if not provided)
        
    Returns:
        Strategy name or None if not found
    """
    if config is None:
        config = load_optimal_strategies()
    
    strategy_info = config.get("strategies", {}).get(category)
    if strategy_info:
        return strategy_info.get("strategy_name")
    
    return None


def extract_text_with_optimal_strategy(
    image_path: Path,
    category: str = "story",
    config: Optional[Dict[str, Dict]] = None,
    fallback_strategy: Optional[str] = None,
) -> str:
    """Extract text from image using optimal strategy for category.
    
    Args:
        image_path: Path to image file
        category: Category name (name, location, motto, story, special_power, etc.)
        config: Optional pre-loaded config (will load if not provided)
        fallback_strategy: Fallback strategy name if optimal not found
        
    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # If config doesn't exist, use fallback
            if fallback_strategy:
                return _extract_with_strategy(image_path, fallback_strategy)
            # Last resort: use first available strategy
            strategies = get_all_strategies()
            if strategies:
                return strategies[0].extract(image_path)
            return ""
    
    # Get optimal strategy for category
    strategy_name = get_optimal_strategy_for_category(category, config)
    
    if not strategy_name:
        # Try fallback
        if fallback_strategy:
            return _extract_with_strategy(image_path, fallback_strategy)
        # Last resort
        strategies = get_all_strategies()
        if strategies:
            return strategies[0].extract(image_path)
        return ""
    
    return _extract_with_strategy(image_path, strategy_name)


def extract_front_card_with_optimal_strategy(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> str:
    """Extract text from front card using optimal strategy.
    
    Uses the strategy optimized for story extraction (most important front card field).
    
    Args:
        image_path: Path to front card image
        config: Optional pre-loaded config
        
    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback to basic strategy
            return _extract_with_strategy(image_path, "tesseract_basic_psm3")
    
    # Use front_card_strategy if available, otherwise use story strategy
    front_strategy = config.get("front_card_strategy", {}).get("strategy_name")
    if not front_strategy:
        front_strategy = get_optimal_strategy_for_category("story", config)
    
    if front_strategy:
        return _extract_with_strategy(image_path, front_strategy)
    
    # Fallback
    return _extract_with_strategy(image_path, "tesseract_basic_psm3")


def extract_back_card_with_optimal_strategy(
    image_path: Path, config: Optional[Dict[str, Dict]] = None
) -> str:
    """Extract text from back card using optimal strategy.
    
    Uses the strategy optimized for special power extraction (most important back card field).
    
    Args:
        image_path: Path to back card image
        config: Optional pre-loaded config
        
    Returns:
        Extracted text
    """
    if config is None:
        try:
            config = load_optimal_strategies()
        except FileNotFoundError:
            # Fallback to basic strategy
            return _extract_with_strategy(image_path, "tesseract_basic_psm3")
    
    # Use back_card_strategy if available, otherwise use special_power strategy
    back_strategy = config.get("back_card_strategy", {}).get("strategy_name")
    if not back_strategy:
        back_strategy = get_optimal_strategy_for_category("special_power", config)
    
    if back_strategy:
        return _extract_with_strategy(image_path, back_strategy)
    
    # Fallback
    return _extract_with_strategy(image_path, "tesseract_basic_psm3")


def _extract_with_strategy(image_path: Path, strategy_name: str) -> str:
    """Extract text using a specific strategy by name.
    
    Args:
        image_path: Path to image file
        strategy_name: Name of OCR strategy
        
    Returns:
        Extracted text
    """
    strategies = get_all_strategies()
    strategy_dict = {s.name: s for s in strategies}
    
    strategy = strategy_dict.get(strategy_name)
    if not strategy:
        # Strategy not found, use first available
        if strategies:
            return strategies[0].extract(image_path)
        return ""
    
    return strategy.extract(image_path)


def update_optimal_strategies_from_benchmark(
    benchmark_file: Path, output_config: Optional[Path] = None
) -> Dict[str, Dict]:
    """Update optimal strategies config from benchmark results.
    
    Args:
        benchmark_file: Path to benchmark JSON file
        output_config: Optional output path (defaults to scripts/data/optimal_ocr_strategies.json)
        
    Returns:
        Updated config dictionary
    """
    from scripts.parsing.benchmark_ocr_strategies import find_best_strategies_per_category
    
    with open(benchmark_file, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)
    
    best_strategies = find_best_strategies_per_category(benchmark_data["results"])
    
    # Build config structure
    config = {
        "version": "1.0.0",
        "last_updated": benchmark_data.get("timestamp", "").split("T")[0],
        "description": "Optimal OCR strategies per category, determined from benchmark results",
        "strategies": best_strategies,
        "front_card_strategy": {
            "strategy_name": best_strategies.get("story", {}).get("strategy_name", ""),
            "description": f"Best for story extraction ({best_strategies.get('story', {}).get('score', 0):.1f}%)",
            "reason": "Story is the most important and hardest to extract from front card",
        },
        "back_card_strategy": {
            "strategy_name": best_strategies.get("special_power", {}).get("strategy_name", ""),
            "description": f"Best for power extraction ({best_strategies.get('special_power', {}).get('score', 0):.1f}%)",
            "reason": "Special power extraction is the most important back card field",
        },
    }
    
    if output_config is None:
        output_config = project_root / "scripts" / "data" / "optimal_ocr_strategies.json"
    
    output_config.parent.mkdir(parents=True, exist_ok=True)
    with open(output_config, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config

