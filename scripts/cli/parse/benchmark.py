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
from typing import Dict, Final, List, Optional, Tuple

# Add project root to path (go up 2 levels from scripts/parsing/)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from difflib import SequenceMatcher

    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

try:
    from scripts.cli.parse.benchmark_models import (
        BENCHMARK_CATEGORIES,
        CATEGORY_SPECIAL_POWER,
        CATEGORY_STORY,
        BenchmarkResult,
        BenchmarkResultsSummary,
        BestStrategyPerCategory,
        ComponentStrategies,
        ExtractedData,
        ExtractionScores,
        LevelScores,
    )
    from scripts.cli.parse.parsing_constants import (
        BLACK_DICE_PATTERNS,
        DICE_SYMBOL_CONTEXT_PATTERNS,
        DICE_SYMBOLS,
        GREEN_DICE_PATTERNS,
        MIN_DICE_SYMBOL_COUNT,
        MIN_SANITY_MENTION_COUNT,
        RED_SWIRL_PATTERNS,
        SANITY_ON_A_PATTERN,
        WORD_PROXIMITY_THRESHOLD_CLOSE,
        WORD_PROXIMITY_THRESHOLD_FAR,
    )
    from scripts.core.parsing.ocr_engines import OCRStrategy, get_all_strategies
    from scripts.models.character import BackCardData, CharacterData, FrontCardData
    from scripts.models.constants import FileExtension, Filename
except ImportError as e:
    print(f"Error: Missing required import: {e}\n", file=sys.stderr)
    raise

console = Console()

# Constants
BENCHMARK_DIR: Final[str] = ".generated/benchmark"
DEFAULT_TOP_RESULTS: Final[int] = 10
DEFAULT_SEASON: Final[str] = "season1"

# Scoring constants
SCORE_MIN: Final[float] = 0.0
SCORE_MAX: Final[float] = 100.0
SCORE_NEUTRAL: Final[float] = 50.0  # Neutral score when no ground truth
SCORE_EXACT_MATCH: Final[float] = 100.0
SCORE_PARTIAL_MATCH: Final[float] = 80.0  # Partial match (e.g., location parts match)
SCORE_SIMILARITY_MULTIPLIER: Final[float] = 100.0  # Convert similarity ratio (0-1) to score (0-100)
SCORE_OVERLAP_MULTIPLIER: Final[float] = 80.0  # Multiplier for word overlap score

# Similarity score constants
SIMILARITY_MIN: Final[float] = 0.0
SIMILARITY_MAX: Final[float] = 1.0
SIMILARITY_PERFECT_MATCH: Final[float] = 1.0

# Dice recognition scoring constants
DICE_SCORE_INCREMENT: Final[float] = 25.0  # Points for finding dice/swirl mentions
DICE_SCORE_BONUS: Final[float] = 10.0  # Bonus points for finding both dice and sanity
DICE_SCORE_VISUAL_BONUS: Final[float] = 15.0  # Bonus for finding both visually

# Mechanics recognition scoring constants
MECHANICS_SCORE_BASE: Final[float] = 10.0  # Base points for key mechanics
MECHANICS_SCORE_IMPORTANT: Final[float] = 15.0  # Points for important mechanics (e.g., "instead")
MECHANICS_SCORE_MINOR: Final[float] = 5.0  # Points for minor mechanics (e.g., "dice")
MECHANICS_SCORE_NUMBER: Final[float] = 5.0  # Points per number found
MECHANICS_SCORE_NUMBER_CAP: Final[float] = 15.0  # Maximum points for numbers

# Power level scoring constants
POWER_LEVEL_COUNT: Final[int] = 4  # Number of power levels (1-4)
POWER_LEVEL_DIVISOR: Final[float] = 4.0  # Divisor for calculating average level score


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two texts (0-1)."""
    if not text1 and not text2:
        return SIMILARITY_PERFECT_MATCH
    if not text1 or not text2:
        return SIMILARITY_MIN
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()


def score_name_extraction(extracted: Optional[str], ground_truth: str) -> float:
    """Score name extraction (0-100)."""
    if not extracted:
        return SCORE_MIN
    # Exact match
    if extracted.strip().lower() == ground_truth.lower():
        return SCORE_EXACT_MATCH
    # Fuzzy match
    sim = similarity_score(extracted, ground_truth)
    return sim * SCORE_SIMILARITY_MULTIPLIER


def score_location_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score location extraction (0-100)."""
    if not ground_truth:
        return SCORE_NEUTRAL
    if not extracted:
        return SCORE_MIN
    # Exact match
    if extracted.strip().lower() == ground_truth.lower():
        return SCORE_EXACT_MATCH
    # Check if key parts match (city, country)
    extracted_parts = set(extracted.lower().split(","))
    truth_parts = set(ground_truth.lower().split(","))
    if extracted_parts.intersection(truth_parts):
        return SCORE_PARTIAL_MATCH
    # Fuzzy match
    sim = similarity_score(extracted, ground_truth)
    return sim * SCORE_SIMILARITY_MULTIPLIER


def score_motto_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score motto extraction (0-100).

    Scoring logic:
    1. Exact match: 100%
    2. Calculate similarity score (most accurate)
    3. Calculate word overlap score (fallback)
    4. Return the higher of the two
    """
    if not ground_truth:
        return SCORE_NEUTRAL
    if not extracted:
        return SCORE_MIN

    # Remove quotes/punctuation for comparison (they're often OCR errors)
    extracted_clean = re.sub(r'["\'"]', "", extracted.strip())
    truth_clean = re.sub(r'["\'"]', "", ground_truth.strip())

    # Exact match (after cleaning)
    if extracted_clean.lower() == truth_clean.lower():
        return SCORE_EXACT_MATCH

    # Calculate similarity score (most accurate for mottos)
    sim = similarity_score(extracted_clean, truth_clean)
    similarity_score_value = sim * SCORE_SIMILARITY_MULTIPLIER

    # Calculate word overlap score (fallback)
    truth_words = set(truth_clean.lower().split())
    extracted_words = set(extracted_clean.lower().split())
    if truth_words and extracted_words:
        overlap = len(truth_words.intersection(extracted_words)) / len(truth_words)
        overlap_score = overlap * SCORE_OVERLAP_MULTIPLIER
    else:
        overlap_score = SCORE_MIN

    # Return the higher score (similarity is usually more accurate)
    return max(similarity_score_value, overlap_score)


def score_story_extraction(extracted: Optional[str], ground_truth: Optional[str]) -> float:
    """Score story extraction (0-100)."""
    if not ground_truth:
        return SCORE_NEUTRAL
    if not extracted:
        return SCORE_MIN
    # Use similarity score
    sim = similarity_score(extracted, ground_truth)
    return sim * SCORE_SIMILARITY_MULTIPLIER


def score_special_power_levels(
    extracted_levels: List[Dict], ground_truth_levels: List[Dict]
) -> Tuple[float, Dict[str, float]]:
    """Score special power level extraction (0-100).

    Returns:
        (overall_score, level_scores_dict)
    """
    if not ground_truth_levels:
        return SCORE_NEUTRAL, {}

    if not extracted_levels:
        return SCORE_MIN, {}

    level_scores = {}
    total_score = SCORE_MIN

    # Score each level (1-4)
    for level_num in range(1, POWER_LEVEL_COUNT + 1):
        truth_level = next(
            (level for level in ground_truth_levels if level.get("level") == level_num), None
        )
        extracted_level = next(
            (level for level in extracted_levels if level.get("level") == level_num), None
        )

        if truth_level and extracted_level:
            desc_truth = truth_level.get("description", "").strip()
            desc_extracted = extracted_level.get("description", "").strip()

            if desc_extracted:
                sim = similarity_score(desc_extracted, desc_truth)
                score = sim * SCORE_SIMILARITY_MULTIPLIER
            else:
                score = SCORE_MIN
        elif truth_level:
            score = SCORE_MIN  # Missing level
        else:
            score = SCORE_NEUTRAL  # No ground truth for this level

        level_scores[f"level_{level_num}"] = score
        total_score += score

    overall_score = total_score / POWER_LEVEL_DIVISOR if level_scores else SCORE_MIN
    return overall_score, level_scores


def score_dice_recognition(
    extracted_text: str,
    parsed_power_levels: Optional[List[Dict]] = None,
    back_image_path: Optional[Path] = None,
) -> float:
    """Score dice symbol recognition (0-100).

    Uses both OCR text analysis AND visual detection of dice/swirl symbols in the image.

    Looks for mentions of:
    - Green dice / Green Dice (handles OCR errors like "PSOne", "goin")
    - Black dice / Black Dice
    - Dice symbols (@, #, ®, etc.)
    - Red swirl mentions (handles OCR errors like "oR", "red" + "sanity")

    Args:
        extracted_text: Raw OCR text
        parsed_power_levels: Optional list of parsed power level dicts (more reliable than raw OCR)
        back_image_path: Optional path to back card image for visual symbol detection
    """
    import re

    text_lower = extracted_text.lower()
    score = SCORE_MIN
    max_score = SCORE_MAX

    # If we have parsed power levels, check those too (more reliable)
    if parsed_power_levels:
        parsed_text = " ".join(
            [level.get("description", "") for level in parsed_power_levels]
        ).lower()
        text_lower = text_lower + " " + parsed_text

    # Check for green dice mentions (handle OCR errors)
    green_found = any(re.search(pattern, text_lower) for pattern in GREEN_DICE_PATTERNS)

    # Also check if "green" and "dice" appear separately (within reasonable distance)
    green_pos = text_lower.find("green")
    dice_pos = text_lower.find("dice")
    if (
        green_pos != -1
        and dice_pos != -1
        and abs(green_pos - dice_pos) < WORD_PROXIMITY_THRESHOLD_CLOSE
    ):
        green_found = True

    # Check for "gain" + symbol patterns (common: "gain @" = gain green dice)
    if any(re.search(pattern, text_lower) for pattern in DICE_SYMBOL_CONTEXT_PATTERNS[:2]):
        green_found = True

    if green_found:
        score += DICE_SCORE_INCREMENT

    # Check for black dice mentions
    black_found = any(re.search(pattern, text_lower) for pattern in BLACK_DICE_PATTERNS)

    # Also check if "black" and "dice" appear separately
    black_pos = text_lower.find("black")
    if (
        black_pos != -1
        and dice_pos != -1
        and abs(black_pos - dice_pos) < WORD_PROXIMITY_THRESHOLD_CLOSE
    ):
        black_found = True

    if black_found:
        score += DICE_SCORE_INCREMENT

    # Check for dice symbols (common OCR representations)
    # Check if symbols appear near "gain", "dice", or power descriptions
    symbol_found = any(symbol in text_lower for symbol in DICE_SYMBOLS) or any(
        re.search(pattern, text_lower) for pattern in DICE_SYMBOL_CONTEXT_PATTERNS
    )

    # Also check for standalone symbols that appear multiple times (likely dice mentions)
    symbol_counts = sum(text_lower.count(symbol) for symbol in DICE_SYMBOLS)
    if symbol_counts >= MIN_DICE_SYMBOL_COUNT:
        symbol_found = True

    if symbol_found:
        score += DICE_SCORE_INCREMENT

    # Check for red swirl mentions (handle OCR errors)
    # Red swirls are often mentioned with "sanity" and "red"
    red_swirl_found = any(re.search(pattern, text_lower) for pattern in RED_SWIRL_PATTERNS)

    # Also check if "red" and "swirl" appear separately (within reasonable distance)
    red_pos = text_lower.find("red")
    swirl_pos = text_lower.find("swirl")
    if (
        red_pos != -1
        and swirl_pos != -1
        and abs(red_pos - swirl_pos) < WORD_PROXIMITY_THRESHOLD_CLOSE
    ):
        red_swirl_found = True

    # Check for "sanity" + "red" pattern (common way red swirls are mentioned)
    sanity_pos = text_lower.find("sanity")
    if sanity_pos != -1:
        # Look for "red" near "sanity" (within threshold)
        if red_pos != -1 and abs(sanity_pos - red_pos) < WORD_PROXIMITY_THRESHOLD_FAR:
            red_swirl_found = True
        # Also check for "swirl" near "sanity"
        if swirl_pos != -1 and abs(sanity_pos - swirl_pos) < WORD_PROXIMITY_THRESHOLD_FAR:
            red_swirl_found = True
        # Check for patterns like "sanity is on a [red/swirl]"
        if re.search(
            SANITY_ON_A_PATTERN, text_lower[sanity_pos : sanity_pos + WORD_PROXIMITY_THRESHOLD_FAR]
        ):
            red_swirl_found = True

    # If we find "sanity" mentioned multiple times, it's likely discussing red swirls
    sanity_count = text_lower.count("sanity")
    if sanity_count >= MIN_SANITY_MENTION_COUNT and (red_pos != -1 or swirl_pos != -1):
        red_swirl_found = True

    if red_swirl_found:
        score += DICE_SCORE_INCREMENT

    # Bonus: If we found dice symbols AND sanity mentions, likely discussing dice + red swirls
    if symbol_found and sanity_pos != -1:
        score = min(score + DICE_SCORE_BONUS, max_score)

    # Visual detection: If we have the image, use computer vision to detect symbols directly
    if back_image_path and back_image_path.exists():
        try:
            from scripts.core.parsing.dice_detection import detect_dice_and_swirls

            visual_results = detect_dice_and_swirls(back_image_path)

            # If visual detection finds dice/swirls, boost the score
            if visual_results["dice_found"]:
                # We found dice visually - give full credit for dice detection
                if not green_found and not black_found and not symbol_found:
                    score += DICE_SCORE_INCREMENT
                else:
                    score = max(score, DICE_SCORE_INCREMENT)

            if visual_results["red_swirl_found"]:
                # We found red swirls visually - give full credit
                if not red_swirl_found:
                    score += DICE_SCORE_INCREMENT
                else:
                    score = max(score, min(score + DICE_SCORE_BONUS, max_score))

            # If visual detection found both, we're very confident
            if visual_results["dice_found"] and visual_results["red_swirl_found"]:
                score = min(score + DICE_SCORE_VISUAL_BONUS, max_score)
        except Exception:
            # If visual detection fails, fall back to OCR-only scoring
            pass

    return min(score, max_score)


def score_power_mechanics_recognition(
    extracted_text: str, ground_truth_levels: List[Dict]
) -> float:
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
    score = SCORE_MIN
    checks = 0

    # Check for key mechanics
    mechanics = {
        "gain": MECHANICS_SCORE_BASE,
        "add": MECHANICS_SCORE_BASE,
        "instead": MECHANICS_SCORE_IMPORTANT,
        "heal": MECHANICS_SCORE_BASE,
        "healing": MECHANICS_SCORE_BASE,
        "reroll": MECHANICS_SCORE_BASE,
        "attack": MECHANICS_SCORE_BASE,
        "action": MECHANICS_SCORE_BASE,
        "dice": MECHANICS_SCORE_MINOR,
    }

    for mechanic, points in mechanics.items():
        if mechanic in text_lower:
            score += points
        checks += 1

    # Check for numbers (dice counts, healing amounts)
    import re

    numbers = re.findall(r"\b\d+\b", text_lower)
    if numbers:
        score += min(len(numbers) * MECHANICS_SCORE_NUMBER, MECHANICS_SCORE_NUMBER_CAP)
    checks += 1

    return min(score, SCORE_MAX)


def benchmark_strategy(
    strategy: OCRStrategy,
    front_image: Path,
    back_image: Path,
    ground_truth: CharacterData,
) -> BenchmarkResult:
    """Benchmark a single OCR strategy.

    Returns:
        BenchmarkResult with scores and extracted data
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
                {"level": level.level, "description": level.description}
                for level in back_data.special_power.levels
            ]

        ground_truth_levels = []
        if ground_truth.special_power and ground_truth.special_power.levels:
            ground_truth_levels = [
                {"level": level.level, "description": level.description}
                for level in ground_truth.special_power.levels
            ]

        power_score, level_scores_dict = score_special_power_levels(
            extracted_levels, ground_truth_levels
        )

        # Score dice recognition (pass parsed power levels and image path for visual detection)
        dice_score = score_dice_recognition(back_text, extracted_levels, back_image)

        # Score mechanics recognition
        mechanics_score = score_power_mechanics_recognition(back_text, ground_truth_levels)

        # Calculate overall score (weighted average)
        overall_score = (
            name_score * 0.10
            + location_score * 0.10
            + motto_score * 0.10
            + story_score * 0.15
            + power_score * 0.30  # Most important
            + dice_score * 0.10
            + mechanics_score * 0.15
        )

        # Build Pydantic models
        scores = ExtractionScores(
            name=name_score,
            location=location_score,
            motto=motto_score,
            story=story_score,
            special_power=power_score,
            dice_recognition=dice_score,
            mechanics_recognition=mechanics_score,
        )

        level_scores = LevelScores.from_dict(level_scores_dict)

        extracted = ExtractedData(
            name=front_data.name,
            location=front_data.location,
            motto=front_data.motto,
            story=front_data.story,
            special_power_levels=len(extracted_levels),
        )

        return BenchmarkResult(
            strategy_name=strategy.name,
            strategy_description=strategy.description,
            overall_score=overall_score,
            scores=scores,
            level_scores=level_scores,
            extracted=extracted,
            front_text_length=len(front_text),
            back_text_length=len(back_text),
        )
    except Exception as e:
        return BenchmarkResult(
            strategy_name=strategy.name,
            strategy_description=strategy.description,
            overall_score=0.0,
            error=str(e),
        )


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
    default=DEFAULT_SEASON,
    help=f"Season directory (default: {DEFAULT_SEASON})",
)
@click.option(
    "--top",
    type=int,
    default=DEFAULT_TOP_RESULTS,
    help=f"Show top N strategies (default: {DEFAULT_TOP_RESULTS})",
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

    with open(char_json, encoding="utf-8") as f:
        char_data = json.load(f)

    ground_truth = CharacterData(**char_data)

    # Find images - try multiple extensions
    front_image = None
    back_image = None

    # Try different extensions in order of preference
    for ext in [FileExtension.WEBP, FileExtension.JPG, FileExtension.JPEG]:
        candidate_front = data_dir / f"front{ext.value}"
        candidate_back = data_dir / f"back{ext.value}"
        if candidate_front.exists() and front_image is None:
            front_image = candidate_front
        if candidate_back.exists() and back_image is None:
            back_image = candidate_back

    # Fallback to default if not found
    if front_image is None:
        front_image = data_dir / Filename.FRONT
    if back_image is None:
        back_image = data_dir / Filename.BACK

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
    results: List[BenchmarkResult] = []
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
    results.sort(key=lambda x: x.overall_score, reverse=True)

    # Create summary
    summary = BenchmarkResultsSummary(
        character=character,
        season=season,
        timestamp=datetime.now().isoformat(),
        total_strategies=len(results),
        top_score=results[0].overall_score if results else 0.0,
        results=results,
    )

    # Save results if requested
    benchmark_file_path = None
    if save_results:
        benchmark_file_path = save_benchmark_results(summary, project_root)

        # Automatically update optimal strategies config
        try:
            from scripts.utils.optimal_ocr import update_optimal_strategies_from_benchmark

            console.print("\n[cyan]Updating optimal strategies config...[/cyan]")
            config = update_optimal_strategies_from_benchmark(benchmark_file_path)
            console.print("[green]✓[/green] Updated optimal strategies config")
            console.print(f"  Front card: {config['front_card_strategy']['strategy_name']}")
            console.print(f"  Back card: {config['back_card_strategy']['strategy_name']}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not update optimal strategies: {e}[/yellow]")

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
        if result.error:
            summary_table.add_row(
                str(i),
                result.strategy_name,
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
            # Color code overall score
            overall = result.overall_score
            if overall >= 80:
                overall_str = f"[green]{overall:.1f}[/green]"
            elif overall >= 60:
                overall_str = f"[yellow]{overall:.1f}[/yellow]"
            else:
                overall_str = f"[red]{overall:.1f}[/red]"

            summary_table.add_row(
                str(i),
                result.strategy_name[:28],
                overall_str,
                f"{result.scores.name:.1f}",
                f"{result.scores.location:.1f}",
                f"{result.scores.motto:.1f}",
                f"{result.scores.story:.1f}",
                f"{result.scores.special_power:.1f}",
                f"{result.scores.dice_recognition:.1f}",
                f"{result.scores.mechanics_recognition:.1f}",
            )

    console.print(summary_table)

    # Show detailed results for top 3
    console.print("\n[bold]Detailed Results for Top 3 Strategies:[/bold]\n")

    for i, result in enumerate(results[:3], 1):
        if result.error:
            console.print(
                Panel(f"[red]Error: {result.error}[/red]", title=f"#{i} {result.strategy_name}")
            )
            continue

        details = f"""
[bold]Overall Score: {result.overall_score:.2f}/100[/bold]

[bold]Extraction Scores:[/bold]
  Name:        {result.scores.name:.1f}/100
  Location:    {result.scores.location:.1f}/100
  Motto:       {result.scores.motto:.1f}/100
  Story:       {result.scores.story:.1f}/100
  Special Power: {result.scores.special_power:.1f}/100
  Dice Recognition: {result.scores.dice_recognition:.1f}/100
  Mechanics:   {result.scores.mechanics_recognition:.1f}/100

[bold]Level-by-Level Scores:[/bold]
  Level 1: {result.level_scores.level_1:.1f}/100
  Level 2: {result.level_scores.level_2:.1f}/100
  Level 3: {result.level_scores.level_3:.1f}/100
  Level 4: {result.level_scores.level_4:.1f}/100

[bold]Extracted Data:[/bold]
  Name: {result.extracted.name or "[red]Not found[/red]"}
  Location: {result.extracted.location or "[red]Not found[/red]"}
  Motto: {result.extracted.motto or "[red]Not found[/red]"}
  Story: {result.extracted.story or "[red]Not found[/red]"}
  Special Power Levels Found: {result.extracted.special_power_levels}/4

[bold]Text Extraction:[/bold]
  Front card: {result.front_text_length} characters
  Back card: {result.back_text_length} characters
"""

        console.print(Panel(details, title=f"#{i} {result.strategy_name}", border_style="blue"))

    console.print(f"\n[dim]Tested {len(results)} strategies total[/dim]\n")

    if save_results:
        console.print(f"[dim]Results saved to {BENCHMARK_DIR}/[/dim]\n")


def save_benchmark_results(
    summary: BenchmarkResultsSummary,
    project_root: Path,
) -> Path:
    """Save benchmark results to JSON file.

    Args:
        summary: BenchmarkResultsSummary with all results
        project_root: Project root directory
    """
    # Create benchmark directory
    generated_dir = project_root / BENCHMARK_DIR
    generated_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{summary.season}_{summary.character}_{timestamp}{FileExtension.JSON.value}"
    output_path = generated_dir / filename

    # Convert to dict for JSON serialization
    output_data = {
        "character": summary.character,
        "season": summary.season,
        "timestamp": summary.timestamp,
        "total_strategies": summary.total_strategies,
        "top_score": summary.top_score,
        "results": [result.to_dict() for result in summary.results],
    }

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓[/green] Results saved to: {output_path.relative_to(project_root)}")
    return output_path


def find_best_strategies_per_category(
    results: List[BenchmarkResult],
) -> Dict[str, BestStrategyPerCategory]:
    """Find the best strategy for each category from benchmark results.

    Args:
        results: List of benchmark results

    Returns:
        Dictionary mapping category to best strategy
    """
    best_strategies: Dict[str, BestStrategyPerCategory] = {}

    for category in BENCHMARK_CATEGORIES:
        best_score = -1.0
        best_result: Optional[BenchmarkResult] = None

        for result in results:
            if result.error:
                continue

            score = getattr(result.scores, category, 0.0)
            if score > best_score:
                best_score = score
                best_result = result

        if best_result:
            # Get extracted value for this category
            extracted_value = getattr(
                best_result.extracted,
                category.replace("_recognition", "").replace(
                    "special_power", "special_power_levels"
                ),
                None,
            )

            best_strategies[category] = BestStrategyPerCategory(
                strategy_name=best_result.strategy_name,
                strategy_description=best_result.strategy_description,
                score=best_score,
                extracted=extracted_value,
            )

    return best_strategies


def benchmark_hybrid_strategy(
    best_strategies: Dict[str, BestStrategyPerCategory],
    strategies_dict: Dict[str, OCRStrategy],
    front_image: Path,
    back_image: Path,
    ground_truth: CharacterData,
) -> BenchmarkResult:
    """Benchmark a hybrid strategy that uses best strategy for each category.

    Args:
        best_strategies: Dictionary of best strategies per category
        strategies_dict: Dictionary mapping strategy names to OCRStrategy objects
        front_image: Path to front card image
        back_image: Path to back card image
        ground_truth: Ground truth character data

    Returns:
        BenchmarkResult with scores and extracted data for hybrid strategy
    """
    # Extract text using best strategy for story (front card)
    story_strategy_name = (
        best_strategies.get(CATEGORY_STORY).strategy_name
        if best_strategies.get(CATEGORY_STORY)
        else None
    )
    if story_strategy_name and story_strategy_name in strategies_dict:
        story_strategy = strategies_dict[story_strategy_name]
        front_text = story_strategy.extract(front_image)
    else:
        # Fallback to first available strategy
        front_text = list(strategies_dict.values())[0].extract(front_image)

    # Extract text using best strategy for special power (back card)
    power_strategy_name = (
        best_strategies.get(CATEGORY_SPECIAL_POWER).strategy_name
        if best_strategies.get(CATEGORY_SPECIAL_POWER)
        else None
    )
    if power_strategy_name and power_strategy_name in strategies_dict:
        power_strategy = strategies_dict[power_strategy_name]
        back_text = power_strategy.extract(back_image)
    else:
        # Fallback to first available strategy
        back_text = list(strategies_dict.values())[0].extract(back_image)

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
            {"level": level.level, "description": level.description}
            for level in back_data.special_power.levels
        ]

    ground_truth_levels = []
    if ground_truth.special_power and ground_truth.special_power.levels:
        ground_truth_levels = [
            {"level": level.level, "description": level.description}
            for level in ground_truth.special_power.levels
        ]

    power_score, level_scores_dict = score_special_power_levels(
        extracted_levels, ground_truth_levels
    )

    # Score dice recognition
    dice_score = score_dice_recognition(back_text, extracted_levels, back_image)

    # Score mechanics recognition
    mechanics_score = score_power_mechanics_recognition(back_text, ground_truth_levels)

    # Calculate overall score (weighted average)
    overall_score = (
        name_score * 0.10
        + location_score * 0.10
        + motto_score * 0.10
        + story_score * 0.15
        + power_score * 0.30
        + dice_score * 0.10
        + mechanics_score * 0.15
    )

    # Build strategy description
    strategy_parts = []
    if story_strategy_name:
        strategy_parts.append(f"Story: {story_strategy_name}")
    if power_strategy_name:
        strategy_parts.append(f"Power: {power_strategy_name}")

    # Build Pydantic models
    scores = ExtractionScores(
        name=name_score,
        location=location_score,
        motto=motto_score,
        story=story_score,
        special_power=power_score,
        dice_recognition=dice_score,
        mechanics_recognition=mechanics_score,
    )

    level_scores = LevelScores.from_dict(level_scores_dict)

    extracted = ExtractedData(
        name=front_data.name,
        location=front_data.location,
        motto=front_data.motto,
        story=front_data.story,
        special_power_levels=len(extracted_levels),
    )

    component_strategies = ComponentStrategies(
        story=story_strategy_name,
        special_power=power_strategy_name,
    )

    return BenchmarkResult(
        strategy_name="hybrid_best_per_category",
        strategy_description="Hybrid: " + " | ".join(strategy_parts),
        overall_score=overall_score,
        scores=scores,
        level_scores=level_scores,
        extracted=extracted,
        front_text_length=len(front_text),
        back_text_length=len(back_text),
        component_strategies=component_strategies,
    )


if __name__ == "__main__":
    main()
