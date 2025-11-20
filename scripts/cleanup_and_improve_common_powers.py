#!/usr/bin/env python3
"""
Comprehensive script to clean up and improve common_powers.json.

This script:
1. Fixes OCR errors in descriptions
2. Improves OCR extraction with better preprocessing
3. Adds enhanced statistics fields
4. Generates a cleaned version of common_powers.json
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Optional

try:
    import click
    from pydantic import BaseModel, Field, computed_field
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/cleanup_and_improve_common_powers.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/cleanup_and_improve_common_powers.py [options]\n\n"
        "Recommended: uv run ./scripts/cleanup_and_improve_common_powers.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.analyze_power_statistics import analyze_power_level
from scripts.models.constants import CommonPower
from scripts.utils.parsing import OCR_CORRECTIONS, fix_number_ocr_errors

console = Console()


# Pydantic models for effect extraction
class ConditionalEffects(BaseModel):
    """Represents conditional effects parsed from a power description."""

    conditions: List[str] = Field(default_factory=list, description="List of condition strings")

    @computed_field
    def is_conditional(self) -> bool:
        """Whether this power has any conditional effects."""
        return len(self.conditions) > 0


class RerollEffects(BaseModel):
    """Represents reroll effects parsed from a power description."""

    rerolls_added: int = Field(default=0, ge=0, description="Number of rerolls added")
    reroll_type: Optional[str] = Field(default=None, description="Type of reroll: 'free' or 'standard'")

    @computed_field
    def has_reroll(self) -> bool:
        """Whether this power adds any rerolls."""
        return self.rerolls_added > 0


class HealingEffects(BaseModel):
    """Represents healing effects parsed from a power description."""

    wounds_healed: int = Field(default=0, ge=0, description="Number of wounds healed")
    stress_healed: int = Field(default=0, ge=0, description="Number of stress healed")

    @computed_field
    def has_healing(self) -> bool:
        """Whether this power has any healing effects."""
        return self.wounds_healed > 0 or self.stress_healed > 0


class DefensiveEffects(BaseModel):
    """Represents defensive effects (damage reduction) parsed from a power description."""

    wound_reduction: int = Field(default=0, ge=0, description="Wound damage reduction")
    sanity_reduction: int = Field(default=0, ge=0, description="Sanity loss reduction")

    @computed_field
    def has_defensive(self) -> bool:
        """Whether this power has any defensive effects."""
        return self.wound_reduction > 0 or self.sanity_reduction > 0

# OCR corrections are loaded from scripts/data/ocr_corrections.toml via get_ocr_corrections()


def cleanup_ocr_errors(text: str) -> str:
    """Apply comprehensive OCR corrections to clean up text."""
    cleaned = text

    # Apply corrections from OCR_CORRECTIONS dictionary (skip problematic ones)
    for error, correction in OCR_CORRECTIONS.items():
        # Skip number/letter confusions that are context-dependent
        if error in ["0", "1"]:
            continue
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(error) + r'\b'
        cleaned = re.sub(pattern, correction, cleaned, flags=re.IGNORECASE)

    # Fix context-aware OCR errors where "I" -> "1" in specific contexts
    # Uses shared patterns from utils/parsing.py
    cleaned = fix_number_ocr_errors(cleaned)

    # Clean up excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Remove garbled uppercase text patterns (like "BRAWLING" at start of description)
    # But preserve power names that are legitimately all caps
    # Use CommonPower enum values converted to uppercase for comparison
    power_names_upper = [power.value.upper() for power in CommonPower]
    for power_name_upper in power_names_upper:
        if cleaned.startswith(power_name_upper + " "):
            cleaned = cleaned[len(power_name_upper) + 1:]
            break

    # Remove repeated phrases (common OCR error)
    # Pattern: "reduce wounds reduce wounds" -> "reduce wounds"
    # Try multiple times to catch nested repetitions
    for _ in range(3):
        cleaned = re.sub(r'\b(\w+(?:\s+\w+){0,4})\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)

    # Fix specific repeated patterns
    cleaned = re.sub(r'\breduce\s+wounds?\s+reduce\s+wounds?\b', 'reduce wounds', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\btaken\s+and\s+loss\s+of\s+taken\s+and\s+loss\s+of\b', 'taken and loss of', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bloss\s+of\s+taken\s+and\s+loss\s+of\b', 'loss of', cleaned, flags=re.IGNORECASE)

    # Fix garbled text patterns like "attacked or railing" -> "attacked or rolling"
    cleaned = re.sub(r'\brailing\b', 'rolling', cleaned, flags=re.IGNORECASE)

    # Fix "loss o!" -> "loss of"
    cleaned = re.sub(r'\bloss\s+o!\s+', 'loss of ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bloss\s+o!\b', 'loss of', cleaned, flags=re.IGNORECASE)

    # Fix "re bce wou" -> "reduce wound"
    cleaned = re.sub(r'\bre\s+bce\s+wou', 'reduce wound', cleaned, flags=re.IGNORECASE)

    # Fix "taken and loss o! taken" -> "taken and loss of"
    cleaned = re.sub(r'\btaken\s+and\s+loss\s+o!\s+taken\b', 'taken and loss of', cleaned, flags=re.IGNORECASE)

    # Fix "loss o! taken" -> "loss of taken"
    cleaned = re.sub(r'\bloss\s+o!\s+taken\b', 'loss of taken', cleaned, flags=re.IGNORECASE)

    # Fix "taken and loss o! ta" -> "taken and loss of"
    cleaned = re.sub(r'\btaken\s+and\s+loss\s+o!\s+ta\b', 'taken and loss of', cleaned, flags=re.IGNORECASE)

    # Remove garbled text like "MASTERY" in middle of sentences
    cleaned = re.sub(r'\b([A-Z]{6,})\s+', '', cleaned)

    # Fix "doesnt" -> "doesn't"
    cleaned = re.sub(r'\bdoesnt\b', "doesn't", cleaned, flags=re.IGNORECASE)

    # Fix "You have 2 free When you attack" -> "You have 2 free rerolls when you attack"
    cleaned = re.sub(r'\bYou have (\d+) free When you attack\b', r'You have \1 free rerolls when you attack', cleaned, flags=re.IGNORECASE)

    # Fix "ANY NUMBER" -> "any number"
    cleaned = re.sub(r'\bANY NUMBER\b', 'any number', cleaned)

    # Fix "figures in your space" repetition
    cleaned = re.sub(r'\b(figures in your space)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)

    # Fix garbled patterns in Toughness Level 4
    # "reduce wound 5 reduce wounds" -> "reduce wounds"
    cleaned = re.sub(r'\breduce\s+wound\s+\d+\s+reduce\s+wounds?\b', 'reduce wounds', cleaned, flags=re.IGNORECASE)

    # Fix "taken and loss o! taken and loss of taken" -> "taken and loss of"
    cleaned = re.sub(r'\btaken\s+and\s+loss\s+o!\s+taken\s+and\s+loss\s+of\s+taken\b', 'taken and loss of', cleaned, flags=re.IGNORECASE)

    # Fix "loss o! taken and loss of taken" -> "loss of"
    cleaned = re.sub(r'\bloss\s+o!\s+taken\s+and\s+loss\s+of\s+taken\b', 'loss of', cleaned, flags=re.IGNORECASE)

    # Fix "taken by 2 and loss You have" -> "taken by 2. You have"
    cleaned = re.sub(r'\btaken\s+by\s+(\d+)\s+and\s+loss\s+You\s+have\b', r'taken by \1. You have', cleaned, flags=re.IGNORECASE)

    # Fix "ity by tw" -> "by 2"
    cleaned = re.sub(r'\bity\s+by\s+tw\b', 'by 2', cleaned, flags=re.IGNORECASE)

    # Fix "stocks Y wll sanity" -> "sanity"
    cleaned = re.sub(r'\bstocks\s+Y\s+wll\s+sanity\b', 'sanity', cleaned, flags=re.IGNORECASE)

    # Fix "by T from of sanity by from ee orrolling" -> "sanity"
    cleaned = re.sub(r'\bby\s+T\s+from\s+of\s+sanity\s+by\s+from\s+ee\s+orrolling\b', 'sanity', cleaned, flags=re.IGNORECASE)

    # Fix "ANY SOURCE. ANY SOURCE," -> "ANY SOURCE."
    cleaned = re.sub(r'\bANY\s+SOURCE\.\s+ANY\s+SOURCE,?\b', 'ANY SOURCE.', cleaned)

    # Fix "for Fire. , ," -> "for Fire."
    cleaned = re.sub(r'\bfor\s+Fire\.\s*,\s*,?\s*$', 'for Fire.', cleaned, flags=re.IGNORECASE)

    # Fix "Brawling Level 2" garbled text: "loss of attacked or rolling" -> "loss of sanity when attacked or rolling"
    cleaned = re.sub(r'\bloss\s+of\s+attacked\s+or\s+rolling\b', 'loss of sanity when attacked or rolling', cleaned, flags=re.IGNORECASE)

    # Fix "taken and loss of taken by 2" -> "taken and loss of sanity by 2"
    cleaned = re.sub(r'\btaken\s+and\s+loss\s+of\s+taken\s+by\s+(\d+)\b', r'taken and loss of sanity by \1', cleaned, flags=re.IGNORECASE)

    # Fix "by 2. You have 1 free reroll when attacked or by 2 rolling" -> "by 2. You have 1 free reroll when attacked or rolling"
    cleaned = re.sub(r'\bby\s+(\d+)\s+rolling\b', r'rolling', cleaned, flags=re.IGNORECASE)

    # Fix "sanity sanity ANY SOURCE" -> "sanity from ANY SOURCE"
    cleaned = re.sub(r'\bsanity\s+sanity\s+ANY\s+SOURCE\b', 'sanity from ANY SOURCE', cleaned, flags=re.IGNORECASE)

    # Fix "ANY SOURCE., for Fire." -> "ANY SOURCE when attacked or rolling for Fire."
    cleaned = re.sub(r'\bANY\s+SOURCE\.\s*,\s*for\s+Fire\.\s*$', 'ANY SOURCE when attacked or rolling for Fire.', cleaned, flags=re.IGNORECASE)

    # Fix "sanity by 1 when. attacked" -> "sanity by 1 when attacked"
    cleaned = re.sub(r'\bsanity\s+by\s+(\d+)\s+when\.\s+attacked\b', r'sanity by \1 when attacked', cleaned, flags=re.IGNORECASE)

    # Remove trailing commas and fix punctuation
    cleaned = re.sub(r',\s*$', '.', cleaned)

    # Fix common sentence-ending issues
    if cleaned and not cleaned.endswith(('.', '!', '?', ',')):
        # If it looks like a complete sentence, add period
        if len(cleaned) > 20 and cleaned[-1].isalpha():
            cleaned += '.'

    return cleaned.strip()


def extract_conditional_effects(description: str) -> ConditionalEffects:
    """Extract conditional effects from description (e.g., 'when attacking', 'while sanity is on red')."""
    conditions: List[str] = []

    desc_lower = description.lower()

    # Check for conditional dice additions
    if "when attacking" in desc_lower or "while attacking" in desc_lower:
        conditions.append("when attacking")

    if "when attacking a target not in your space" in desc_lower:
        conditions.append("when attacking target not in your space")

    if "when attacking a target in your space" in desc_lower:
        conditions.append("when attacking target in your space")

    if "sanity is on red" in desc_lower or "sanity on red" in desc_lower:
        conditions.append("when sanity is on red sanity marker")

    if "when attacked" in desc_lower or "when rolling for fire" in desc_lower:
        conditions.append("when attacked or rolling for fire")

    return ConditionalEffects(conditions=conditions)


def extract_reroll_effects(description: str) -> RerollEffects:
    """Extract reroll effects from description."""
    desc_lower = description.lower()

    rerolls = 0
    reroll_type: Optional[str] = None

    # Pattern: "1 free reroll" or "reroll 1 die"
    match = re.search(r'(\d+)\s+(?:free\s+)?reroll', desc_lower)
    if match:
        rerolls = int(match.group(1))
        reroll_type = "free"

    # Pattern: "reroll 1 die" or "reroll (\d+) dice"
    match = re.search(r'reroll\s+(\d+)\s+(?:die|dice)', desc_lower)
    if match:
        rerolls = int(match.group(1))
        reroll_type = "standard"

    return RerollEffects(rerolls_added=rerolls, reroll_type=reroll_type)


def extract_healing_effects(description: str) -> HealingEffects:
    """Extract healing effects from description."""
    desc_lower = description.lower()

    wounds_healed = 0
    stress_healed = 0

    # Pattern: "heal 1 wound" or "heal (\d+) wounds"
    match = re.search(r'heal\s+(\d+)\s+(?:wound|wounds)', desc_lower)
    if match:
        wounds_healed = int(match.group(1))

    # Pattern: "heal 1 stress" or "heal (\d+) stress"
    match = re.search(r'heal\s+(\d+)\s+stress', desc_lower)
    if match:
        stress_healed = int(match.group(1))

    # Pattern: "heal 1 wound and 1 stress"
    match = re.search(r'heal\s+(\d+)\s+wound.*?(\d+)\s+stress', desc_lower)
    if match:
        wounds_healed = int(match.group(1))
        stress_healed = int(match.group(2))

    return HealingEffects(wounds_healed=wounds_healed, stress_healed=stress_healed)


def extract_defensive_effects(description: str) -> DefensiveEffects:
    """Extract defensive effects (damage reduction, etc.) from description."""
    desc_lower = description.lower()

    wound_reduction = 0
    sanity_reduction = 0

    # Pattern: "reduce wounds taken by 1" or "reduce wounds by (\d+)"
    match = re.search(r'reduce\s+wounds?\s+(?:taken\s+)?by\s+(\d+)', desc_lower)
    if match:
        wound_reduction = int(match.group(1))

    # Pattern: "reduce loss of sanity by 1" or "reduce sanity by (\d+)"
    match = re.search(r'reduce\s+(?:loss\s+of\s+)?sanity\s+by\s+(\d+)', desc_lower)
    if match:
        sanity_reduction = int(match.group(1))

    # Pattern: "reduce wounds and sanity by (\d+)"
    match = re.search(r'reduce\s+wounds?\s+and\s+(?:loss\s+of\s+)?sanity\s+by\s+(\d+)', desc_lower)
    if match:
        wound_reduction = int(match.group(1))
        sanity_reduction = int(match.group(1))

    return DefensiveEffects(wound_reduction=wound_reduction, sanity_reduction=sanity_reduction)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data",
    help="Data directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without updating files",
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="Create backup before updating (default: True)",
)
@click.option(
    "--recalculate-stats",
    is_flag=True,
    default=True,
    help="Recalculate statistics after cleanup (default: True)",
)
def main(data_dir: Path, dry_run: bool, backup: bool, recalculate_stats: bool):
    """Clean up and improve common_powers.json with OCR fixes and enhanced statistics."""
    console.print(
        Panel.fit(
            "[bold cyan]Common Powers Cleanup and Improvement[/bold cyan]\n"
            "Fixing OCR errors, improving descriptions, and enhancing statistics",
            border_style="cyan",
        )
    )

    common_powers_path = data_dir / "common_powers.json"
    if not common_powers_path.exists():
        console.print(f"[red]Error: {common_powers_path} not found![/red]")
        sys.exit(1)

    # Load existing data
    console.print(f"[cyan]Loading {common_powers_path}...[/cyan]")
    with open(common_powers_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[green]✓ Loaded {len(powers_data)} powers[/green]\n")

    # Track changes
    total_fixed = 0
    total_improved = 0

    # Process each power
    for power in powers_data:
        power_name = power["name"]
        console.print(f"[bold cyan]{power_name}[/bold cyan]")

        for level_data in power["levels"]:
            level = level_data["level"]
            original_desc = level_data["description"]

            # Clean up OCR errors
            cleaned_desc = cleanup_ocr_errors(original_desc)

            # Extract additional effects
            conditional_effects = extract_conditional_effects(cleaned_desc)
            reroll_effects = extract_reroll_effects(cleaned_desc)
            healing_effects = extract_healing_effects(cleaned_desc)
            defensive_effects = extract_defensive_effects(cleaned_desc)

            # Update description if changed
            if cleaned_desc != original_desc:
                level_data["description"] = cleaned_desc
                total_fixed += 1
                console.print(f"  Level {level}: [yellow]Fixed OCR errors[/yellow]")
                console.print(f"    Before: {original_desc[:80]}{'...' if len(original_desc) > 80 else ''}")
                console.print(f"    After:  {cleaned_desc[:80]}{'...' if len(cleaned_desc) > 80 else ''}")

            # Recalculate statistics if requested
            if recalculate_stats:
                analysis = analyze_power_level(power_name, level, cleaned_desc)

                # Update statistics with enhanced fields
                stats = level_data.get("statistics", {})
                stats.update({
                    "green_dice_added": analysis.green_dice_added,
                    "black_dice_added": analysis.black_dice_added,
                    "base_expected_successes": round(analysis.base_expected_successes, 3),
                    "enhanced_expected_successes": round(analysis.enhanced_expected_successes, 3),
                    "expected_successes_increase": round(analysis.expected_successes_increase, 3),
                    "expected_successes_percent_increase": round(
                        analysis.expected_successes_percent_increase, 2
                    ),
                    "max_successes_increase": analysis.max_successes_increase,
                    "tentacle_risk": round(analysis.tentacle_risk, 3),
                    "base_tentacle_risk": round(analysis.base_tentacle_risk, 3),
                    # Enhanced fields from Pydantic models
                    "is_conditional": conditional_effects.is_conditional,
                    "conditions": conditional_effects.conditions,
                    "rerolls_added": reroll_effects.rerolls_added,
                    "reroll_type": reroll_effects.reroll_type,
                    "has_reroll": reroll_effects.has_reroll,
                    "wounds_healed": healing_effects.wounds_healed,
                    "stress_healed": healing_effects.stress_healed,
                    "has_healing": healing_effects.has_healing,
                    "wound_reduction": defensive_effects.wound_reduction,
                    "sanity_reduction": defensive_effects.sanity_reduction,
                    "has_defensive": defensive_effects.has_defensive,
                })

                level_data["statistics"] = stats
                level_data["effect"] = analysis.effect

                # Show improvements
                if conditional_effects.is_conditional or reroll_effects.has_reroll or healing_effects.has_healing or defensive_effects.has_defensive:
                    total_improved += 1
                    improvements = []
                    if conditional_effects.is_conditional:
                        improvements.append(f"Conditional: {', '.join(conditional_effects.conditions)}")
                    if reroll_effects.has_reroll:
                        improvements.append(f"Rerolls: {reroll_effects.rerolls_added} ({reroll_effects.reroll_type})")
                    if healing_effects.has_healing:
                        improvements.append(f"Healing: {healing_effects.wounds_healed} wounds, {healing_effects.stress_healed} stress")
                    if defensive_effects.has_defensive:
                        improvements.append(f"Defensive: {defensive_effects.wound_reduction} wounds, {defensive_effects.sanity_reduction} sanity")

                    console.print(f"  Level {level}: [green]Enhanced statistics[/green]")
                    for imp in improvements:
                        console.print(f"    • {imp}")

        console.print()

    # Summary
    console.print("=" * 80)
    console.print("[bold cyan]Summary[/bold cyan]")
    console.print("=" * 80)
    console.print(f"Descriptions fixed: {total_fixed}")
    console.print(f"Statistics enhanced: {total_improved}")

    if dry_run:
        console.print("\n[yellow]DRY RUN - No changes made[/yellow]")
    else:
        # Create backup
        if backup:
            backup_path = common_powers_path.with_suffix(common_powers_path.suffix + ".backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(powers_data, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓ Backup created: {backup_path}[/green]")

        # Write updated data
        with open(common_powers_path, "w", encoding="utf-8") as f:
            json.dump(powers_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Updated {common_powers_path}[/green]")
        console.print(f"[green]✓ Fixed {total_fixed} descriptions[/green]")
        console.print(f"[green]✓ Enhanced {total_improved} power levels with additional statistics[/green]")

    console.print("\n[green]✓ Complete![/green]")


if __name__ == "__main__":
    main()

