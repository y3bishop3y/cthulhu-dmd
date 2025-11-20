# Turn Structure

## Overview

Each player's turn follows a structured sequence: actions, mythos card, and resolution phase.

---

## Turn Phases

### Phase 1: Take 3 Actions
Player can take **3 actions** in any combination:
- **Run** - Move 3 spaces
- **Attack** - Attack 1 enemy (roll dice)
- **Rest** - Heal 3 points (health/stress, requires safe space)
- **Trade** - Trade items with other investigators
- **Investigate** - Episode-specific actions

**Free Actions:** Some powers grant free actions that don't count toward the 3 actions.

### Phase 2: Draw Mythos Card
- Draw 1 Mythos card
- Resolve any immediate effects

### Phase 3: Investigate or Fight
- **If Safe:** Draw a Discovery card
- **If Not Safe:** Enemies attack you

### Phase 4: Resolve End of Turn
- Clean up any end-of-turn effects
- Pass turn to next player

---

## Action Economy

### Standard Actions
- Each action takes 1 of 3 available actions
- Actions can be repeated (e.g., Attack 3 times)
- Actions can be skipped

### Free Actions
- Powers can grant free actions
- Example: "Marksman Level 4" - 1 free attack per turn
- Free actions don't count toward 3 actions

### Action Efficiency
- **Rest = 1 action** (heals 3 points)
- **Attack = 1 action** (may cause damage/stress)
- **Run = 1 action** (moves 3 spaces)
- **Free actions** = more actions available

---

## Example Turn

### Turn 1: Offensive
1. **Action 1:** Attack (roll dice, deal damage)
2. **Action 2:** Attack (roll dice, deal damage)
3. **Action 3:** Run (move 3 spaces)
4. **Mythos:** Draw card
5. **Resolution:** Investigate (draw Discovery card)

### Turn 2: Defensive
1. **Action 1:** Rest (heal 3: 2 health + 1 stress)
2. **Action 2:** Run (move to safe space)
3. **Action 3:** Investigate (episode action)
4. **Mythos:** Draw card
5. **Resolution:** Safe → Draw Discovery card

### Turn 3: Mixed (with Free Action)
1. **Action 1:** Attack (roll dice)
2. **Free Action:** Attack (from Marksman Level 4)
3. **Action 2:** Rest (heal 3 points)
4. **Action 3:** Run (move 3 spaces)
5. **Mythos:** Draw card
6. **Resolution:** Not safe → Enemies attack

---

## Impact on Power Analysis

### Action Efficiency
- **Free actions** = more actions available
- Example: "Marksman Level 4" - 1 free attack = 4 attacks total (3 normal + 1 free)

### Action Synergy
- Powers that grant free actions work well together
- Example: Multiple free attack powers = many attacks per turn

### Action Economy
- **Rest = 1 action** - healing powers reduce need for Rest
- **Attack = 1 action** - free attacks = more damage output
- **Run = 1 action** - movement powers reduce need for Run

---

## Implementation

See `scripts/models/game_mechanics.py`:
- `TurnStructure` - Turn structure model
- `ActionType` - Action type enum
- `RestAction` - Rest action mechanics

---

**Last Updated:** 2024-12-19

