# Insanity Track Mechanics

## Overview

The insanity/madness track is a critical system that affects power upgrades, tentacle risk, and survival. Each tentacle rolled advances the track, and reaching red swirls grants level-up opportunities.

---

## Track Structure

### Layout
- **20 slots** (player starts at slot 1)
- **Death threshold:** Slot 21 (one more tentacle = death from madness)
- **Red Swirls (Level-Ups):** Slots 5, 9, 13, 16, 19, 20 (6 total)
- **Green Dice Bonuses:** Red swirls 2, 4, 5, 6 grant permanent green dice

### Red Swirl Positions
| Red Swirl # | Slot Position | Grants Green Dice? |
|-------------|---------------|-------------------|
| 1 | 5 | No |
| 2 | 9 | **Yes** |
| 3 | 13 | No |
| 4 | 16 | **Yes** |
| 5 | 19 | **Yes** |
| 6 | 20 | **Yes** |

**Total:** 6 level-up opportunities, 4 green dice bonuses

---

## Insanity Progression

### How Insanity Increases
- **Tentacle rolled:** +1 insanity (on any roll)
- **Enemy tentacle:** +1 insanity (when enemies attack)
- **Other effects:** Some cards/effects may add insanity

### ⚠️ CRITICAL RULE: Red Swirl Stop Behavior

**When you hit a red swirl during a roll, you STOP there and don't accumulate tentacles past it for that roll.**

**Example:**
- **Current insanity:** Slot 4
- **Roll 3 tentacles:** Would normally go to slot 7
- **BUT:** Red swirl is at slot 5
- **Result:** Stop at slot 5, gain level-up benefit immediately
- **Remaining tentacles:** Ignored for this roll (don't go to 6, 7)
- **Next roll:** Tentacles matter again until next red swirl

**Why this matters:**
- You get the level-up benefit immediately (can use upgraded power on next action)
- You don't "overshoot" red swirls and waste tentacles
- Each roll/action can only cross one red swirl threshold

### Example Progression

**Red swirl stop behavior:**
- **Action 1:** Attack at slot 4, roll 3 tentacles
  - Would go to slot 7, but stops at slot 5 (red swirl)
  - Gain level-up benefit immediately
  - Remaining 2 tentacles ignored for this action
- **Action 2:** Attack again at slot 5 (with 1 power upgrade)
  - Roll 2 tentacles → goes to slot 7
  - No red swirl in range, so tentacles accumulate normally
- **Action 3:** Attack at slot 7, roll 3 tentacles
  - Would go to slot 10, but stops at slot 9 (red swirl)
  - Gain level-up + green dice benefit immediately
  - Remaining 1 tentacle ignored for this action

---

## Level-Up System

### Key Constraint
- **Only 6 level-ups total** (one per red swirl)
- Player cannot level up every power to max
- Must choose which powers to upgrade strategically

### Level-Up Process
1. Reach a red swirl slot (5, 9, 13, 16, 19, or 20)
2. Choose ONE power to level up (special or common)
3. That power gains +1 level (max level 4 for common powers)
4. If red swirl grants green dice, gain +1 permanent green dice bonus

### Green Dice Bonuses
- **Red Swirl 2 (slot 9):** +1 green dice
- **Red Swirl 4 (slot 16):** +1 green dice
- **Red Swirl 5 (slot 19):** +1 green dice
- **Red Swirl 6 (slot 20):** +1 green dice
- **Total:** Up to 4 permanent green dice bonuses

---

## Impact on Gameplay

### Tentacle Risk Analysis
- **Tentacles = Insanity = Closer to Death**
- Each tentacle brings player 1 slot closer to death
- At slot 20, one tentacle = death
- **Risk increases exponentially** as insanity rises

### Green Dice Value
- **Green dice have NO tentacles** (only successes, elder signs, blanks)
- Green dice = safer rolls = less insanity risk
- Gaining green dice = reducing tentacle probability

### Reroll Value
- **Rerolls can avoid tentacles** or get successes
- High insanity = rerolls become more valuable
- Can reroll tentacles to try for successes/elder signs
- Can reroll blanks to try for successes

### Power Upgrade Strategy
- **Only 6 upgrades total** - must choose carefully
- Early upgrades = more time to benefit
- Late upgrades = less time to benefit
- Must balance offense vs defense vs utility

---

## Examples

### Example 1: Early Game
- **Insanity:** Slot 3
- **Tentacles until Red Swirl 1:** 2 tentacles
- **Strategy:** Can afford to take risks, roll aggressively
- **Upgrade Priority:** Offensive powers (more time to benefit)

### Example 2: Mid Game
- **Insanity:** Slot 12
- **Red Swirls Reached:** 2 (slots 5, 9)
- **Green Dice Bonus:** +1 (from red swirl 2)
- **Tentacles until Red Swirl 3:** 1 tentacle
- **Strategy:** Getting riskier, consider defensive powers
- **Upgrade Priority:** Balanced (some offense, some defense)

### Example 3: Late Game
- **Insanity:** Slot 19
- **Red Swirls Reached:** 5 (slots 5, 9, 13, 16, 19)
- **Green Dice Bonus:** +3 (from red swirls 2, 4, 5)
- **Tentacles until Death:** 2 tentacles
- **Strategy:** Very risky, prioritize survival
- **Upgrade Priority:** Defensive/healing powers

### Example 4: Maximum Power
- **Insanity:** Slot 20
- **Red Swirls Reached:** 6 (all red swirls)
- **Green Dice Bonus:** +4 (all green dice bonuses)
- **Tentacles until Death:** 1 tentacle
- **Strategy:** Extremely dangerous, one tentacle = death
- **Upgrade Priority:** Survival powers (healing, defensive, rerolls)

---

## Implementation

See `scripts/models/game_mechanics.py`:
- `InsanityTrack` - Insanity track model
- `take_tentacles_in_roll()` - Handles red swirl stop behavior
- `take_tentacle()` - Basic tentacle accumulation
- Red swirl tracking and green dice bonus calculation

---

**Last Updated:** 2024-12-19

