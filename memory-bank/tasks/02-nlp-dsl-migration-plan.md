# NLP → DSL Migration Plan

## Problem Statement

**Current State:**
- `BackCardData.parse_from_text()` has 900+ lines of regex-based parsing
- 50+ decision points with brittle pattern matching
- Hard to maintain, extend, or debug
- Doesn't scale to new power types or variations

**Goal:**
- Use NLP to understand semantic meaning of text
- Map natural language → DSL (Domain-Specific Language) → Game Rules
- Build extensible system that can handle variations
- Enable probability calculations and gameplay analysis

---

## Architecture Overview

```
┌─────────────────┐
│  OCR Text       │  (Cleaned, optimal strategy)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  NLP Preprocess  │  (spaCy: sentence segmentation, dependency parsing, entities)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pattern Match  │  (Match against DSL grammar patterns using NLP entities)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DSL Structure   │  (GameRule with Conditions, Effects, Scope)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Game Rule      │  (Pydantic model: actionable, queryable)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Probability    │  (Calculate dice probabilities, success rates, etc.)
│  Calculation    │
└─────────────────┘
```

---

## Phase 1: Foundation - NLP Preprocessing Pipeline

### Goal
Build robust NLP preprocessing that extracts semantic structure from power descriptions.

### Tasks

#### 1.1 Create NLP Preprocessor Module
**File:** `scripts/parsing/nlp_preprocessor.py`

**Responsibilities:**
- Load spaCy model (lazy loading)
- Clean OCR text (fix common errors)
- Sentence segmentation
- Dependency parsing
- Entity extraction (numbers, dice types, actions, conditions)
- Phrase chunking (identify clauses)

**Key Functions:**
```python
def preprocess_power_text(text: str) -> NLPAnalysis:
    """Preprocess power description text with NLP."""
    
def extract_entities(doc: spacy.Doc) -> PowerEntities:
    """Extract game-specific entities (dice, actions, conditions)."""
    
def identify_clauses(doc: spacy.Doc) -> List[Clause]:
    """Identify conditional clauses, effect clauses, scope clauses."""
```

**Output:**
- Structured NLP analysis with entities, dependencies, clauses
- Ready for pattern matching

---

#### 1.2 Create Game-Specific Entity Recognizer
**File:** `scripts/parsing/game_entity_recognizer.py`

**Responsibilities:**
- Recognize game terms (dice colors, actions, conditions)
- Handle OCR variations ("goin" → "gain", "santiy" → "sanity")
- Extract quantities (numbers, "any number")
- Identify action types (attack, move, investigate, etc.)
- Detect conditions (when, while, if)

**Key Functions:**
```python
def recognize_dice_mentions(doc: spacy.Doc) -> List[DiceMention]:
    """Find all dice mentions (green dice, black dice, etc.)."""
    
def recognize_actions(doc: spacy.Doc) -> List[ActionMention]:
    """Find action mentions (attack, move, investigate, etc.)."""
    
def recognize_conditions(doc: spacy.Doc) -> List[ConditionMention]:
    """Find conditional clauses (when, while, if)."""
```

---

### Deliverables
- ✅ NLP preprocessing module
- ✅ Game entity recognizer
- ✅ Unit tests with sample power descriptions
- ✅ Benchmark: Can extract entities from 80%+ of power descriptions

---

## Phase 2: DSL Grammar Implementation

### Goal
Implement the DSL grammar (from `01-dsl-grammar-design.md`) using TextX.

### Tasks

#### 2.1 Create DSL Grammar File
**File:** `scripts/parsing/dsl_grammar.tx` (TextX grammar file)

**Based on:** `tasks/01-dsl-grammar-design.md`

**Key Grammar Rules:**
- `GameRule` - Top-level rule
- `Condition` - When/while/if clauses
- `Effect` - Dice, reroll, healing, defensive, conversion, action
- `Scope` - Duration, target, limitations

---

#### 2.2 Create DSL Pydantic Models
**File:** `scripts/models/game_rule_dsl.py`

**Models:**
- `GameRule` - Complete rule representation
- `Condition` - Condition types
- `Effect` - All effect types (DiceEffect, RerollEffect, etc.)
- `Scope` - Scope information

**Integration:**
- Models should integrate with existing `game_mechanics.py`
- Should be queryable/executable

---

#### 2.3 Create DSL Parser
**File:** `scripts/parsing/dsl_parser.py`

**Responsibilities:**
- Load TextX grammar
- Parse DSL strings into Pydantic models
- Validate parsed structures

**Key Functions:**
```python
def parse_dsl(dsl_text: str) -> GameRule:
    """Parse DSL text into GameRule model."""
    
def validate_rule(rule: GameRule) -> bool:
    """Validate rule structure."""
```

---

### Deliverables
- ✅ TextX grammar file
- ✅ DSL Pydantic models
- ✅ DSL parser
- ✅ Unit tests parsing example rules
- ✅ Can parse 90%+ of well-formed DSL

---

## Phase 3: NLP → DSL Translation Layer

### Goal
Translate NLP analysis into DSL structures.

### Tasks

#### 3.1 Create Translation Engine
**File:** `scripts/parsing/dsl_translator.py`

**Responsibilities:**
- Take NLP analysis (entities, clauses, dependencies)
- Match against DSL patterns
- Generate DSL structures
- Handle ambiguities and variations

**Strategy:**
1. **Pattern Matching:** Match NLP entities to DSL patterns
2. **Clause Mapping:** Map conditional clauses → Condition DSL
3. **Effect Extraction:** Extract effects from effect clauses
4. **Scope Detection:** Identify scope from remaining clauses

**Key Functions:**
```python
def translate_to_dsl(nlp_analysis: NLPAnalysis) -> GameRule:
    """Translate NLP analysis to DSL GameRule."""
    
def match_effect_pattern(clause: Clause, entities: PowerEntities) -> Optional[Effect]:
    """Match a clause against effect patterns."""
    
def match_condition_pattern(clause: Clause) -> Optional[Condition]:
    """Match a clause against condition patterns."""
```

---

#### 3.2 Create Pattern Library
**File:** `scripts/parsing/dsl_patterns.py`

**Responsibilities:**
- Define pattern matching rules
- Handle variations and synonyms
- OCR error tolerance

**Pattern Examples:**
- Dice patterns: "gain X green dice", "add X black dice"
- Conditional patterns: "when you attack", "while sanity on red"
- Effect patterns: "heal X stress", "reroll X dice"

**Key Functions:**
```python
def match_dice_effect(clause: Clause, entities: PowerEntities) -> Optional[DiceEffect]:
    """Match clause against dice effect patterns."""
    
def match_healing_effect(clause: Clause, entities: PowerEntities) -> Optional[HealingEffect]:
    """Match clause against healing effect patterns."""
```

---

### Deliverables
- ✅ Translation engine
- ✅ Pattern library
- ✅ Unit tests translating NLP → DSL
- ✅ Can translate 70%+ of power descriptions correctly

---

## Phase 4: Integration & Migration

### Goal
Integrate NLP → DSL pipeline into character parsing, replacing regex.

### Tasks

#### 4.1 Create Hybrid Parser
**File:** `scripts/models/character_nlp.py` (new)

**Strategy:**
- Try NLP → DSL parsing first
- Fall back to regex if NLP fails
- Gradually migrate regex patterns to NLP patterns

**Key Functions:**
```python
def parse_power_with_nlp(text: str) -> Optional[Power]:
    """Parse power using NLP → DSL pipeline."""
    
def parse_power_hybrid(text: str) -> Power:
    """Try NLP first, fall back to regex."""
```

---

#### 4.2 Update BackCardData.parse_from_text()
**File:** `scripts/models/character.py`

**Migration Strategy:**
1. Add optional `use_nlp` parameter (default: False initially)
2. If `use_nlp=True`, use NLP → DSL pipeline
3. Keep regex as fallback
4. Gradually enable NLP for more cases

**Code Structure:**
```python
@classmethod
def parse_from_text(cls, text: str, use_nlp: bool = False) -> "BackCardData":
    if use_nlp:
        return cls._parse_with_nlp(text)
    else:
        return cls._parse_with_regex(text)  # Current implementation
```

---

#### 4.3 Create Migration Script
**File:** `scripts/parsing/migrate_to_nlp.py`

**Purpose:**
- Test NLP parsing on all existing characters
- Compare NLP vs regex results
- Identify cases where NLP needs improvement
- Generate migration report

---

### Deliverables
- ✅ Hybrid parser
- ✅ Updated BackCardData with NLP option
- ✅ Migration script
- ✅ Comparison report (NLP vs regex accuracy)

---

## Phase 5: DSL → Game Rules → Probabilities

### Goal
Execute DSL rules to calculate probabilities and gameplay impact.

### Tasks

#### 5.1 Create Rule Executor
**File:** `scripts/analysis/rule_executor.py`

**Responsibilities:**
- Take DSL GameRule
- Execute against game state
- Calculate probabilities
- Determine gameplay impact

**Key Functions:**
```python
def execute_rule(rule: GameRule, game_state: GameState) -> RuleResult:
    """Execute a game rule and calculate effects."""
    
def calculate_probability(rule: GameRule, dice_config: DiceConfig) -> ProbabilityResult:
    """Calculate probability of success given rule and dice."""
```

---

#### 5.2 Integrate with Existing Probability System
**File:** `scripts/models/game_mechanics.py` (extend)

**Integration:**
- Use existing dice probability models
- Add rule execution on top
- Calculate combined effects

---

### Deliverables
- ✅ Rule executor
- ✅ Probability calculations from DSL
- ✅ Integration with existing game mechanics

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Phase 1.1: NLP Preprocessor
- [ ] Phase 1.2: Game Entity Recognizer
- [ ] Unit tests

### Week 2: DSL Implementation
- [ ] Phase 2.1: TextX Grammar
- [ ] Phase 2.2: DSL Models
- [ ] Phase 2.3: DSL Parser
- [ ] Unit tests

### Week 3: Translation
- [ ] Phase 3.1: Translation Engine
- [ ] Phase 3.2: Pattern Library
- [ ] Unit tests with real power descriptions

### Week 4: Integration
- [ ] Phase 4.1: Hybrid Parser
- [ ] Phase 4.2: Update BackCardData
- [ ] Phase 4.3: Migration Script
- [ ] Test on all characters

### Week 5: Execution & Probabilities
- [ ] Phase 5.1: Rule Executor
- [ ] Phase 5.2: Integration
- [ ] End-to-end tests

---

## Success Metrics

### Phase 1 (NLP Preprocessing)
- ✅ Can extract entities from 80%+ of power descriptions
- ✅ Handles OCR errors gracefully
- ✅ Identifies clauses correctly

### Phase 2 (DSL Grammar)
- ✅ Can parse 90%+ of well-formed DSL
- ✅ Models are queryable/executable
- ✅ Integrates with existing game mechanics

### Phase 3 (Translation)
- ✅ Can translate 70%+ of power descriptions to DSL
- ✅ Handles variations and synonyms
- ✅ OCR error tolerance

### Phase 4 (Integration)
- ✅ NLP parsing works for 70%+ of characters
- ✅ Fallback to regex works seamlessly
- ✅ No regression in existing functionality

### Phase 5 (Execution)
- ✅ Can calculate probabilities from DSL rules
- ✅ Can determine gameplay impact
- ✅ Integrates with existing analysis tools

---

## Key Design Decisions

### 1. Hybrid Approach (Initially)
- Start with NLP + regex fallback
- Gradually migrate patterns to NLP
- Reduces risk during transition

### 2. Pattern-Based Translation
- Use NLP to extract entities/clauses
- Match against DSL patterns
- More maintainable than pure NLP parsing

### 3. Incremental Migration
- Don't replace regex all at once
- Enable NLP per-character or per-power-type
- Learn and improve iteratively

### 4. DSL as Intermediate Representation
- NLP → DSL → Game Rules
- DSL is human-readable and debuggable
- Can be manually corrected if needed

---

## Risks & Mitigations

### Risk 1: NLP Accuracy
**Mitigation:** 
- Hybrid approach with regex fallback
- Pattern matching (more reliable than pure NLP)
- Manual correction capability

### Risk 2: Performance
**Mitigation:**
- Lazy load spaCy model
- Cache NLP results
- Optimize pattern matching

### Risk 3: Migration Complexity
**Mitigation:**
- Incremental migration
- Keep regex as fallback
- Comprehensive testing

---

## Next Steps

1. **Review this plan** - Ensure it aligns with goals
2. **Start Phase 1** - Build NLP preprocessing foundation
3. **Test incrementally** - Validate each phase before moving on
4. **Iterate** - Improve based on real-world results

---

## References

- `tasks/00-power-analysis-system-plan.md` - Overall system plan
- `tasks/01-dsl-grammar-design.md` - DSL grammar design
- `scripts/models/game_mechanics.py` - Existing game mechanics models
- `scripts/parsing/nlp_parser.py` - Existing NLP parser (experimental)

---

**Status:** Planning Phase  
**Last Updated:** 2025-11-20

