#!/usr/bin/env python3
"""
Test script to demonstrate parsing improvements.

This script tests various OCR text scenarios and shows how the improved
parsing handles edge cases, OCR errors, and different phrasings.
"""

import sys
from pathlib import Path

try:
    from scripts.analyze_power_statistics import (
        DiceAddition,
        ElderSignConversion,
        ActionAddition,
        analyze_power_level,
    )
    from scripts.utils.parsing import (
        clean_ocr_text,
        normalize_dice_symbols,
        normalize_red_swirl_symbols,
        extract_power_level_number,
        is_likely_power_description,
        validate_power_description,
    )
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use:\n"
        "  uv run ./scripts/test_parsing_improvements.py\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Test cases: (raw_text, expected_parsing_result)
TEST_CASES = [
    # OCR error corrections
    ("goin 2 green dice", "gain 2 green dice"),
    ("isone your space", "is on your space"),
    ("Yi as success", "elder signs as success"),
    
    # Dice variations
    ("Gain 2 Green dice when attacking", "2 green dice"),
    ("gain 2 green dice", "2 green dice"),
    ("add 1 black dice", "1 black dice"),
    ("2 additional green dice", "2 green dice"),
    
    # Elder sign variations
    ("count 1 Arcane as success", "1 elder sign"),
    ("may count any number of Elder signs as 2 successes each", "any number, 2x"),
    ("Heal 1 stress for each elder sign you count as a success", "any number"),
    
    # Action variations
    ("You may perform 1 free attack per turn", "1 free attack"),
    ("gain 1 action", "1 action"),
    ("1 bonus action", "1 action"),
    
    # Range/conditional effects
    ("You may attack a target 1 space away", "range extension"),
    ("You may attack a target 1 additional space away (2 total)", "range extension"),
]


def test_ocr_cleaning():
    """Test OCR text cleaning improvements."""
    console.print("[bold cyan]Testing OCR Text Cleaning[/bold cyan]\n")
    
    test_texts = [
        "goin 2 green dice isone your space",
        "Yi as success | ~ artifacts",
        "Gain 2 Green dice when attacking",
        "count 1 Arcane (elder sign) as success",
    ]
    
    table = Table(title="OCR Cleaning Results")
    table.add_column("Original", style="red")
    table.add_column("Cleaned", style="green")
    
    for text in test_texts:
        cleaned = clean_ocr_text(text)
        table.add_row(text, cleaned)
    
    console.print(table)
    console.print()


def test_dice_parsing():
    """Test dice addition parsing improvements."""
    console.print("[bold cyan]Testing Dice Addition Parsing[/bold cyan]\n")
    
    test_descriptions = [
        "Gain 2 Green dice when attacking a target not in your space",
        "gain 2 green dice",
        "add 1 black dice",
        "2 additional green dice",
        "gain 1 extra black dice",
    ]
    
    table = Table(title="Dice Parsing Results")
    table.add_column("Description", style="cyan")
    table.add_column("Green Dice", justify="right")
    table.add_column("Black Dice", justify="right")
    
    for desc in test_descriptions:
        dice = DiceAddition.from_description(desc)
        table.add_row(desc, str(dice.green_dice), str(dice.black_dice))
    
    console.print(table)
    console.print()


def test_elder_sign_parsing():
    """Test elder sign conversion parsing improvements."""
    console.print("[bold cyan]Testing Elder Sign Conversion Parsing[/bold cyan]\n")
    
    test_descriptions = [
        "count 1 Arcane as success",
        "may count any number of Elder signs as 2 successes each",
        "Heal 1 stress for each elder sign you count as a success",
        "count 1 elder sign as success",
    ]
    
    table = Table(title="Elder Sign Parsing Results")
    table.add_column("Description", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Successes Each", justify="right")
    table.add_column("Any Number", justify="center")
    
    for desc in test_descriptions:
        elder = ElderSignConversion.from_description(desc)
        count_str = str(elder.elder_signs_as_successes) if elder.elder_signs_as_successes < 999 else "any"
        table.add_row(
            desc,
            count_str,
            str(elder.successes_per_elder_sign),
            "✓" if elder.converts_any_number else "✗",
        )
    
    console.print(table)
    console.print()


def test_action_parsing():
    """Test action addition parsing improvements."""
    console.print("[bold cyan]Testing Action Addition Parsing[/bold cyan]\n")
    
    test_descriptions = [
        "You may perform 1 free attack per turn against a target in your space",
        "gain 1 action",
        "1 bonus action",
        "may perform 2 free attacks",
    ]
    
    table = Table(title="Action Parsing Results")
    table.add_column("Description", style="cyan")
    table.add_column("Actions Added", justify="right")
    table.add_column("Action Type", style="green")
    
    for desc in test_descriptions:
        action = ActionAddition.from_description(desc)
        table.add_row(desc, str(action.actions_added), action.action_type)
    
    console.print(table)
    console.print()


def test_power_level_analysis():
    """Test full power level analysis."""
    console.print("[bold cyan]Testing Full Power Level Analysis[/bold cyan]\n")
    
    test_powers = [
        ("Marksman", 2, "Gain 2 Green dice when attacking a target not in your space"),
        ("Marksman", 4, "You may perform 1 free attack per turn against a target in your space"),
        ("Arcane Mastery", 1, "When making any roll, you may count 1 Arcane (elder sign) as a success."),
        ("Arcane Mastery", 4, "You may count any number of Elder signs as 2 successes each."),
    ]
    
    table = Table(title="Power Level Analysis Results")
    table.add_column("Power", style="cyan")
    table.add_column("Level", justify="right")
    table.add_column("Description", style="yellow")
    table.add_column("Effect", style="green")
    table.add_column("Success Increase", justify="right")
    
    for power_name, level, description in test_powers:
        analysis = analyze_power_level(power_name, level, description)
        success_inc = f"+{analysis.expected_successes_increase:.2f}"
        if analysis.action_addition.actions_added > 0:
            success_inc += f" (+{analysis.action_addition.actions_added} action)"
        table.add_row(
            power_name,
            str(level),
            description[:50] + "..." if len(description) > 50 else description,
            analysis.effect,
            success_inc,
        )
    
    console.print(table)
    console.print()


def test_validation():
    """Test power description validation."""
    console.print("[bold cyan]Testing Power Description Validation[/bold cyan]\n")
    
    test_descriptions = [
        ("You may attack a target 1 space away", True),
        ("Gain 2 Green dice when attacking", True),
        ("", False),  # Too short
        ("abc", False),  # Too short
        ("Gain 2 Green dice ||| artifacts", False),  # OCR artifacts
    ]
    
    table = Table(title="Validation Results")
    table.add_column("Description", style="cyan")
    table.add_column("Valid", justify="center")
    table.add_column("Issues", style="red")
    
    for desc, expected_valid in test_descriptions:
        is_valid, issues = validate_power_description(desc)
        valid_str = "✓" if is_valid else "✗"
        issues_str = "; ".join(issues) if issues else "None"
        table.add_row(desc[:60] + "..." if len(desc) > 60 else desc, valid_str, issues_str)
    
    console.print(table)
    console.print()


def main():
    """Run all parsing improvement tests."""
    console.print("[bold]Parsing Improvements Test Suite[/bold]\n")
    console.print("=" * 80 + "\n")
    
    test_ocr_cleaning()
    test_dice_parsing()
    test_elder_sign_parsing()
    test_action_parsing()
    test_power_level_analysis()
    test_validation()
    
    console.print("[bold green]✓ All parsing tests completed![/bold green]")


if __name__ == "__main__":
    main()

