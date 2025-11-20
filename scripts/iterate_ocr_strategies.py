#!/usr/bin/env python3
"""
Iterative OCR strategy testing and comparison.

Tests multiple preprocessing + OCR engine combinations and compares
results against ground truth to find best strategies.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

from scripts.parsing.multi_ocr import get_all_strategies, test_all_strategies, combine_results
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
    """Calculate similarity score between two texts.
    
    Uses word overlap (Jaccard similarity).
    
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
    
    # Word overlap
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def find_key_phrases(text: str, phrases: List[str]) -> int:
    """Count how many key phrases appear in text.
    
    Args:
        text: Text to search
        phrases: List of key phrases to find
        
    Returns:
        Number of phrases found
    """
    text_lower = text.lower()
    count = 0
    for phrase in phrases:
        if phrase.lower() in text_lower:
            count += 1
    return count


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
    "--top-n",
    type=int,
    default=5,
    help="Show top N strategies (default: 5)",
)
@click.option(
    "--combine",
    is_flag=True,
    help="Test combined results from multiple strategies",
)
def main(character: str, season: str, top_n: int, combine: bool):
    """Test all OCR strategies and find best ones."""
    console.print(f"[bold cyan]Iterative OCR Strategy Testing[/bold cyan]\n")
    
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
        console.print("[yellow]Warning: No ground truth found[/yellow]")
        console.print("Make sure special_power levels are populated.\n")
        ground_truth_text = ""
    else:
        ground_truth_text = " ".join(ground_truth.values())
        console.print("[bold]Ground Truth:[/bold]")
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
        console.print(f"[red]Error: Back card image not found[/red]")
        sys.exit(1)
    
    console.print(f"[green]Testing on: {back_path}[/green]\n")
    
    # Get all strategies
    strategies = get_all_strategies()
    console.print(f"[cyan]Testing {len(strategies)} OCR strategies...[/cyan]\n")
    
    # Test all strategies
    results = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Testing strategies...", total=len(strategies))
        
        for strategy in strategies:
            progress.update(task, description=f"Testing {strategy.name}...")
            try:
                text = strategy.extract(back_path)
                results[strategy.name] = {
                    "text": text,
                    "strategy": strategy,
                }
            except Exception as e:
                console.print(f"[red]Error in {strategy.name}: {e}[/red]")
                results[strategy.name] = {
                    "text": "",
                    "strategy": strategy,
                }
            progress.update(task, advance=1)
    
    # Calculate scores
    scored_results = []
    key_phrases = ["heal", "stress", "wound", "investigator", "instead", "end of your turn"]
    
    for name, result in results.items():
        text = result["text"]
        
        # Calculate similarity
        similarity = calculate_similarity(text, ground_truth_text) if ground_truth_text else 0.0
        
        # Count key phrases
        phrase_count = find_key_phrases(text, key_phrases)
        
        # Score: similarity + phrase bonus
        score = similarity + (phrase_count * 0.05)
        
        scored_results.append({
            "name": name,
            "description": result["strategy"].description,
            "text": text,
            "similarity": similarity,
            "phrase_count": phrase_count,
            "score": score,
            "length": len(text),
        })
    
    # Sort by score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Display results
    table = Table(title=f"OCR Strategy Comparison (Top {top_n})", box=box.ROUNDED)
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Strategy", style="cyan", max_width=30)
    table.add_column("Similarity", justify="right", style="green")
    table.add_column("Key Phrases", justify="right", style="yellow")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Text Preview", style="dim", max_width=50)
    
    for i, result in enumerate(scored_results[:top_n], 1):
        similarity = result["similarity"]
        phrase_count = result["phrase_count"]
        score = result["score"]
        text_preview = result["text"][:80] + "..." if len(result["text"]) > 80 else result["text"]
        
        # Color code similarity
        if similarity > 0.3:
            sim_style = "green"
        elif similarity > 0.15:
            sim_style = "yellow"
        else:
            sim_style = "red"
        
        table.add_row(
            str(i),
            result["description"],
            f"[{sim_style}]{similarity:.2%}[/{sim_style}]",
            str(phrase_count),
            f"[bold]{score:.3f}[/bold]",
            text_preview,
        )
    
    console.print(table)
    
    # Best strategy
    if scored_results:
        best = scored_results[0]
        console.print(f"\n[bold green]Best Strategy: {best['description']}[/bold green]")
        console.print(f"  Similarity: {best['similarity']:.2%}")
        console.print(f"  Key Phrases Found: {best['phrase_count']}/{len(key_phrases)}")
        console.print(f"  Score: {best['score']:.3f}")
        
        console.print(f"\n[bold]Best Result Text:[/bold]")
        console.print(f"  {best['text'][:200]}...")
    
    # Test combinations
    if combine and len(scored_results) > 1:
        console.print("\n[bold cyan]Testing Combined Results...[/bold cyan]")
        
        # Get top 3 strategies
        top_strategies = {r["name"]: r["text"] for r in scored_results[:3]}
        
        combined_longest = combine_results(top_strategies, method="longest")
        combined_merge = combine_results(top_strategies, method="merge")
        
        sim_longest = calculate_similarity(combined_longest, ground_truth_text) if ground_truth_text else 0.0
        sim_merge = calculate_similarity(combined_merge, ground_truth_text) if ground_truth_text else 0.0
        
        console.print(f"\n  Combined (longest): {sim_longest:.2%} similarity")
        console.print(f"  Combined (merge): {sim_merge:.2%} similarity")
        
        if sim_longest > best["similarity"] or sim_merge > best["similarity"]:
            console.print("[green]✓ Combination improves results![/green]")
    
    # Recommendations
    if scored_results and best["similarity"] < 0.3:
        console.print("\n[yellow]Recommendations:[/yellow]")
        console.print("  1. Consider cloud OCR APIs (Google Vision, AWS Textract)")
        console.print("  2. Try manual preprocessing for specific images")
        console.print("  3. Focus on post-processing/NLP to fix errors")
        console.print("  4. Use best strategy for initial extraction, then refine")


if __name__ == "__main__":
    main()

