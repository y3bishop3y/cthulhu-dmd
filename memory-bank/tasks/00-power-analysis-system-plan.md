# Power Analysis System - Master Plan

## Overview

This document tracks the plan for building a comprehensive power analysis system that can:
1. Parse natural language power descriptions into structured game logic (DSL)
2. Combine multiple powers and calculate their combined effects
3. Optimize power upgrade paths (which power/level to upgrade next)
4. Analyze character team synergy (how characters complement each other)

---

## Part 1: Natural Language to Game Rules DSL

### Goal
Translate English power descriptions into structured, programmatic representations similar to chess notation.

**Example:**
- **Input:** "When you attack, you may target figures in your space. Gain 1 green dice while attacking a target in your space."
- **Output:** Structured representation with conditions, actions, effects, and scope

### Current State
- ✅ Regex pattern matching (fragile, many patterns)
- ✅ Keyword-based extraction (limited coverage)
- ✅ Manual extraction functions (conditional, reroll, healing, defensive)

### Target State
- ✅ Structured DSL representation
- ✅ NLP preprocessing for robust parsing
- ✅ Pattern matching with NLP-extracted entities
- ✅ Queryable/executable game rules

---

## Part 0: Core Game Mechanics (Foundation)

### Character Health & Stress System ✅
**Status:** Implemented

**Key Mechanics:**
- **Health Track:** 5 health slots (wounds)
  - 6th hit = death (character eliminated)
  - Starts at 5 health
- **Stress Track:** 5 stress slots (sanity)
  - Starts at 0 stress
  - Maximum stress = 5 (can't take more, some effects deal wounds instead)
- **Rest Action:** Provides 3 healing points per action
  - Can distribute between health and stress
  - Example: 5 health, takes 3 damage → can heal back to 5 health with 1 Rest action
  - Requires safe space (usually)

**Turn Structure:**
- Player gets **3 actions per turn**
- Actions can be: Run, Attack, Rest, Trade, Investigate (in any combination)
- After actions: Draw Mythos card, then Investigate or Fight

**Models Added:**
- `HealthTrack` - Tracks health/wounds (5 slots, death at 6)
- `StressTrack` - Tracks stress/sanity (5 slots, max 5)
- `RestAction` - Rest action with 3 healing points
- `TurnStructure` - Turn structure and available actions

**Impact on Power Analysis:**
- Healing powers become more valuable (survival = staying in game)
- Defensive powers reduce need for healing actions
- Stress management powers help avoid insanity
- Action economy matters (free actions = more healing opportunities)

---

## Part 0.5: Insanity Track System ✅
**Status:** Implemented

**Key Mechanics:**
- **Insanity Track:** 20 slots (player starts at slot 1, dies at slot 21)
- **Tentacles = Insanity:** Each tentacle rolled = +1 insanity
- **Red Swirls (Level-Ups):** Slots 5, 9, 13, 16, 19, 20 (6 total)
  - **Only 6 level-ups total** - cannot max all powers
  - Must choose upgrades strategically
- **Green Dice Bonuses:** Red swirls 2, 4, 5, 6 grant permanent green dice
  - Slots 9, 16, 19, 20 grant +1 green dice each
  - Maximum +4 green dice from red swirls
- **Death from Madness:** Slot 21 = death (one tentacle after slot 20)

**Models Added:**
- `InsanityTrack` - Tracks insanity progression (1-21, 21 = death)
- Red swirl tracking (level-up opportunities)
- Green dice bonus calculation
- Tentacle risk calculations

**Impact on Power Analysis:**
- **Tentacle risk = death risk** (especially at high insanity)
- **Green dice value increases** (no tentacles = safer)
- **Reroll value increases** (can avoid tentacles or get successes)
- **Limited upgrades** (only 6 total) - optimization critical
- **Early vs Late upgrades** - early upgrades benefit longer
- **Survival powers** become critical at high insanity

---

## Part 2: Power Combination System

### Goal
Calculate combined effects when multiple powers are active simultaneously.

### Key Features
- Combine additive effects (dice, rerolls, healing)
- Detect conflicts (exclusive effects like "instead")
- Identify synergies (powers that enhance each other)
- Calculate combined statistics

### Models Needed
- `PowerCombination` - Represents multiple active powers
- `PowerCombinationCalculator` - Calculates combined effects
- `Synergy` / `Conflict` - Interaction types

---

## Part 3: Upgrade Optimization System

### Goal
Determine optimal power upgrade paths for maximum effectiveness.

### Key Features
- Evaluate marginal improvement per upgrade
- Optimize for different goals (maximize successes, minimize risk, balance)
- Consider synergies when planning upgrades
- Generate upgrade recommendations

### Models Needed
- `UpgradePath` - Sequence of upgrades
- `Upgrade` - Single upgrade step
- `UpgradeOptimizer` - Optimization engine
- `OptimizationGoal` - Target metrics

---

## Part 4: Character Synergy Analysis

### Goal
Analyze how well characters work together in a team.

### Key Features
- Detect complementary powers
- Identify amplifying combinations
- Analyze action economy
- Find gaps in team coverage
- Recommend team additions

### Models Needed
- `TeamComposition` - Team of characters
- `TeamSynergy` - Synergy between characters
- `TeamSynergyAnalyzer` - Analysis engine
- `CoverageAnalysis` - Role coverage

---

## Implementation Phases

### Phase 1: Power Combination (Foundation) ⏳
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Create `PowerCombination` Pydantic model
- [ ] Implement `PowerCombinationCalculator`
- [ ] Handle additive effects (dice, rerolls, healing)
- [ ] Detect basic conflicts ("instead" clauses)
- [ ] Calculate combined statistics
- [ ] Unit tests for combination logic

**Deliverables:**
- `scripts/models/power_combination.py`
- `scripts/analysis/power_combiner.py`
- `scripts/tests/unit/test_power_combination.py`

---

### Phase 2: Upgrade Optimization ⏳
**Status:** Not Started  
**Priority:** High

**Tasks:**
- [ ] Create `UpgradePath` and `Upgrade` models
- [ ] Implement `UpgradeOptimizer` with greedy strategy
- [ ] Add optimization goals (maximize successes, minimize risk, etc.)
- [ ] Calculate efficiency metrics (improvement per cost)
- [ ] Generate upgrade recommendations
- [ ] Unit tests for optimization logic

**Deliverables:**
- `scripts/models/upgrade_optimization.py`
- `scripts/analysis/upgrade_optimizer.py`
- `scripts/tests/unit/test_upgrade_optimization.py`

---

### Phase 3: Synergy Detection ⏳
**Status:** Not Started  
**Priority:** Medium

**Tasks:**
- [ ] Create `TeamComposition` and `TeamSynergy` models
- [ ] Implement `TeamSynergyAnalyzer`
- [ ] Detect complementary powers
- [ ] Identify amplifying combinations
- [ ] Analyze action economy
- [ ] Unit tests for synergy detection

**Deliverables:**
- `scripts/models/team_synergy.py`
- `scripts/analysis/synergy_analyzer.py`
- `scripts/tests/unit/test_team_synergy.py`

---

### Phase 4: DSL Grammar & NLP Parsing ⏳
**Status:** Not Started  
**Priority:** Medium

**Tasks:**
- [ ] Research and select DSL library (TextX/Lark/pyparsing)
- [ ] Define game rule grammar
- [ ] Implement NLP preprocessing (spaCy)
- [ ] Create pattern matching with NLP entities
- [ ] Build translation layer (NLP → DSL)
- [ ] Unit tests for parsing

**Deliverables:**
- `scripts/models/game_rule_dsl.py`
- `scripts/parsing/nlp_preprocessor.py`
- `scripts/parsing/dsl_translator.py`
- `scripts/tests/unit/test_dsl_parsing.py`

---

### Phase 5: Advanced Features ⏳
**Status:** Not Started  
**Priority:** Low

**Tasks:**
- [ ] Lookahead optimization (multi-step planning)
- [ ] Scenario-specific optimization (boss fights, investigation, etc.)
- [ ] Character recommendation engine
- [ ] Power interaction database
- [ ] Visualization tools (upgrade trees, synergy graphs)
- [ ] Query interface for power analysis

**Deliverables:**
- `scripts/analysis/advanced_optimizer.py`
- `scripts/queries/power_queries.py`
- `scripts/visualization/` (if needed)

---

## Libraries & Frameworks Research

### DSL Parsing Libraries

#### 1. TextX ⭐ Recommended
**Pros:**
- Python-native, easy to learn
- Clean grammar syntax
- Generates Python objects directly
- Good documentation
- Active development

**Cons:**
- Less flexible than Lark for complex grammars
- Smaller community than pyparsing

**Use Case:** Best for defining game rule grammar with clean syntax

**Installation:**
```bash
uv add textx
```

**Example:**
```python
from textx import metamodel_from_str

grammar = """
GameRule: conditions*=Condition effects*=Effect;
Condition: 'when' action=ID | 'while' predicate=STRING;
Effect: 'gain' quantity=INT type=ID;
"""

mm = metamodel_from_str(grammar)
rule = mm.model_from_str("when attack gain 1 green_dice")
```

---

#### 2. Lark ⭐ Alternative
**Pros:**
- Very flexible (LALR, Earley, CYK parsers)
- Handles ambiguous grammars
- Good performance
- Can generate parse trees

**Cons:**
- Steeper learning curve
- More verbose grammar definitions
- Overkill for simple DSLs

**Use Case:** If we need complex parsing or ambiguous grammar handling

**Installation:**
```bash
uv add lark
```

**Example:**
```python
from lark import Lark

grammar = """
start: game_rule
game_rule: condition* effect*
condition: "when" action | "while" predicate
effect: "gain" INT type
%import common.WS
%ignore WS
"""

parser = Lark(grammar, start='start')
tree = parser.parse("when attack gain 1 green_dice")
```

---

#### 3. pyparsing
**Pros:**
- Mature library (20+ years)
- Very flexible
- Good for complex text parsing
- Extensive examples

**Cons:**
- More verbose syntax
- Steeper learning curve
- Less Pythonic than TextX

**Use Case:** If we need very complex parsing patterns

**Installation:**
```bash
uv add pyparsing
```

---

### NLP Libraries

#### 1. spaCy ⭐ Recommended
**Pros:**
- Fast, production-ready
- Excellent dependency parsing
- Custom entity recognition
- Good documentation
- Pre-trained models available

**Cons:**
- Requires model download
- Larger dependency size

**Use Case:** Primary NLP preprocessing (sentence segmentation, dependency parsing, entity extraction)

**Installation:**
```bash
uv add spacy
# Download model: python -m spacy download en_core_web_sm
```

**Example:**
```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("When you attack, gain 1 green dice")

# Extract entities, dependencies, etc.
for token in doc:
    print(token.text, token.dep_, token.head.text)
```

---

#### 2. NLTK
**Pros:**
- Comprehensive NLP toolkit
- Good for research/experimentation
- Many algorithms available

**Cons:**
- Slower than spaCy
- More complex setup
- Less production-focused

**Use Case:** If we need specific algorithms not in spaCy

**Installation:**
```bash
uv add nltk
```

---

#### 3. AllenNLP
**Pros:**
- State-of-the-art semantic parsing
- Good for complex NLP tasks

**Cons:**
- Overkill for our use case
- Requires ML models
- More complex setup

**Use Case:** Only if we need advanced semantic parsing

---

### Optimization Libraries

#### 1. scipy.optimize
**Pros:**
- Standard library for optimization
- Multiple algorithms (simplex, genetic, etc.)
- Well-tested

**Use Case:** For upgrade path optimization

**Installation:**
```bash
uv add scipy
```

---

#### 2. NetworkX
**Pros:**
- Graph analysis
- Good for synergy network analysis
- Path finding algorithms

**Use Case:** Analyzing power synergy networks

**Installation:**
```bash
uv add networkx
```

---

### Data Analysis Libraries

#### 1. pandas
**Pros:**
- Standard for data analysis
- Good for comparing upgrade paths
- Easy visualization

**Use Case:** Analyzing and comparing power combinations

**Installation:**
```bash
uv add pandas
```

---

## Recommended Tech Stack

### Primary Stack
1. **TextX** - DSL grammar definition
2. **spaCy** - NLP preprocessing
3. **Pydantic** - Data models (already in use)
4. **scipy.optimize** - Optimization algorithms
5. **NetworkX** - Synergy graph analysis

### Optional Additions
- **pandas** - Data analysis and comparison
- **matplotlib/plotly** - Visualization (if needed)

---

## File Structure

```
scripts/
  models/
    power_combination.py      # PowerCombination models
    upgrade_optimization.py   # UpgradePath, Upgrade models
    team_synergy.py           # TeamComposition, TeamSynergy models
    game_rule_dsl.py          # DSL models for game rules
  analysis/
    power_combiner.py         # PowerCombinationCalculator
    upgrade_optimizer.py      # UpgradeOptimizer
    synergy_analyzer.py       # TeamSynergyAnalyzer
    game_mechanics_engine.py  # Core calculation engine
  parsing/
    nlp_preprocessor.py       # spaCy preprocessing
    dsl_translator.py         # NLP → DSL translation
    grammar.py                 # TextX grammar definition
  queries/
    power_queries.py          # Query interface
  tests/
    unit/
      test_power_combination.py
      test_upgrade_optimization.py
      test_team_synergy.py
      test_dsl_parsing.py
```

---

## Success Metrics

### Phase 1 (Power Combination)
- ✅ Can combine 2+ powers and calculate accurate combined stats
- ✅ Detects conflicts correctly
- ✅ Identifies basic synergies

### Phase 2 (Upgrade Optimization)
- ✅ Recommends optimal next upgrade
- ✅ Considers multiple optimization goals
- ✅ Generates efficient upgrade paths

### Phase 3 (Synergy Detection)
- ✅ Identifies complementary characters
- ✅ Detects amplifying combinations
- ✅ Recommends team additions

### Phase 4 (DSL Parsing)
- ✅ Parses 80%+ of power descriptions correctly
- ✅ Handles natural language variations
- ✅ Generates structured representations

---

## Next Steps

1. **Review this plan** - Ensure all requirements are captured
2. **Start Phase 1** - Implement power combination foundation
3. **Research DSL libraries** - Test TextX vs Lark with sample grammar
4. **Set up NLP pipeline** - Test spaCy with sample power descriptions
5. **Iterate** - Build incrementally, test with real data

---

## Notes

- All models should use Pydantic for validation
- Follow existing code patterns (encapsulated logic in models)
- Write comprehensive unit tests
- Document with docstrings
- Use type hints throughout

---

## References

- [TextX Documentation](https://textx.github.io/textX/)
- [Lark Documentation](https://lark-parser.readthedocs.io/)
- [spaCy Documentation](https://spacy.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Last Updated:** 2024-12-19  
**Status:** Planning Phase

