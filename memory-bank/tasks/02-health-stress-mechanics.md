# Health & Stress Mechanics

## Overview

This document details the health and stress (sanity) mechanics for Cthulhu: Death May Die characters.

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

### Insanity Thresholds
- Some stress slots have red sanity markers
- Reaching these thresholds grants bonus dice
- 4 thresholds = 4 bonus dice (one per threshold reached)

---

## Rest Action

### Mechanics
- **Cost:** 1 action (out of 3 per turn)
- **Healing:** Provides 3 healing points
- **Distribution:** Can allocate between health and stress
- **Requirement:** Usually requires safe space

### Examples

**Example 1: Full Health Recovery**
- Character: 5 health, takes 3 damage → 2 health remaining
- Uses Rest action: Allocates all 3 points to health
- Result: 2 + 3 = 5 health (fully healed)

**Example 2: Mixed Healing**
- Character: 3 health, 2 stress
- Uses Rest action: Allocates 2 points to health, 1 point to stress
- Result: 5 health, 1 stress

**Example 3: Stress Management**
- Character: 5 health, 4 stress (near max)
- Uses Rest action: Allocates all 3 points to stress
- Result: 5 health, 1 stress (stress managed)

---

## Turn Structure

### Actions Per Turn
- **3 actions** per turn (can be any combination)
- Available actions:
  - **Run** - Move 3 spaces
  - **Attack** - Attack 1 enemy
  - **Rest** - Heal 3 points (health/stress)
  - **Trade** - Trade with other investigators
  - **Investigate** - Investigate current space
  - **Episode actions** - Special scenario actions

### Turn Sequence
1. **TAKE 3 ACTIONS** (any combination)
2. **DRAW MYTHOS CARD**
3. **INVESTIGATE OR FIGHT!**
   - If Safe space: Draw Discovery card
   - Otherwise: Enemies attack you
4. **RESOLVE END OF TURN**

---

## Impact on Power Analysis

### Healing Powers
- **Value:** Very high (survival = staying in game)
- **Efficiency:** Compare healing per action vs Rest action (3 points)
- **Example:** Power that heals 1 stress per elder sign = free stress management

### Defensive Powers
- **Value:** High (reduces need for healing actions)
- **Efficiency:** Wound/sanity reduction = fewer Rest actions needed
- **Example:** Reduce wounds by 1 = saves healing actions over time

### Action Economy
- **Free actions** = more opportunities to Rest
- **Action addition powers** = can Rest more often
- **Example:** Free attack per turn = can use 1 action for Rest instead

### Stress Management
- **Stress healing powers** = avoid max stress penalties
- **Stress reduction** = stay below insanity thresholds longer
- **Example:** Heal 1 stress per elder sign = maintain sanity while rolling

---

## Power Combination Examples

### Example 1: Healing Synergy
**Powers:**
- Arcane Mastery Level 3: "Heal 1 stress for each elder sign you count as a success"
- Rest Action: 3 healing points

**Combined Effect:**
- Roll dice, count elder signs as successes
- Each elder sign = 1 stress healed (free)
- Can use Rest action for health only (stress handled by power)

### Example 2: Defensive Synergy
**Powers:**
- Toughness Level 3: "Reduce wounds taken by 1 when attacked"
- Rest Action: 3 healing points

**Combined Effect:**
- Take less damage from attacks
- Need fewer Rest actions to recover
- More actions available for other purposes

### Example 3: Action Economy
**Powers:**
- Marksman Level 4: "1 free attack per turn"
- Rest Action: 3 healing points

**Combined Effect:**
- Free attack = 1 action freed up
- Can use that action for Rest instead
- More healing capacity per turn

---

## Optimization Considerations

### When to Prioritize Healing Powers
- Character has low health/stress capacity
- Scenario has high damage output
- Team lacks dedicated healer

### When to Prioritize Defensive Powers
- Character takes frequent damage
- Want to reduce Rest actions needed
- Team has good healing support

### When to Prioritize Action Economy
- Want flexibility in turn planning
- Need to balance offense and healing
- Free actions compound with other powers

---

## Models & Implementation

### HealthTrack Model
```python
class HealthTrack(BaseModel):
    max_health: int = 5
    current_health: int = 5
    death_threshold: int = 6
    
    def take_damage(self, amount: int) -> int
    def heal(self, amount: int) -> int
```

### StressTrack Model
```python
class StressTrack(BaseModel):
    max_stress: int = 5
    current_stress: int = 0
    
    def take_stress(self, amount: int) -> int
    def heal_stress(self, amount: int) -> int
```

### RestAction Model
```python
class RestAction(BaseModel):
    healing_points: int = 3
    requires_safe_space: bool = True
    
    def apply_healing(
        self, health_track: HealthTrack, 
        stress_track: StressTrack,
        health_amount: int, stress_amount: int
    ) -> tuple[int, int]
```

---

**Status:** Documented  
**Last Updated:** 2024-12-19

