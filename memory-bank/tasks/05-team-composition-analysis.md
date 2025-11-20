# Team Composition & Synergy Analysis

## Overview

This phase enables analyzing character teams for different player counts (1-5 players) and identifying optimal pairings based on synergy, role coverage, and effectiveness.

---

## Goals

### Primary Goal
Create a system that can:
- Analyze character builds and suggest play strategies
- Identify optimal character pairings for different team sizes
- Filter by season (e.g., "season 1 only" or "season 1 + season 3")
- Recommend team compositions for 1-5 player games
- Analyze team synergy and role coverage

### Key Features

1. **Character Pool Management**
   - Load characters from specific seasons
   - Filter by availability
   - Support multiple season combinations

2. **Play Strategy Suggestions**
   - Analyze character build strengths
   - Suggest optimal power upgrade paths
   - Recommend playstyle (offensive, defensive, balanced, utility)

3. **Team Composition Analysis**
   - Analyze teams of 1-5 characters
   - Identify role coverage (tank, damage, support, utility)
   - Detect synergies and conflicts
   - Calculate team effectiveness

4. **Pairing Recommendations**
   - For a given character, find best partners
   - Consider team size (1-5 players)
   - Consider season availability
   - Rank by synergy score

---

## Implementation Plan

### Step 1: Character Pool Manager ⏳
**Status:** Ready to implement

**What we need:**
- Load all characters from specified seasons
- Filter by season combinations
- Create character pool with builds

**Model:**
```python
class CharacterPool(BaseModel):
    season_filters: List[Season]
    characters: List[CharacterBuild]
    
    @classmethod
    def from_seasons(cls, seasons: List[Season]) -> "CharacterPool"
    def filter_by_season(cls, season: Season) -> "CharacterPool"
```

### Step 2: Play Strategy Analyzer ✅
**Status:** ✅ COMPLETE

**What we need:**
- Analyze character build strengths/weaknesses
- Suggest playstyle (offensive, defensive, balanced, utility)
- Recommend power upgrade priorities
- Suggest optimal upgrade paths

**Model:**
```python
class PlayStrategy(BaseModel):
    character_name: str
    playstyle: Playstyle  # OFFENSIVE, DEFENSIVE, BALANCED, UTILITY
    strengths: List[str]
    weaknesses: List[str]
    recommended_upgrades: List[UpgradeRecommendation]
    upgrade_path: UpgradePath
```

### Step 3: Team Composition Model ⏳
**Status:** Ready to implement

**What we need:**
- Represent team of 1-5 characters
- Calculate team statistics
- Analyze role coverage
- Detect synergies and conflicts

**Model:**
```python
class TeamComposition(BaseModel):
    characters: List[CharacterBuild]  # 1-5 characters
    team_size: int  # 1-5
    
    @property
    def team_statistics(self) -> TeamStatistics
    @property
    def role_coverage(self) -> RoleCoverage
    @property
    def synergies(self) -> List[Synergy]
    @property
    def conflicts(self) -> List[Conflict]
```

### Step 4: Synergy Analyzer ⏳
**Status:** Ready to implement

**What we need:**
- Detect complementary powers
- Identify amplifying combinations
- Calculate synergy scores
- Rank character pairings

**Model:**
```python
class Synergy(BaseModel):
    character_1: str
    character_2: str
    synergy_type: SynergyType  # COMPLEMENTARY, AMPLIFYING, DEFENSIVE, etc.
    description: str
    score: float  # 0.0 - 1.0
    examples: List[str]  # Specific power combinations
```

### Step 5: Pairing Recommender ⏳
**Status:** Ready to implement

**What we need:**
- For a given character, find best partners
- Consider team size
- Consider season availability
- Rank by synergy score

**Function:**
```python
def recommend_pairings(
    character: CharacterBuild,
    pool: CharacterPool,
    team_size: int,  # 1-5
    exclude_characters: Optional[List[str]] = None
) -> List[PairingRecommendation]
```

---

## Use Cases

### Use Case 1: Character Play Strategy
**Input:** Character name (e.g., "Amelie")
**Output:**
- Character strengths/weaknesses
- Recommended playstyle
- Optimal upgrade path
- Power combination suggestions

### Use Case 2: Best Partner for Character
**Input:** Character name, team size (e.g., "Amelie", 2 players)
**Output:**
- Top 5 partner recommendations
- Synergy explanations
- Team effectiveness scores

### Use Case 3: Optimal Team Composition
**Input:** Team size (e.g., 3 players), seasons (e.g., ["season1", "season3"])
**Output:**
- Top 5 team compositions
- Role coverage analysis
- Synergy scores
- Effectiveness rankings

### Use Case 4: Team Analysis
**Input:** List of character names
**Output:**
- Team statistics
- Role coverage
- Synergies detected
- Conflicts detected
- Recommendations

---

## Implementation Order

### Phase 1.5.2: Character Pool & Play Strategy ✅
**Priority:** High
**Status:** ✅ COMPLETE
**Tasks:**
- [x] Create `CharacterPool` model
- [x] Create `PlayStrategy` model
- [x] Implement play strategy analyzer
- [x] Load characters from seasons
- [x] Unit tests

**Files Created:**
- `scripts/models/character_pool.py`
- `scripts/models/play_strategy.py`
- `scripts/tests/unit/test_character_pool.py`
- `scripts/tests/unit/test_play_strategy.py`

### Phase 1.5.3: Team Composition ⏳
**Priority:** High
**Tasks:**
- [ ] Create `TeamComposition` model
- [ ] Create `TeamStatistics` model
- [ ] Create `RoleCoverage` model
- [ ] Calculate team statistics
- [ ] Unit tests

### Phase 1.5.4: Synergy Detection ⏳
**Priority:** High
**Tasks:**
- [ ] Create `Synergy` model
- [ ] Create `Conflict` model
- [ ] Implement synergy detection algorithms
- [ ] Calculate synergy scores
- [ ] Unit tests

### Phase 1.5.5: Pairing Recommender ⏳
**Priority:** High
**Tasks:**
- [ ] Create `PairingRecommendation` model
- [ ] Implement pairing algorithm
- [ ] Support team size filtering
- [ ] Support season filtering
- [ ] Unit tests

---

## Files to Create

```
scripts/models/
  character_pool.py          # CharacterPool model
  play_strategy.py           # PlayStrategy model
  team_composition.py        # TeamComposition, TeamStatistics, RoleCoverage
  synergy.py                 # Synergy, Conflict models

scripts/analysis/
  play_strategy_analyzer.py  # Analyze character play strategies
  team_analyzer.py           # Analyze team compositions
  synergy_analyzer.py        # Detect synergies
  pairing_recommender.py     # Recommend character pairings
```

---

## Synergy Types

### Complementary Synergy
Powers that fill gaps in each other's capabilities:
- Offensive + Defensive
- Damage + Healing
- Range + Melee

### Amplifying Synergy
Powers that enhance each other:
- Elder sign conversion + Green dice
- Rerolls + Tentacle avoidance
- Free actions + Attack powers

### Defensive Synergy
Powers that stack defensive capabilities:
- Multiple healing powers
- Damage reduction stacking
- Stress management

### Utility Synergy
Powers that provide complementary utility:
- Movement + Investigation
- Trading + Resource management
- Information gathering

---

## Role Coverage

### Roles to Track
- **Tank** - High health, defensive powers, damage reduction
- **Damage Dealer** - High success rate, attack powers, dice additions
- **Support** - Healing, stress management, utility
- **Utility** - Movement, investigation, resource management
- **Hybrid** - Multiple roles

### Coverage Analysis
- Identify which roles are covered
- Identify gaps in coverage
- Recommend additions to fill gaps

---

## Success Criteria

- ✅ Can load characters from specific seasons
- ✅ Can analyze character play strategies
- ✅ Can detect synergies between characters
- ✅ Can recommend best partners for a character
- ✅ Can analyze team compositions
- ✅ Can filter by season and team size
- ✅ Can rank teams by effectiveness

---

**Status:** Planning Phase  
**Last Updated:** 2024-12-19

