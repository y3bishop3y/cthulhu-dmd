#!/usr/bin/env python3
"""
Test OCR pipeline against known correct text.

This script compares OCR output from different pipelines against
ground truth text to measure accuracy and identify best strategies.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich import box
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

from scripts.utils.ocr import extract_text_from_image as extract_basic
from scripts.utils.advanced_ocr import extract_text_advanced
from scripts.models.character import CharacterData

console = Console()


def load_ground_truth(character_json_path: Path) -> Dict[str, str]:
    """Load ground truth text from character.json.
    
    Args:
        character_json_path: Path to character.json
        
    Returns:
        Dictionary with ground truth text (special_power levels)
    """
    try:
        char_data = CharacterData.model_validate_json(character_json_path.read_text())
        
        ground_truth = {}
        if char_data.special_power and char_data.special_power.levels:
            for i, level in enumerate(char_data.special_power.levels, 1):
                ground_truth[f"level_{i}"] = level.description
        
        return ground_truth
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load ground truth: {e}[/yellow]")
        return {}


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple similarity score between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    # Normalize texts
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    
    if not t1 and not t2:
        return 1.0
    
    if not t1 or not t2:
        return 0.0
    
    # Simple word overlap
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def test_ocr_pipelines(
    image_path: Path, ground_truth: Dict[str, str]
) -> Dict[str, Dict[str, float]]:
    """Test different OCR pipelines on an image.
    
    Args:
        image_path: Path to image file
        ground_truth: Dictionary of ground truth text
        
    Returns:
        Dictionary mapping pipeline name to results
    """
    results = {}
    
    # Test basic OCR
    try:
        console.print(f"[cyan]Testing basic OCR pipeline...[/cyan]")
        basic_text = extract_basic(image_path)
        results["basic"] = {
            "text": basic_text,
            "similarity": calculate_similarity(basic_text, " ".join(ground_truth.values())),
        }
    except Exception as e:
        console.print(f"[red]Basic OCR failed: {e}[/red]")
        results["basic"] = {"text": "", "similarity": 0.0}
    
    # Test advanced OCR (with regions)
    try:
        console.print(f"[cyan]Testing advanced OCR pipeline (with regions)...[/cyan]")
        advanced_text = extract_text_advanced(image_path, use_regions=True)
        results["advanced_regions"] = {
            "text": advanced_text,
            "similarity": calculate_similarity(advanced_text, " ".join(ground_truth.values())),
        }
    except Exception as e:
        console.print(f"[red]Advanced OCR (regions) failed: {e}[/red]")
        results["advanced_regions"] = {"text": "", "similarity": 0.0}
    
    # Test advanced OCR (without regions)
    try:
        console.print(f"[cyan]Testing advanced OCR pipeline (no regions)...[/cyan]")
        advanced_no_regions_text = extract_text_advanced(image_path, use_regions=False)
        results["advanced_no_regions"] = {
            "text": advanced_no_regions_text,
            "similarity": calculate_similarity(
                advanced_no_regions_text, " ".join(ground_truth.values())
            ),
        }
    except Exception as e:
        console.print(f"[red]Advanced OCR (no regions) failed: {e}[/red]")
        results["advanced_no_regions"] = {"text": "", "similarity": 0.0}
    
    return results


@click.command()
@click.option(
    "--character",
    type=str,
    required=True,
    help="Character name (e.g., 'ahmed')",
)
@click.option(
    "--season",
    type=str,
    default="season1",
    help="Season directory (default: season1)",
)
def main(character: str, season: str):
    """Test OCR pipelines against ground truth text."""
    console.print(f"[bold cyan]OCR Pipeline Testing[/bold cyan]\n")
    
    # Find character directory
    char_dir = Path("data") / season / character
    if not char_dir.exists():
        console.print(f"[red]Error: Character directory not found: {char_dir}[/red]")
        sys.exit(1)
    
    # Load ground truth
    char_json = char_dir / "character.json"
    if not char_json.exists():
        console.print(f"[red]Error: character.json not found: {char_json}[/red]")
        sys.exit(1)
    
    ground_truth = load_ground_truth(char_json)
    if not ground_truth:
        console.print("[yellow]Warning: No ground truth found in character.json[/yellow]")
        console.print("Make sure special_power levels are populated.\n")
    
    # Display ground truth
    console.print("[bold]Ground Truth Text:[/bold]")
    for key, text in ground_truth.items():
        console.print(f"  {key}: {text}")
    console.print()
    
    # Find back card image
    back_path = None
    for ext in [".webp", ".jpg", ".jpeg"]:
        candidate = char_dir / f"back{ext}"
        if candidate.exists():
            back_path = candidate
            break
    
    if not back_path:
        console.print(f"[red]Error: Back card image not found in {char_dir}[/red]")
        sys.exit(1)
    
    console.print(f"[green]Testing on: {back_path}[/green]\n")
    
    # Test OCR pipelines
    results = test_ocr_pipelines(back_path, ground_truth)
    
    # Display results
    table = Table(title="OCR Pipeline Comparison", box=box.ROUNDED)
    table.add_column("Pipeline", style="cyan")
    table.add_column("Similarity Score", justify="right", style="green")
    table.add_column("Text Preview", style="dim", max_width=60)
    
    # Sort by similarity
    sorted_results = sorted(results.items(), key=lambda x: x[1]["similarity"], reverse=True)
    
    for pipeline_name, result in sorted_results:
        similarity = result["similarity"]
        text_preview = result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"]
        
        # Color code similarity
        if similarity > 0.5:
            similarity_style = "green"
        elif similarity > 0.2:
            similarity_style = "yellow"
        else:
            similarity_style = "red"
        
        table.add_row(
            pipeline_name,
            f"[{similarity_style}]{similarity:.2%}[/{similarity_style}]",
            text_preview,
        )
    
    console.print(table)
    
    # Best result
    best_pipeline = sorted_results[0][0]
    best_similarity = sorted_results[0][1]["similarity"]
    
    console.print(f"\n[bold green]Best Pipeline: {best_pipeline} ({best_similarity:.2%} similarity)[/bold green]")
    
    if best_similarity < 0.3:
        console.print(
            "\n[yellow]Warning: All pipelines have low similarity. Consider:[/yellow]"
        )
        console.print("  1. Adding EasyOCR as alternative engine")
        console.print("  2. Improving preprocessing (deskewing, despeckling)")
        console.print("  3. Using cloud OCR APIs for difficult images")
        console.print("  4. Manual correction for critical characters")


if __name__ == "__main__":
    main()

