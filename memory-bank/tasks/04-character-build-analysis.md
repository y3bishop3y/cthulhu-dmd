# Character Build Analysis

## Overview

This phase bridges individual power statistics with full character analysis. We need to:
1. Build complete character models with all powers combined
2. Calculate full character statistics (all powers active)
3. Determine power "value" metrics (beyond just dice stats)
4. Analyze character builds at different upgrade levels

---

## Goals

### Primary Goal
Create a system that can:
- Load a character with their powers (special + 2 common)
- Combine all powers into a complete build
- Calculate overall character effectiveness
- Compare different power combinations
- Analyze upgrade paths for characters

### Key Metrics to Calculate

1. **Combat Effectiveness**
   - Expected successes per roll
   - Tentacle risk (insanity risk)
   - Maximum damage output
   - Action economy (free actions)

2. **Survival Value**
   - Healing capabilities
   - Defensive reductions
   - Stress management
   - Health management

3. **Utility Value**
   - Reroll capabilities
   - Conditional effects
   - Movement/positioning
   - Investigation capabilities

4. **Synergy Value**
   - How well powers work together
   - Amplifying combinations
   - Complementary effects

---

## Implementation Plan

### Step 1: Character Build Model ✅
**Status:** ✅ COMPLETE

**What we need:**
- `CharacterBuild` model that combines:
  - Character base stats (health, stress, insanity track)
  - Special power (at specific level)
  - Common powers (at specific levels)
  - Red swirl bonuses (green dice from insanity track)

**Model Structure:**
```python
class CharacterBuild(BaseModel):
    character_name: str
    special_power_level: int  # 1-4 (or 1 for special)
    common_power_1: str  # Power name
    common_power_1_level: int  # 1-4
    common_power_2: str  # Power name
    common_power_2_level: int  # 1-4
    insanity_track: InsanityTrack
    health_track: HealthTrack
    stress_track: StressTrack
    
    # Computed properties
    @property
    def all_powers(self) -> List[PowerEffect]
    @property
    def power_combination(self) -> PowerCombination
    @property
    def total_statistics(self) -> CharacterStatistics
```

### Step 2: Character Statistics Calculator ✅
**Status:** ✅ COMPLETE

**What we need:**
- Calculate combined statistics for all active powers
- Include insanity track bonuses (green dice from red swirls)
- Calculate overall effectiveness metrics

**Key Calculations:**
- Total dice (base + powers + red swirl bonuses)
- Expected successes (with elder sign conversions)
- Tentacle risk (adjusted for green dice)
- Healing capabilities
- Action economy
- Defensive capabilities

### Step 3: Power Value Calculation
**Status:** Ready to implement

**What we need:**
- Assign "value" scores to powers based on:
  - Success improvement
  - Tentacle risk reduction
  - Healing/defensive value
  - Action economy value
  - Synergy potential

**Value Metrics:**
```python
class PowerValue(BaseModel):
    power_name: str
    level: int
    success_value: float  # Expected success improvement
    risk_reduction_value: float  # Tentacle risk reduction
    healing_value: float  # Healing capabilities
    action_value: float  # Free actions
    synergy_value: float  # Works well with other powers
    total_value: float  # Weighted sum
```

### Step 4: Character Build Comparison
**Status:** Ready to implement

**What we need:**
- Compare different power combinations
- Compare different upgrade levels
- Identify optimal builds for different goals

**Comparison Metrics:**
- Offensive builds (maximize damage)
- Defensive builds (maximize survival)
- Balanced builds (good all-around)
- Synergy builds (powers that amplify each other)

---

## Workflow

### Current Workflow
1. Parse power descriptions → Extract effects
2. Calculate individual power statistics
3. Store in `common_powers.json`

### New Workflow
1. **Load Character** → Get character data with power names
2. **Load Powers** → Get power data from `common_powers.json`
3. **Create Build** → Combine character + powers at specific levels
4. **Calculate Statistics** → Full character effectiveness
5. **Calculate Values** → Power value metrics
6. **Compare Builds** → Different power combinations/levels

---

## Example Use Cases

### Use Case 1: Character Analysis
**Input:** Character name (e.g., "Amelie")
**Output:**
- Character's available powers
- Recommended power combinations
- Optimal upgrade paths
- Build effectiveness at different stages

### Use Case 2: Power Comparison
**Input:** Two power combinations
**Output:**
- Side-by-side statistics comparison
- Value analysis
- Synergy detection
- Recommendation

### Use Case 3: Upgrade Optimization
**Input:** Character with current build
**Output:**
- Best next upgrade (considering only 6 total)
- Upgrade path for different goals
- Value per upgrade point

---

## Implementation Order

### Phase 1.5.1: Character Build Model ✅
**Priority:** High
**Status:** ✅ COMPLETE
**Tasks:**
- [x] Create `CharacterBuild` model
- [x] Load character data
- [x] Load power data
- [x] Combine into build
- [x] Unit tests

**Files Created:**
- `scripts/models/character_build.py`
- `scripts/tests/unit/test_character_build.py`
- `scripts/analysis/character_analyzer.py`

### Phase 1.5.2: Character Statistics ✅
**Priority:** High
**Status:** ✅ COMPLETE
**Tasks:**
- [x] Create `CharacterStatistics` model
- [x] Calculate combined dice stats
- [x] Include insanity track bonuses
- [x] Calculate effectiveness metrics
- [x] Unit tests

**Files Created:**
- `CharacterStatistics` model (in `character_build.py`)

### Phase 1.5.3: Power Value Calculation ⏳
**Priority:** Medium
**Tasks:**
- [ ] Create `PowerValue` model
- [ ] Define value metrics
- [ ] Calculate values for all powers
- [ ] Weight different value types
- [ ] Unit tests

### Phase 1.5.4: Build Comparison ⏳
**Priority:** Medium
**Tasks:**
- [ ] Create comparison functions
- [ ] Generate recommendations
- [ ] Visualize differences
- [ ] Unit tests

---

## Files to Create

```
scripts/models/
  character_build.py          # CharacterBuild model
  character_statistics.py     # CharacterStatistics model
  power_value.py              # PowerValue model

scripts/analysis/
  character_analyzer.py       # Character build analysis
  build_comparator.py         # Compare different builds
  value_calculator.py         # Calculate power values
```

---

## Dependencies

### Required
- ✅ Power statistics calculation (`analyze_power_statistics.py`)
- ✅ Power combination system (`power_combination.py`)
- ✅ Character models (`character.py`)
- ✅ Game mechanics (`game_mechanics.py`)

### Optional (for future)
- NLP parsing (Part 1 - DSL)
- Upgrade optimization (Phase 2)
- Synergy detection (Phase 3)

---

## Success Criteria

- ✅ Can load any character and create a build
- ✅ Can calculate full character statistics
- ✅ Can compare different power combinations
- ✅ Can identify optimal builds
- ✅ Can calculate power values
- ✅ Can recommend upgrade paths

---

**Status:** Planning Phase  
**Last Updated:** 2024-12-19

