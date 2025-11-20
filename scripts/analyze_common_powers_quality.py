#!/usr/bin/env python3
"""
Analyze common_powers.json for quality issues:
1. OCR errors in descriptions
2. Incomplete or garbled text
3. Statistics accuracy
4. Missing or incorrect effects
5. Suggestions for improvements
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/analyze_common_powers_quality.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/analyze_common_powers_quality.py [options]\n\n"
        "Recommended: uv run ./scripts/analyze_common_powers_quality.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Common OCR errors and corrections
OCR_CORRECTIONS: Dict[str, str] = {
    "freee": "free",
    "goin": "gain",
    "ison": "is on",
    "figuresures": "figures",
    "detectitve": "detective",
    "santiy": "sanity",
    "railing": "rolling",
    "aff": "and",
    "BINS": "When",
    "I enemy": "1 enemy",
    "wou": "wound",
    "o!": "of",
    "re bce": "reduce",
    "rero": "reroll",
}

# Key phrases loaded from TOML config
_parsing_config = get_parsing_patterns()
KEY_PHRASES = {
    "dice": _parsing_config.key_phrases_dice,
    "elder sign": _parsing_config.key_phrases_elder_sign,
    "success": _parsing_config.key_phrases_success,
    "attack": _parsing_config.key_phrases_attack,
    "action": _parsing_config.key_phrases_action,
    "reroll": _parsing_config.key_phrases_reroll,
    "sneak": _parsing_config.key_phrases_sneak,
    "heal": _parsing_config.key_phrases_heal,
    "wound": _parsing_config.key_phrases_wound,
    "stress": _parsing_config.key_phrases_stress,
}


def check_ocr_errors(description: str) -> List[str]:
    """Check for common OCR errors in description."""
    errors = []
    desc_lower = description.lower()

    for error, correction in OCR_CORRECTIONS.items():
        if error.lower() in desc_lower and correction.lower() not in desc_lower:
            errors.append(f"'{error}' should be '{correction}'")

    return errors


def check_description_quality(description: str) -> Dict[str, any]:
    """Check description quality and completeness."""
    issues = []
    suggestions = []

    # Check for garbled text
    if re.search(r"[A-Z]{5,}", description):
        issues.append("Contains garbled uppercase text (likely OCR error)")

    if re.search(r"\s{3,}", description):
        issues.append("Contains excessive whitespace")

    # Check for incomplete sentences
    if not description.endswith((".", "!", "?")) and len(description) > 20:
        # Might be incomplete
        if not description.endswith("."):
            issues.append("Description doesn't end with punctuation (might be incomplete)")

    # Check for placeholder text
    if "Not found" in description or "TODO" in description:
        issues.append("Contains placeholder text")

    # Check length
    if len(description) < 20:
        issues.append(f"Description is very short ({len(description)} chars)")
        suggestions.append("May be incomplete - check source")

    # Check for repeated words (OCR artifact)
    words = description.split()
    if len(words) > 0:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        repeated = [word for word, count in word_counts.items() if count > 3 and len(word) > 3]
        if repeated:
            issues.append(f"Contains repeated words: {', '.join(repeated[:3])}")

    return {"issues": issues, "suggestions": suggestions}


def check_statistics_consistency(level_data: CommonPowerLevelData) -> List[str]:
    """Check if statistics are consistent with description."""
    issues = []
    stats = level_data.statistics
    description = level_data.description.lower()
    effect = level_data.effect.lower()

    green_dice = stats.green_dice_added
    black_dice = stats.black_dice_added

    # Check if description mentions dice but stats don't reflect it
    # Use key phrases from config
    dice_phrases = parsing_config.key_phrases_dice
    elder_sign_phrases = parsing_config.key_phrases_elder_sign
    success_phrases = parsing_config.key_phrases_success
    attack_phrases = parsing_config.key_phrases_attack
    action_phrases = parsing_config.key_phrases_action

    # Check for green/black dice mentions
    has_green_dice_mention = any(phrase in description for phrase in dice_phrases if "green" in phrase.lower())
    has_black_dice_mention = any(phrase in description for phrase in dice_phrases if "black" in phrase.lower())

    if has_green_dice_mention and green_dice == 0:
        # Check if it's conditional (e.g., "when attacking")
        if "when" not in description and "while" not in description:
            issues.append("Description mentions green dice but green_dice_added is 0")

    if has_black_dice_mention and black_dice == 0:
        if "when" not in description and "while" not in description:
            issues.append("Description mentions black dice but black_dice_added is 0")

    # Check elder sign conversion
    has_elder_sign_mention = any(phrase in description for phrase in elder_sign_phrases)
    has_success_mention = any(phrase in description for phrase in success_phrases)

    if has_elder_sign_mention:
        if has_success_mention and "count" in description:
            # Should have elder sign conversion effect
            has_elder_in_effect = any(phrase in effect for phrase in elder_sign_phrases)
            has_success_in_effect = any(phrase in effect for phrase in success_phrases)
            if not has_elder_in_effect and not has_success_in_effect:
                issues.append("Description mentions counting elder signs as successes but effect doesn't reflect this")

    # Check action additions
    has_attack_mention = any(phrase in description for phrase in attack_phrases)
    has_action_mention = any(phrase in description for phrase in action_phrases)
    has_free_mention = "free" in description

    if has_free_mention and (has_attack_mention or has_action_mention):
        has_attack_in_effect = any(phrase in effect for phrase in attack_phrases)
        has_action_in_effect = any(phrase in effect for phrase in action_phrases)
        if not has_attack_in_effect and not has_action_in_effect:
            issues.append("Description mentions free attack/action but effect doesn't reflect this")

    return issues


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default="data",
    help="Data directory",
)
@click.option(
    "--power",
    type=str,
    help="Analyze specific power only",
)
@click.option(
    "--show-all",
    is_flag=True,
    help="Show all descriptions, not just issues",
)
def main(data_dir: Path, power: Optional[str], show_all: bool):
    """Analyze common_powers.json for quality issues."""
    console.print(
        Panel.fit(
            "[bold cyan]Common Powers Quality Analysis[/bold cyan]\n"
            "Checking OCR errors, completeness, and statistics consistency",
            border_style="cyan",
        )
    )

    # Load JSON
    json_path = data_dir / "common_powers.json"
    if not json_path.exists():
        console.print(f"[red]Error: {json_path} not found![/red]")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        powers_data = json.load(f)

    console.print(f"[cyan]Analyzing {len(powers_data)} powers...[/cyan]\n")

    # Track overall statistics
    total_issues = 0
    total_levels = 0
    powers_with_issues = []

    # Analyze each power
    powers_to_analyze = [p for p in powers_data if not power or p["name"] == power]

    for power_data in powers_to_analyze:
        power_name = power_data["name"]
        power_issues = []

        console.print(f"\n[bold cyan]{power_name}[/bold cyan]")
        console.print("=" * 80)

        for level_dict in power_data["levels"]:
            # Parse level data into Pydantic model
            level_data = CommonPowerLevelData(
                level=level_dict["level"],
                description=level_dict["description"],
                statistics=PowerLevelStatistics(**level_dict.get("statistics", {})),
                effect=level_dict.get("effect", ""),
            )
            level = level_data.level
            description = level_data.description
            stats = level_data.statistics
            effect = level_data.effect

            total_levels += 1

            # Check OCR errors
            ocr_errors = check_ocr_errors(description)

            # Check quality
            quality = check_description_quality(description)

            # Check statistics consistency
            stat_issues = check_statistics_consistency(level_data)

            # Combine all issues
            all_issues = ocr_errors + quality["issues"] + stat_issues

            if all_issues or show_all:
                console.print(f"\n[bold]Level {level}:[/bold]")

                if show_all or all_issues:
                    # Show description (truncated if long)
                    desc_display = description[:200] + "..." if len(description) > 200 else description
                    console.print(f"[yellow]Description:[/yellow] {desc_display}")

                # Show issues
                if all_issues:
                    console.print(f"[red]Issues ({len(all_issues)}):[/red]")
                    for issue in all_issues:
                        console.print(f"  • {issue}")
                    total_issues += len(all_issues)
                    power_issues.append(level)

                # Show statistics
                if stats and (show_all or all_issues):
                    console.print("[cyan]Statistics:[/cyan]")
                    console.print(
                        f"  Green dice: {stats.get('green_dice_added', 0)}, "
                        f"Black dice: {stats.get('black_dice_added', 0)}"
                    )
                    console.print(
                        f"  Expected successes: {stats.get('base_expected_successes', 0):.2f} → "
                        f"{stats.get('enhanced_expected_successes', 0):.2f} "
                        f"(+{stats.get('expected_successes_increase', 0):.2f}, "
                        f"{stats.get('expected_successes_percent_increase', 0):.1f}%)"
                    )
                    console.print(f"  Effect: {effect}")

                # Show suggestions
                if quality["suggestions"]:
                    console.print("[magenta]Suggestions:[/magenta]")
                    for suggestion in quality["suggestions"]:
                        console.print(f"  • {suggestion}")

        if power_issues:
            powers_with_issues.append((power_name, power_issues))

    # Summary
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]Summary[/bold cyan]")
    console.print("=" * 80)
    console.print(f"Total levels analyzed: {total_levels}")
    console.print(f"Total issues found: {total_issues}")
    console.print(f"Powers with issues: {len(powers_with_issues)}")

    if powers_with_issues:
        console.print("\n[bold yellow]Powers needing attention:[/bold yellow]")
        for power_name, levels in powers_with_issues:
            console.print(f"  • {power_name}: Levels {', '.join(map(str, levels))}")

    console.print("\n[green]✓ Analysis complete![/green]")
    console.print("\n[cyan]Recommendations:[/cyan]")
    console.print("  1. Fix OCR errors using the corrections dictionary")
    console.print("  2. Re-extract descriptions from character cards with improved OCR")
    console.print("  3. Verify statistics match descriptions")
    console.print("  4. Add missing effect descriptions")


if __name__ == "__main__":
    main()

