# Health & Stress Mechanics

## Overview

Characters have two survival tracks: **Health** (wounds) and **Stress** (sanity). Managing both is critical for survival.

---

## Health Track (Wounds)

### Structure
- **5 health slots** (tracked on character board)
- **Starting health:** 5 (all slots empty)
- **Death threshold:** 6th hit = character eliminated from game

### Mechanics
- When character takes damage, mark health slots
- 6th hit = death (skull icon at end of track)
- Health can be healed back up to maximum (5)

### Example
- Character starts: 5 health
- Takes 3 damage: 2 health remaining
- Uses 1 Rest action (3 healing points): Heals 3 health → back to 5 health

### Implementation
```python
from scripts.models.game_mechanics import HealthTrack

track = HealthTrack()  # Starts at 5 health
track.take_damage(3)   # Now at 2 health
track.heal(3)          # Back to 5 health
track.is_dead          # False (not at 6th hit)
```

---

## Stress Track (Sanity)

### Structure
- **5 stress slots** (tracked on character board)
- **Starting stress:** 0 (all slots empty)
- **Maximum stress:** 5 (can't take more)

### Mechanics
- When character takes stress, mark stress slots
- At maximum stress (5), can't take more stress
- Some effects deal wounds instead if at max stress
- Stress can be healed back down to 0

### Example
- Character starts: 0 stress
- Takes 3 stress: 3 stress
- Uses 1 Rest action (3 healing points): Heals 3 stress → back to 0 stress

### Implementation
```python
from scripts.models.game_mechanics import StressTrack

track = StressTrack()  # Starts at 0 stress
track.take_stress(3)   # Now at 3 stress
track.heal_stress(3)   # Back to 0 stress
track.is_insane        # False (insanity threshold is 10)
```

**Note:** Stress track is separate from Insanity track (see [Insanity Track](./insanity-track.md)).

---

## Rest Action

### Mechanics
- Provides **3 healing points** per action
- Can distribute healing points between health and stress
- Requires safe space (usually)
- Takes 1 action (out of 3 per turn)

### Example Distributions
- **All to health:** 3 health healed, 0 stress healed
- **All to stress:** 0 health healed, 3 stress healed
- **Split:** 2 health + 1 stress, or 1 health + 2 stress

### Implementation
```python
from scripts.models.game_mechanics import RestAction, HealthTrack, StressTrack

rest = RestAction()
health = HealthTrack()
stress = StressTrack()

health.take_damage(3)  # 2 health remaining
stress.take_stress(2)  # 2 stress

# Heal 2 health + 1 stress
health_healed, stress_healed = rest.apply_healing(
    health, stress, health_amount=2, stress_amount=1
)
# health_healed = 2, stress_healed = 1
```

---

## Turn Structure

### Actions Per Turn
- Player gets **3 actions per turn**
- Actions can be: Run, Attack, Rest, Trade, Investigate (in any combination)
- After actions: Draw Mythos card, then Investigate or Fight

### Action Economy
- **Rest = 1 action** (heals 3 points)
- **Attack = 1 action** (may cause damage/stress)
- **Run = 1 action** (moves 3 spaces)
- **Free actions** from powers don't count toward 3 actions

### Example Turn
1. **Action 1:** Attack (roll dice, deal damage)
2. **Action 2:** Rest (heal 3 points: 2 health + 1 stress)
3. **Action 3:** Run (move 3 spaces)
4. **After actions:** Draw Mythos card, then Investigate or Fight

---

## Impact on Power Analysis

### Healing Powers
- **More valuable** - survival = staying in game
- Example: Powers that heal stress reduce need for Rest actions

### Defensive Powers
- **Reduce need for healing** - take less damage/stress
- Example: "Toughness" reduces damage taken

### Action Economy
- **Free actions** = more healing opportunities
- Example: "Marksman Level 4" - 1 free attack per turn

### Stress Management
- **Avoid insanity** - high stress can lead to insanity
- Example: Powers that reduce stress gain

---

## Implementation

See `scripts/models/game_mechanics.py`:
- `HealthTrack` - Health/wounds tracking
- `StressTrack` - Stress/sanity tracking
- `RestAction` - Rest action mechanics
- `TurnStructure` - Turn structure and actions

---

**Last Updated:** 2024-12-19

