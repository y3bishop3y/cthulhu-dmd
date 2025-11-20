#!/usr/bin/env python3
"""
Benchmark OCR strategies to find the best combination for character data extraction.

Tests different OCR preprocessing + engine combinations and scores them (1-100)
based on how well they extract:
- Description (story)
- Motto
- Location
- Special Power levels 1-4
- Dice symbols and game mechanics recognition

Does NOT create JSON files - just displays ranked results.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path (go up 2 levels from scripts/parsing/)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import click
    from difflib import SequenceMatcher
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

try:
    from scripts.models.character import CharacterData, FrontCardData, BackCardData
    from scripts.models.constants import Filename, Season
    from scripts.parsing.multi_ocr import get_all_strategies, OCRStrategy
    from scripts.parsing.text_parsing import clean_ocr_text
except ImportError as e:
    print(f"Error: Missing required import: {e}\n", file=sys.stderr)
    raise

console = Console()


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two texts (0-1)."""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()


def score_name_extraction(extracted: Optional[str], ground_truth: str) -> float:
    """Score name extraction (0-100)."""
    if not extracted:
        return 0.0
    # Exact match
    if extracted.strip().lower() == ground_truth.lower():
        return 100.0
    # Fuzzy match
    sim = similarity_score(extracted, ground_truth)
    return sim * 100.0


def score_location_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score location extraction (0-100)."""
    if not ground_truth:
        return 50.0  # Neutral if no ground truth
    if not extracted:
        return 0.0
    # Exact match
    if extracted.strip().lower() == ground_truth.lower():
        return 100.0
    # Check if key parts match (city, country)
    extracted_parts = set(extracted.lower().split(","))
    truth_parts = set(ground_truth.lower().split(","))
    if extracted_parts.intersection(truth_parts):
        return 80.0
    # Fuzzy match
    sim = similarity_score(extracted, ground_truth)
    return sim * 100.0


def score_motto_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score motto extraction (0-100).
    
    Scoring logic:
    1. Exact match: 100%
    2. Calculate similarity score (most accurate)
    3. Calculate word overlap score (fallback)
    4. Return the higher of the two
    """
    if not ground_truth:
        return 50.0
    if not extracted:
        return 0.0
    
    # Remove quotes/punctuation for comparison (they're often OCR errors)
    extracted_clean = re.sub(r'["\'"]', '', extracted.strip())
    truth_clean = re.sub(r'["\'"]', '', ground_truth.strip())
    
    # Exact match (after cleaning)
    if extracted_clean.lower() == truth_clean.lower():
        return 100.0
    
    # Calculate similarity score (most accurate for mottos)
    sim = similarity_score(extracted_clean, truth_clean)
    similarity_score_value = sim * 100.0
    
    # Calculate word overlap score (fallback)
    truth_words = set(truth_clean.lower().split())
    extracted_words = set(extracted_clean.lower().split())
    if truth_words and extracted_words:
        overlap = len(truth_words.intersection(extracted_words)) / len(truth_words)
        overlap_score = overlap * 80.0
    else:
        overlap_score = 0.0
    
    # Return the higher score (similarity is usually more accurate)
    return max(similarity_score_value, overlap_score)


def score_story_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score story extraction (0-100)."""
    if not ground_truth:
        return 50.0
    if not extracted:
        return 0.0
    # Use similarity score
    sim = similarity_score(extracted, ground_truth)
    return sim * 100.0


def score_special_power_levels(
    extracted_levels: List[Dict], ground_truth_levels: List[Dict]
) -> Tuple[float, Dict[str, float]]:
    """Score special power level extraction (0-100).
    
    Returns:
        (overall_score, level_scores_dict)
    """
    if not ground_truth_levels:
        return 50.0, {}
    
    if not extracted_levels:
        return 0.0, {}
    
    level_scores = {}
    total_score = 0.0
    
    # Score each level (1-4)
    for level_num in range(1, 5):
        truth_level = next(
            (l for l in ground_truth_levels if l.get("level") == level_num), None
        )
        extracted_level = next(
            (l for l in extracted_levels if l.get("level") == level_num), None
        )
        
        if truth_level and extracted_level:
            desc_truth = truth_level.get("description", "").strip()
            desc_extracted = extracted_level.get("description", "").strip()
            
            if desc_extracted:
                sim = similarity_score(desc_extracted, desc_truth)
                score = sim * 100.0
            else:
                score = 0.0
        elif truth_level:
            score = 0.0  # Missing level
        else:
            score = 50.0  # No ground truth for this level
        
        level_scores[f"level_{level_num}"] = score
        total_score += score
    
    overall_score = total_score / 4.0 if level_scores else 0.0
    return overall_score, level_scores


def score_dice_recognition(extracted_text: str) -> float:
    """Score dice symbol recognition (0-100).
    
    Looks for mentions of:
    - Green dice / Green Dice
    - Black dice / Black Dice
    - Dice symbols (@, #, etc.)
    - Red swirl mentions
    """
    text_lower = extracted_text.lower()
    score = 0.0
    checks = 0
    
    # Check for dice mentions
    if "green dice" in text_lower or "green" in text_lower and "dice" in text_lower:
        score += 25.0
    checks += 1
    
    if "black dice" in text_lower or "black" in text_lower and "dice" in text_lower:
        score += 25.0
    checks += 1
    
    # Check for dice symbols (common OCR representations)
    dice_symbols = ["@", "#", "o", "0", "d", "die"]
    if any(symbol in text_lower for symbol in dice_symbols):
        score += 25.0
    checks += 1
    
    # Check for red swirl mentions
    if "red swirl" in text_lower or "red" in text_lower and "swirl" in text_lower:
        score += 25.0
    checks += 1
    
    return score if checks > 0 else 0.0


def score_power_mechanics_recognition(extracted_text: str, ground_truth_levels: List[Dict]) -> float:
    """Score recognition of power mechanics (0-100).
    
    Looks for:
    - "gain" / "add" (dice additions)
    - "instead" (level markers)
    - "heal" / "healing"
    - "reroll"
    - "attack" / "action"
    - Numbers (dice counts, healing amounts)
    """
    text_lower = extracted_text.lower()
    score = 0.0
    checks = 0
    
    # Check for key mechanics
    mechanics = {
        "gain": 10.0,
        "add": 10.0,
        "instead": 15.0,  # Important for level detection
        "heal": 10.0,
        "healing": 10.0,
        "reroll": 10.0,
        "attack": 10.0,
        "action": 10.0,
        "dice": 5.0,
    }
    
    for mechanic, points in mechanics.items():
        if mechanic in text_lower:
            score += points
        checks += 1
    
    # Check for numbers (dice counts, healing amounts)
    import re
    numbers = re.findall(r"\b\d+\b", text_lower)
    if numbers:
        score += min(len(numbers) * 5.0, 15.0)  # Cap at 15 points
    checks += 1
    
    return min(score, 100.0)  # Cap at 100


def benchmark_strategy(
    strategy: OCRStrategy,
    front_image: Path,
    back_image: Path,
    ground_truth: CharacterData,
) -> Dict:
    """Benchmark a single OCR strategy.
    
    Returns:
        Dictionary with scores and extracted data
    """
    try:
        # Extract text
        front_text = strategy.extract(front_image)
        back_text = strategy.extract(back_image)
        
        # Parse front card (pass image path for layout-aware extraction)
        front_data = FrontCardData.parse_from_text(front_text, image_path=front_image)
        
        # Parse back card
        back_data = BackCardData.parse_from_text(back_text)
        
        # Score extractions
        name_score = score_name_extraction(front_data.name, ground_truth.name)
        location_score = score_location_extraction(front_data.location, ground_truth.location)
        motto_score = score_motto_extraction(front_data.motto, ground_truth.motto)
        story_score = score_story_extraction(front_data.story, ground_truth.story)
        
        # Score special power levels
        extracted_levels = []
        if back_data.special_power and back_data.special_power.levels:
            extracted_levels = [
                {"level": l.level, "description": l.description}
                for l in back_data.special_power.levels
            ]
        
        ground_truth_levels = []
        if ground_truth.special_power and ground_truth.special_power.levels:
            ground_truth_levels = [
                {"level": l.level, "description": l.description}
                for l in ground_truth.special_power.levels
            ]
        
        power_score, level_scores = score_special_power_levels(
            extracted_levels, ground_truth_levels
        )
        
        # Score dice recognition
        dice_score = score_dice_recognition(back_text)
        
        # Score mechanics recognition
        mechanics_score = score_power_mechanics_recognition(back_text, ground_truth_levels)
        
        # Calculate overall score (weighted average)
        overall_score = (
            name_score * 0.10 +
            location_score * 0.10 +
            motto_score * 0.10 +
            story_score * 0.15 +
            power_score * 0.30 +  # Most important
            dice_score * 0.10 +
            mechanics_score * 0.15
        )
        
        return {
            "strategy_name": strategy.name,
            "strategy_description": strategy.description,
            "overall_score": round(overall_score, 2),
            "scores": {
                "name": round(name_score, 2),
                "location": round(location_score, 2),
                "motto": round(motto_score, 2),
                "story": round(story_score, 2),
                "special_power": round(power_score, 2),
                "dice_recognition": round(dice_score, 2),
                "mechanics_recognition": round(mechanics_score, 2),
            },
            "level_scores": level_scores,
            "extracted": {
                "name": front_data.name,
                "location": front_data.location,
                "motto": front_data.motto,
                "story": front_data.story[:200] + "..." if front_data.story and len(front_data.story) > 200 else front_data.story,
                "special_power_levels": len(extracted_levels),
            },
            "front_text_length": len(front_text),
            "back_text_length": len(back_text),
        }
    except Exception as e:
        return {
            "strategy_name": strategy.name,
            "strategy_description": strategy.description,
            "overall_score": 0.0,
            "error": str(e),
        }


@click.command()
@click.option(
    "--character",
    type=str,
    required=True,
    help="Character name (e.g., 'adam', 'ahmed')",
)
@click.option(
    "--season",
    type=str,
    default="season1",
    help="Season directory (default: season1)",
)
@click.option(
    "--top",
    type=int,
    default=10,
    help="Show top N strategies (default: 10)",
)
@click.option(
    "--save-results/--no-save-results",
    default=True,
    help="Save results to .generated/benchmark/ directory (default: --save-results)",
)
def main(character: str, season: str, top: int, save_results: bool):
    """Benchmark OCR strategies for character data extraction."""
    
    # Find character directory
    data_dir = project_root / "data" / season / character.lower()
    if not data_dir.exists():
        console.print(f"[red]Error: Character directory not found: {data_dir}[/red]")
        sys.exit(1)
    
    # Load ground truth
    char_json = data_dir / Filename.CHARACTER_JSON
    if not char_json.exists():
        console.print(f"[red]Error: character.json not found: {char_json}[/red]")
        sys.exit(1)
    
    with open(char_json, "r", encoding="utf-8") as f:
        char_data = json.load(f)
    
    ground_truth = CharacterData(**char_data)
    
    # Find images
    front_image = data_dir / Filename.FRONT
    back_image = data_dir / Filename.BACK
    
    # Try .webp first, then .jpg
    if not front_image.exists():
        front_image = data_dir / f"{Filename.FRONT.replace('.webp', '.jpg')}"
    if not back_image.exists():
        back_image = data_dir / f"{Filename.BACK.replace('.webp', '.jpg')}"
    
    if not front_image.exists():
        console.print(f"[red]Error: Front image not found in {data_dir}[/red]")
        sys.exit(1)
    if not back_image.exists():
        console.print(f"[red]Error: Back image not found in {data_dir}[/red]")
        sys.exit(1)
    
    # Get all OCR strategies
    strategies = get_all_strategies()
    
    console.print(f"\n[bold]Benchmarking OCR Strategies for {ground_truth.name}[/bold]")
    console.print(f"Testing {len(strategies)} strategies...\n")
    
    # Benchmark each strategy
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Testing strategies...", total=len(strategies))
        
        for strategy in strategies:
            progress.update(task, description=f"Testing: {strategy.name}")
            result = benchmark_strategy(strategy, front_image, back_image, ground_truth)
            results.append(result)
            progress.advance(task)
    
    # Sort by overall score
    results.sort(key=lambda x: x["overall_score"], reverse=True)
    
    # Save results if requested
    if save_results:
        save_benchmark_results(results, character, season, project_root)
    
    # Display results
    console.print(f"\n[bold green]Top {top} Strategies (Ranked by Overall Score)[/bold green]\n")
    
    # Create summary table
    summary_table = Table(title="Strategy Rankings", show_header=True, header_style="bold magenta")
    summary_table.add_column("Rank", style="cyan", width=5)
    summary_table.add_column("Strategy", style="yellow", width=30)
    summary_table.add_column("Overall", style="green", justify="right", width=10)
    summary_table.add_column("Name", justify="right", width=8)
    summary_table.add_column("Location", justify="right", width=8)
    summary_table.add_column("Motto", justify="right", width=8)
    summary_table.add_column("Story", justify="right", width=8)
    summary_table.add_column("Power", justify="right", width=8)
    summary_table.add_column("Dice", justify="right", width=8)
    summary_table.add_column("Mech", justify="right", width=8)
    
    for i, result in enumerate(results[:top], 1):
        if "error" in result:
            summary_table.add_row(
                str(i),
                result["strategy_name"],
                "[red]ERROR[/red]",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
            )
        else:
            scores = result["scores"]
            # Color code overall score
            overall = result["overall_score"]
            if overall >= 80:
                overall_str = f"[green]{overall:.1f}[/green]"
            elif overall >= 60:
                overall_str = f"[yellow]{overall:.1f}[/yellow]"
            else:
                overall_str = f"[red]{overall:.1f}[/red]"
            
            summary_table.add_row(
                str(i),
                result["strategy_name"][:28],
                overall_str,
                f"{scores['name']:.1f}",
                f"{scores['location']:.1f}",
                f"{scores['motto']:.1f}",
                f"{scores['story']:.1f}",
                f"{scores['special_power']:.1f}",
                f"{scores['dice_recognition']:.1f}",
                f"{scores['mechanics_recognition']:.1f}",
            )
    
    console.print(summary_table)
    
    # Show detailed results for top 3
    console.print(f"\n[bold]Detailed Results for Top 3 Strategies:[/bold]\n")
    
    for i, result in enumerate(results[:3], 1):
        if "error" in result:
            console.print(Panel(f"[red]Error: {result['error']}[/red]", title=f"#{i} {result['strategy_name']}"))
            continue
        
        extracted = result["extracted"]
        scores = result["scores"]
        level_scores = result.get("level_scores", {})
        
        details = f"""
[bold]Overall Score: {result['overall_score']:.2f}/100[/bold]

[bold]Extraction Scores:[/bold]
  Name:        {scores['name']:.1f}/100
  Location:    {scores['location']:.1f}/100
  Motto:       {scores['motto']:.1f}/100
  Story:       {scores['story']:.1f}/100
  Special Power: {scores['special_power']:.1f}/100
  Dice Recognition: {scores['dice_recognition']:.1f}/100
  Mechanics:   {scores['mechanics_recognition']:.1f}/100

[bold]Level-by-Level Scores:[/bold]
"""
        for level_num in range(1, 5):
            level_key = f"level_{level_num}"
            if level_key in level_scores:
                details += f"  Level {level_num}: {level_scores[level_key]:.1f}/100\n"
            else:
                details += f"  Level {level_num}: [red]Not extracted[/red]\n"
        
        details += f"""
[bold]Extracted Data:[/bold]
  Name: {extracted['name'] or '[red]Not found[/red]'}
  Location: {extracted['location'] or '[red]Not found[/red]'}
  Motto: {extracted['motto'] or '[red]Not found[/red]'}
  Story: {extracted['story'] or '[red]Not found[/red]'}
  Special Power Levels Found: {extracted['special_power_levels']}/4

[bold]Text Extraction:[/bold]
  Front card: {result['front_text_length']} characters
  Back card: {result['back_text_length']} characters
"""
        
        console.print(Panel(details, title=f"#{i} {result['strategy_name']}", border_style="blue"))
    
    console.print(f"\n[dim]Tested {len(results)} strategies total[/dim]\n")
    
    if save_results:
        console.print(f"[dim]Results saved to .generated/benchmark/[/dim]\n")


def save_benchmark_results(
    results: List[Dict],
    character: str,
    season: str,
    project_root: Path,
) -> None:
    """Save benchmark results to JSON file.
    
    Args:
        results: List of benchmark result dictionaries
        character: Character name
        season: Season directory name
        project_root: Project root directory
    """
    # Create .generated/benchmark directory
    generated_dir = project_root / ".generated" / "benchmark"
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{season}_{character}_{timestamp}.json"
    output_path = generated_dir / filename
    
    # Prepare data to save
    output_data = {
        "character": character,
        "season": season,
        "timestamp": datetime.now().isoformat(),
        "total_strategies": len(results),
        "top_score": results[0]["overall_score"] if results else 0.0,
        "results": results,
    }
    
    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]✓[/green] Results saved to: {output_path.relative_to(project_root)}")


if __name__ == "__main__":
    main()

