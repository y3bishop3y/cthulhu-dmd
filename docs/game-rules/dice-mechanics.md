# Dice Mechanics

## Overview

Cthulhu: Death May Die uses two types of dice: **Black Dice** (standard) and **Green Dice** (bonus). Each die has 6 faces with different symbols and probabilities.

---

## Dice Types

### Black Dice (Standard)
**Always rolled** when making a roll. Each character starts with 3 black dice.

**Face Distribution:**
- 2 × **Success** (pure success, no tentacle)
- 1 × **Success + Tentacle** (success but lose 1 sanity)
- 1 × **Tentacle** (lose 1 sanity)
- 1 × **Elder Sign** (arcane symbol)
- 1 × **Blank** (no effect)

**Probabilities:**
- Success: 3/6 = 50% (2 pure + 1 success+tentacle)
- Tentacle: 2/6 = 33.33% (1 pure + 1 success+tentacle)
- Elder Sign: 1/6 = 16.67%
- Blank: 1/6 = 16.67%

**Reference:** `data/DMD_Rulebook_web.pdf` (pages 11-12)

---

### Green Dice (Bonus)
**Added by powers, cards, or red swirl bonuses.** No limit to number of green dice.

**Face Distribution:**
- 2 × **Blank** (no effect)
- 1 × **Elder Sign** (arcane symbol)
- 2 × **Success** (pure success)
- 1 × **Elder Sign + Success** (both symbols)

**Probabilities:**
- Success: 3/6 = 50% (2 pure + 1 elder+success)
- Elder Sign: 2/6 = 33.33% (1 pure + 1 elder+success)
- Blank: 2/6 = 33.33%
- **Tentacle: 0%** (green dice have NO tentacles!)

**Key Advantage:** Green dice are safer - no tentacle risk!

**Reference:** `data/DMD_Rulebook_web.pdf` (pages 11-12)

---

## Dice Symbols

### Success (⭐)
- Counts as a success for rolls
- Required to succeed at actions
- Can be modified by powers (e.g., "count elder signs as successes")

### Tentacle (🐙)
- **Causes +1 insanity** (advances insanity track)
- Only appears on black dice
- Green dice have NO tentacles (safer!)
- High tentacle risk = closer to death

### Elder Sign (✨)
- Arcane symbol
- Can be converted to successes by some powers
- Example: "Arcane Mastery" - count elder signs as successes

### Blank
- No effect
- Can be rerolled by some powers

---

## Combined Rolls

When rolling multiple dice, probabilities combine:

**Example: 3 Black Dice + 2 Green Dice**
- Expected successes: (3 × 0.5) + (2 × 0.5) = 2.5 successes
- Expected tentacles: 3 × 0.333 = 1.0 tentacle
- Expected elder signs: (3 × 0.167) + (2 × 0.333) = 1.17 elder signs

**Probability of at least 1 success:**
- P(at least 1) = 1 - (0.5³ × 0.5²) = 1 - 0.03125 = 96.875%

**Probability of at least 1 tentacle:**
- P(at least 1) = 1 - (0.667³) = 1 - 0.296 = 70.4%

---

## Power Effects on Dice

### Adding Dice
- Powers can add green dice (safer, no tentacles)
- Powers can add black dice (more successes, but tentacle risk)
- Example: "Marksman Level 2" - gain 2 green dice when attacking

### Converting Symbols
- Powers can convert elder signs to successes
- Example: "Arcane Mastery Level 1" - count 1 elder sign as success

### Rerolls
- Powers can allow rerolling dice
- Useful for avoiding tentacles or getting successes
- Example: "Gate Influence" - 1 free reroll per roll

---

## Implementation

See `scripts/models/game_mechanics.py`:
- `StandardDice` - Black dice model
- `BonusDice` - Green dice model
- `DiceFace` - Individual die face
- `DiceFaceSymbol` - Symbol enum

See `scripts/models/dice_probabilities.py`:
- `SingleDieStats` - Statistics for single die
- `CombinedRollStats` - Statistics for combined rolls
- `DiceProbabilityCalculator` - Probability calculations

---

**Last Updated:** 2024-12-19

