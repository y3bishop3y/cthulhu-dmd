#!/usr/bin/env python3
"""
Analyze OCR output with NLP to extract semantic meaning.

Even when OCR text is garbled, NLP can help extract the underlying meaning
and concepts, making it easier to understand what the OCR is trying to say.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path (go up 2 levels from scripts/parsing/)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError as e:
    print(f"Error: Missing required dependency: {e.name}\n", file=sys.stderr)
    raise

try:
    import spacy
except ImportError:
    print("Error: spaCy not installed. Install with: uv add spacy\n", file=sys.stderr)
    sys.exit(1)

from scripts.parsing.multi_ocr import get_all_strategies
from scripts.models.character import CharacterData
from scripts.parsing.nlp_parser import extract_healing_info, get_nlp_model

console = Console()


def load_ground_truth(character_json_path: Path) -> Dict[str, str]:
    """Load ground truth text from character.json."""
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


def extract_semantic_info(text: str, nlp) -> Dict:
    """Extract semantic information from text using NLP.
    
    Args:
        text: OCR extracted text
        nlp: spaCy NLP model
        
    Returns:
        Dictionary with extracted semantic information
    """
    doc = nlp(text)
    
    # Extract entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # Extract key verbs and actions
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    
    # Extract numbers
    numbers = [token.text for token in doc if token.pos_ == "NUM"]
    
    # Extract key phrases
    key_phrases = {
        "heal": "heal" in text.lower(),
        "stress": "stress" in text.lower(),
        "wound": "wound" in text.lower() or "wounds" in text.lower(),
        "investigator": "investigator" in text.lower(),
        "instead": "instead" in text.lower(),
        "end_of_turn": "end of your turn" in text.lower() or "end of turn" in text.lower(),
        "each": "each" in text.lower(),
        "and": " and " in text.lower(),
        "or": " or " in text.lower(),
        "combination": "combination" in text.lower(),
    }
    
    # Extract healing information using our NLP parser
    healing_info = extract_healing_info(doc)
    
    # Extract sentences
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    
    return {
        "entities": entities,
        "verbs": list(set(verbs)),
        "numbers": numbers,
        "key_phrases": key_phrases,
        "healing_info": healing_info,
        "sentences": sentences[:10],  # First 10 sentences
        "word_count": len(doc),
    }


def compare_semantic_info(ground_truth_info: Dict, ocr_info: Dict) -> Dict:
    """Compare semantic information between ground truth and OCR.
    
    Args:
        ground_truth_info: Semantic info from ground truth
        ocr_info: Semantic info from OCR
        
    Returns:
        Comparison results
    """
    comparison = {
        "key_phrases_match": {},
        "verbs_match": {},
        "numbers_match": {},
        "healing_info_match": {},
    }
    
    # Compare key phrases
    gt_phrases = ground_truth_info.get("key_phrases", {})
    ocr_phrases = ocr_info.get("key_phrases", {})
    
    for phrase in gt_phrases:
        gt_value = gt_phrases.get(phrase, False)
        ocr_value = ocr_phrases.get(phrase, False)
        comparison["key_phrases_match"][phrase] = {
            "ground_truth": gt_value,
            "ocr": ocr_value,
            "match": gt_value == ocr_value,
        }
    
    # Compare verbs (check if OCR has similar verbs)
    gt_verbs = set(ground_truth_info.get("verbs", []))
    ocr_verbs = set(ocr_info.get("verbs", []))
    
    comparison["verbs_match"] = {
        "ground_truth": list(gt_verbs),
        "ocr": list(ocr_verbs),
        "common": list(gt_verbs.intersection(ocr_verbs)),
        "missing": list(gt_verbs - ocr_verbs),
        "extra": list(ocr_verbs - gt_verbs),
    }
    
    # Compare numbers
    gt_numbers = set(ground_truth_info.get("numbers", []))
    ocr_numbers = set(ocr_info.get("numbers", []))
    
    comparison["numbers_match"] = {
        "ground_truth": list(gt_numbers),
        "ocr": list(ocr_numbers),
        "common": list(gt_numbers.intersection(ocr_numbers)),
        "missing": list(gt_numbers - ocr_numbers),
    }
    
    # Compare healing info
    gt_healing = ground_truth_info.get("healing_info", {})
    ocr_healing = ocr_info.get("healing_info", {})
    
    comparison["healing_info_match"] = {
        "ground_truth": gt_healing,
        "ocr": ocr_healing,
        "stress_match": gt_healing.get("stress_healed") == ocr_healing.get("stress_healed"),
        "wounds_match": gt_healing.get("wounds_healed") == ocr_healing.get("wounds_healed"),
    }
    
    return comparison


@click.command()
@click.option(
    "--character",
    type=str,
    required=True,
    help="Character name (e.g., 'adam')",
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
    default="tesseract_basic_psm3",
    help="OCR strategy to use (default: tesseract_basic_psm3)",
)
def main(character: str, season: str, strategy: str):
    """Analyze OCR output with NLP to extract semantic meaning."""
    console.print(f"[bold cyan]NLP Analysis of OCR Output[/bold cyan]\n")
    
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
        console.print("[red]Error: No ground truth found[/red]")
        sys.exit(1)
    
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
    
    # Get strategy
    all_strategies = get_all_strategies()
    strategy_obj = next((s for s in all_strategies if s.name == strategy), None)
    
    if not strategy_obj:
        console.print(f"[red]Error: Strategy '{strategy}' not found[/red]")
        console.print(f"[yellow]Available strategies: {[s.name for s in all_strategies]}[/yellow]")
        sys.exit(1)
    
    # Extract text
    console.print(f"[cyan]Extracting text with: {strategy_obj.description}[/cyan]")
    try:
        ocr_text = strategy_obj.extract(back_path)
    except Exception as e:
        console.print(f"[red]Error extracting text: {e}[/red]")
        sys.exit(1)
    
    console.print(f"[green]Extracted {len(ocr_text)} characters[/green]\n")
    
    # Load NLP model
    console.print("[cyan]Loading NLP model...[/cyan]")
    nlp = get_nlp_model()
    
    # Analyze ground truth
    console.print("[cyan]Analyzing ground truth text...[/cyan]")
    ground_truth_text = " ".join(ground_truth.values())
    gt_info = extract_semantic_info(ground_truth_text, nlp)
    
    # Analyze OCR text
    console.print("[cyan]Analyzing OCR extracted text...[/cyan]\n")
    ocr_info = extract_semantic_info(ocr_text, nlp)
    
    # Compare
    comparison = compare_semantic_info(gt_info, ocr_info)
    
    # Display results
    console.print("[bold]Ground Truth Text:[/bold]")
    for level_name, text in ground_truth.items():
        console.print(Panel(text, title=f"[green]{level_name}[/green]", border_style="green"))
    console.print()
    
    console.print("[bold]OCR Extracted Text (first 500 chars):[/bold]")
    console.print(Panel(ocr_text[:500] + "...", border_style="yellow"))
    console.print()
    
    # Key phrases comparison
    console.print("[bold]Key Phrases Detection:[/bold]")
    table = Table(box=box.ROUNDED)
    table.add_column("Phrase", style="cyan")
    table.add_column("Ground Truth", justify="center")
    table.add_column("OCR Found", justify="center")
    table.add_column("Match", justify="center")
    
    for phrase, match_info in comparison["key_phrases_match"].items():
        gt_val = "✓" if match_info["ground_truth"] else "✗"
        ocr_val = "✓" if match_info["ocr"] else "✗"
        match_val = "✓" if match_info["match"] else "✗"
        match_style = "green" if match_info["match"] else "red"
        
        table.add_row(
            phrase,
            gt_val,
            ocr_val,
            f"[{match_style}]{match_val}[/{match_style}]",
        )
    
    console.print(table)
    console.print()
    
    # Verbs comparison
    console.print("[bold]Verbs Comparison:[/bold]")
    console.print(f"  Ground Truth: {', '.join(comparison['verbs_match']['ground_truth'])}")
    console.print(f"  OCR Found: {', '.join(comparison['verbs_match']['ocr'])}")
    console.print(f"  [green]Common: {', '.join(comparison['verbs_match']['common'])}[/green]")
    if comparison["verbs_match"]["missing"]:
        console.print(f"  [red]Missing: {', '.join(comparison['verbs_match']['missing'])}[/red]")
    console.print()
    
    # Numbers comparison
    console.print("[bold]Numbers Comparison:[/bold]")
    console.print(f"  Ground Truth: {', '.join(comparison['numbers_match']['ground_truth'])}")
    console.print(f"  OCR Found: {', '.join(comparison['numbers_match']['ocr'])}")
    console.print(f"  [green]Common: {', '.join(comparison['numbers_match']['common'])}[/green]")
    if comparison["numbers_match"]["missing"]:
        console.print(f"  [red]Missing: {', '.join(comparison['numbers_match']['missing'])}[/red]")
    console.print()
    
    # Healing info comparison
    console.print("[bold]Healing Information Extraction:[/bold]")
    gt_healing = comparison["healing_info_match"]["ground_truth"]
    ocr_healing = comparison["healing_info_match"]["ocr"]
    
    console.print(f"  Ground Truth:")
    console.print(f"    Has healing: {gt_healing.get('has_healing')}")
    console.print(f"    Stress healed: {gt_healing.get('stress_healed')}")
    console.print(f"    Wounds healed: {gt_healing.get('wounds_healed')}")
    console.print(f"    Has OR: {gt_healing.get('has_or')}")
    console.print(f"    Has AND: {gt_healing.get('has_and')}")
    console.print(f"    Is flexible: {gt_healing.get('is_flexible')}")
    console.print(f"    Is each: {gt_healing.get('is_each')}")
    
    console.print(f"  OCR Extracted:")
    console.print(f"    Has healing: {ocr_healing.get('has_healing')}")
    console.print(f"    Stress healed: {ocr_healing.get('stress_healed')}")
    console.print(f"    Wounds healed: {ocr_healing.get('wounds_healed')}")
    console.print(f"    Has OR: {ocr_healing.get('has_or')}")
    console.print(f"    Has AND: {ocr_healing.get('has_and')}")
    console.print(f"    Is flexible: {ocr_healing.get('is_flexible')}")
    console.print(f"    Is each: {ocr_healing.get('is_each')}")
    
    # Match indicators
    stress_match = comparison["healing_info_match"]["stress_match"]
    wounds_match = comparison["healing_info_match"]["wounds_match"]
    
    console.print(f"\n  [green]Matches:[/green]")
    console.print(f"    Stress amount: {'✓' if stress_match else '✗'}")
    console.print(f"    Wounds amount: {'✓' if wounds_match else '✗'}")
    
    # Show extracted sentences
    console.print("[bold]Key Sentences Extracted by NLP:[/bold]")
    for i, sentence in enumerate(ocr_info.get("sentences", [])[:5], 1):
        console.print(f"  {i}. {sentence[:150]}...")
    console.print()
    
    # Summary
    console.print("[bold]Summary:[/bold]")
    key_phrase_matches = sum(1 for m in comparison["key_phrases_match"].values() if m["match"])
    total_phrases = len(comparison["key_phrases_match"])
    console.print(f"  Key phrases matched: {key_phrase_matches}/{total_phrases}")
    console.print(f"  Verbs matched: {len(comparison['verbs_match']['common'])}/{len(comparison['verbs_match']['ground_truth'])}")
    console.print(f"  Numbers matched: {len(comparison['numbers_match']['common'])}/{len(comparison['numbers_match']['ground_truth'])}")
    
    # Semantic accuracy assessment
    console.print("\n[bold]Semantic Accuracy Assessment:[/bold]")
    
    # Check if OCR is extracting the right TYPE of power
    if ocr_healing.get("has_healing") and gt_healing.get("has_healing"):
        console.print("  [green]✓ Correctly identified as healing power[/green]")
    elif ocr_healing.get("has_healing") and not gt_healing.get("has_healing"):
        console.print("  [yellow]⚠ OCR thinks it's healing, but ground truth says it's not[/yellow]")
        console.print("  [dim]   (OCR may be reading wrong section of card)[/dim]")
    elif not ocr_healing.get("has_healing") and gt_healing.get("has_healing"):
        console.print("  [red]✗ OCR missed healing power[/red]")
    else:
        console.print("  [green]✓ Correctly identified as non-healing power[/green]")
    
    # Check if key concepts are present
    important_phrases = ["instead", "gain", "green", "dice", "sanity", "red", "swirl"]
    found_important = [p for p in important_phrases if ocr_info["key_phrases"].get(p.replace("_", ""), False) or p in ocr_text.lower()]
    
    if found_important:
        console.print(f"  [green]✓ Found important concepts: {', '.join(found_important)}[/green]")
    
    # Overall assessment
    if key_phrase_matches >= total_phrases * 0.7:
        console.print("\n[green]✓ Good semantic match - OCR extracted key concepts correctly[/green]")
    elif key_phrase_matches >= total_phrases * 0.4:
        console.print("\n[yellow]⚠ Partial semantic match - OCR extracted some concepts[/yellow]")
    else:
        console.print("\n[red]✗ Poor semantic match - OCR missed most key concepts[/red]")
        console.print("  [dim]Consider trying different OCR strategies or preprocessing[/dim]")


if __name__ == "__main__":
    main()

