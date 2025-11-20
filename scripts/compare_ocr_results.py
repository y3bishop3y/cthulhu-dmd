#!/usr/bin/env python3
"""
Compare OCR results side-by-side with ground truth.

Shows ground truth text vs each OCR engine/strategy output for easy verification.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.panel import Panel
    from rich.columns import Columns
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

from scripts.parsing.multi_ocr import get_all_strategies, test_all_strategies
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
                ground_truth[f"Level {i}"] = level.description
        
        return ground_truth
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load ground truth: {e}[/yellow]")
        return {}


def highlight_differences(text1: str, text2: str) -> str:
    """Simple difference highlighting (basic implementation).
    
    Args:
        text1: Ground truth text
        text2: OCR extracted text
        
    Returns:
        Highlighted text showing differences
    """
    # For now, just return the text
    # Could be enhanced with diff highlighting
    return text2


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
@click.option(
    "--strategy",
    type=str,
    multiple=True,
    help="Specific strategies to test (can specify multiple). If not specified, tests all.",
)
@click.option(
    "--top-n",
    type=int,
    default=5,
    help="If no strategies specified, show top N strategies (default: 5)",
)
def main(character: str, season: str, strategy: tuple, top_n: int):
    """Compare OCR results side-by-side with ground truth."""
    console.print(f"[bold cyan]OCR Results Comparison[/bold cyan]\n")
    
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
        console.print("[red]Error: No ground truth found in character.json[/red]")
        console.print("Make sure special_power levels are populated with correct descriptions.\n")
        sys.exit(1)
    
    # Display ground truth
    console.print("[bold green]Ground Truth Text:[/bold green]")
    for level_name, text in ground_truth.items():
        console.print(Panel(text, title=level_name, border_style="green"))
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
    
    console.print(f"[cyan]Testing on: {back_path}[/cyan]\n")
    
    # Get strategies to test
    all_strategies = get_all_strategies()
    
    if strategy:
        # Test specific strategies
        strategies_to_test = [s for s in all_strategies if s.name in strategy]
        if not strategies_to_test:
            console.print(f"[red]Error: No matching strategies found: {strategy}[/red]")
            console.print(f"[yellow]Available strategies: {[s.name for s in all_strategies]}[/yellow]")
            sys.exit(1)
    else:
        # Test all, then show top N
        strategies_to_test = all_strategies
    
    # Test strategies
    console.print(f"[cyan]Testing {len(strategies_to_test)} strategies...[/cyan]\n")
    
    results = {}
    for strategy_obj in strategies_to_test:
        try:
            text = strategy_obj.extract(back_path)
            results[strategy_obj.name] = {
                "text": text,
                "description": strategy_obj.description,
            }
        except Exception as e:
            console.print(f"[red]Error testing {strategy_obj.name}: {e}[/red]")
            results[strategy_obj.name] = {
                "text": "",
                "description": strategy_obj.description,
            }
    
    # If testing all, score and show top N
    if not strategy and len(results) > top_n:
        from scripts.iterate_ocr_strategies import calculate_similarity, find_key_phrases
        
        ground_truth_text = " ".join(ground_truth.values())
        key_phrases = ["heal", "stress", "wound", "investigator", "instead", "end of your turn"]
        
        scored = []
        for name, result in results.items():
            text = result["text"]
            similarity = calculate_similarity(text, ground_truth_text)
            phrase_count = find_key_phrases(text, key_phrases)
            score = similarity + (phrase_count * 0.05)
            scored.append((score, name, result))
        
        scored.sort(reverse=True)
        top_strategies = [name for _, name, _ in scored[:top_n]]
        results = {name: results[name] for name in top_strategies}
        console.print(f"[green]Showing top {top_n} strategies based on similarity score[/green]\n")
    
    # Display comparison - show full text for each strategy
    console.print("[bold]Comparison: Ground Truth vs OCR Results[/bold]\n")
    
    # Show ground truth first
    console.print("[bold green]GROUND TRUTH TEXT:[/bold green]")
    for level_name, ground_truth_text in ground_truth.items():
        console.print(Panel(ground_truth_text, title=f"[green]{level_name}[/green]", border_style="green"))
    console.print()
    
    # Show each strategy's extracted text
    for strategy_name, result in results.items():
        extracted_text = result["text"]
        description = result["description"]
        
        # Calculate overall similarity
        from scripts.iterate_ocr_strategies import calculate_similarity
        ground_truth_text = " ".join(ground_truth.values())
        overall_sim = calculate_similarity(ground_truth_text, extracted_text) * 100
        
        # Color code based on similarity
        if overall_sim > 30:
            border_color = "green"
        elif overall_sim > 15:
            border_color = "yellow"
        else:
            border_color = "red"
        
        console.print(f"[bold cyan]{description}[/bold cyan]")
        console.print(f"[dim]Similarity: {overall_sim:.1f}%[/dim]")
        console.print(Panel(extracted_text, border_style=border_color))
        console.print()
    
    # Summary
    console.print("[bold]Summary:[/bold]")
    console.print(f"  Character: {character}")
    console.print(f"  Strategies tested: {len(results)}")
    console.print(f"  Ground truth levels: {len(ground_truth)}")
    
    # Best match recommendation
    if results:
        from scripts.iterate_ocr_strategies import calculate_similarity
        
        ground_truth_text = " ".join(ground_truth.values())
        best_name = None
        best_sim = 0
        
        for name, result in results.items():
            sim = calculate_similarity(result["text"], ground_truth_text)
            if sim > best_sim:
                best_sim = sim
                best_name = name
        
        if best_name:
            console.print(f"\n[bold green]Best Match: {results[best_name]['description']}[/bold green]")
            console.print(f"  Similarity: {best_sim:.2%}")


if __name__ == "__main__":
    main()

