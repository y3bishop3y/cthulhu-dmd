# Power Combination System

## Overview

The Power Combination System calculates combined effects when multiple powers are active simultaneously. This is the foundation for upgrade optimization and synergy analysis.

---

## Goals

1. **Combine additive effects** - Dice additions, rerolls, healing
2. **Detect conflicts** - Exclusive effects like "instead" clauses
3. **Identify synergies** - Powers that enhance each other
4. **Calculate combined statistics** - Overall effectiveness

---

## Power Effect Types

### Additive Effects
Effects that stack together:
- **Dice additions** - "Gain 2 green dice" + "Gain 1 green dice" = 3 green dice
- **Rerolls** - "1 free reroll" + "1 free reroll" = 2 free rerolls
- **Healing** - "Heal 1 stress" + "Heal 1 stress" = 2 stress healed

### Exclusive Effects
Effects that replace each other:
- **"Instead" clauses** - "Instead, gain 2 green dice" replaces previous effect
- **"May" clauses** - Player chooses which effect to use

### Conditional Effects
Effects that depend on conditions:
- **"When attacking"** - Only applies during attacks
- **"While within 1 space of Gate"** - Only applies in specific locations
- **"Per turn"** - Limited to once per turn

### Synergistic Effects
Effects that enhance each other:
- **Elder sign conversion + Green dice** - More elder signs = more successes
- **Rerolls + Tentacle avoidance** - Can reroll tentacles to avoid insanity
- **Free actions + Attack powers** - More attacks = more damage

---

## Combination Rules

### Rule 1: Additive Stacking
**Effects of the same type stack additively.**

Example:
- Power A: "Gain 2 green dice when attacking"
- Power B: "Gain 1 green dice when attacking"
- **Combined:** Gain 3 green dice when attacking

### Rule 2: "Instead" Replacement
**"Instead" clauses replace previous effects of the same type.**

Example:
- Power A Level 1: "Gain 1 green dice"
- Power A Level 2: "Instead, gain 2 green dice"
- **Combined:** Only Level 2 effect applies (2 green dice)

### Rule 3: Conditional Scope
**Effects only apply when conditions are met.**

Example:
- Power A: "Gain 2 green dice when attacking"
- Power B: "Gain 1 green dice when investigating"
- **Combined:** Gain 2 green dice when attacking, 1 green dice when investigating

### Rule 4: Synergy Detection
**Effects that enhance each other are identified as synergies.**

Example:
- Power A: "Count elder signs as successes"
- Power B: "Gain 2 green dice" (green dice have elder signs)
- **Synergy:** More green dice = more elder signs = more successes

---

## Implementation Status

### Phase 1: Foundation ⏳
**Status:** In Progress

**Tasks:**
- [ ] Create `PowerCombination` Pydantic model
- [ ] Implement `PowerCombinationCalculator`
- [ ] Handle additive effects (dice, rerolls, healing)
- [ ] Detect basic conflicts ("instead" clauses)
- [ ] Calculate combined statistics
- [ ] Unit tests for combination logic

**Models Needed:**
- `PowerCombination` - Represents multiple active powers
- `PowerCombinationCalculator` - Calculates combined effects
- `Synergy` / `Conflict` - Interaction types

---

## Example Combinations

### Example 1: Dice Stacking
**Powers:**
- Marksman Level 2: "Gain 2 green dice when attacking"
- Red Swirl Bonus: +1 permanent green dice

**Combined:**
- Base: 3 black dice
- Marksman: +2 green dice
- Red Swirl: +1 green dice
- **Total:** 3 black + 3 green dice

### Example 2: Elder Sign Conversion
**Powers:**
- Arcane Mastery Level 2: "Count any number of elder signs as successes"
- Green Dice Bonus: +2 green dice (more elder signs)

**Combined:**
- More green dice = more elder signs
- Elder signs become successes
- **Result:** Higher success probability

### Example 3: Reroll Synergy
**Powers:**
- Gate Influence Level 1: "1 free reroll per roll"
- High Insanity: Need to avoid tentacles

**Combined:**
- Can reroll tentacles to avoid insanity
- Can reroll blanks to get successes
- **Result:** Better outcomes, lower tentacle risk

---

## Future Enhancements

- **Multi-step combinations** - Powers that trigger other powers
- **Temporal effects** - Effects that last multiple turns
- **Resource costs** - Powers that cost actions/resources
- **Probability calculations** - Combined probability distributions

---

**Last Updated:** 2024-12-19

