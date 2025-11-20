# DSL Grammar Design for Game Rules

## Overview

Design a Domain-Specific Language (DSL) grammar that can represent Cthulhu: Death May Die game rules in a structured, programmatic format.

---

## Grammar Structure

### Core Concepts

1. **Conditions** - When/while/if clauses
2. **Actions** - Game actions (attack, investigate, move, etc.)
3. **Effects** - What happens (dice addition, reroll, healing, etc.)
4. **Scope** - Duration, target, limitations

---

## TextX Grammar Definition

```python
# Game Rule Grammar
grammar = """
GameRule: conditions*=Condition effects*=Effect scope=Scope?;

// Conditions
Condition: 
    WhenCondition | WhileCondition | IfCondition
;

WhenCondition: 'when' action=Action;
WhileCondition: 'while' predicate=Predicate;
IfCondition: 'if' condition=STRING;

// Actions
Action: 
    AttackAction | InvestigateAction | MoveAction | DefendAction | GenericAction
;

AttackAction: 'attack' target=Target?;
InvestigateAction: 'investigate';
MoveAction: 'move' | 'run' | 'sneak';
DefendAction: 'defend' | 'defending';
GenericAction: action=ID;

Target: 
    'target' 'in' 'your' 'space' |
    'target' 'not' 'in' 'your' 'space' |
    'any' 'target' |
    'figures' 'in' 'your' 'space'
;

// Effects
Effect:
    DiceEffect | RerollEffect | HealingEffect | 
    DefensiveEffect | ConversionEffect | ActionEffect
;

DiceEffect: 
    'gain' | 'add' quantity=INT color=Color 'dice' |
    'gain' | 'add' quantity=INT color=Color 'die'
;

Color: 'green' | 'black';

RerollEffect:
    'reroll' quantity=INT ('die' | 'dice') |
    quantity=INT ('free' | 'standard') 'reroll'
;

HealingEffect:
    'heal' quantity=INT ('wound' | 'wounds') |
    'heal' quantity=INT 'stress' |
    'heal' quantity=INT 'wound' 'and' quantity2=INT 'stress'
;

DefensiveEffect:
    'reduce' 'wounds' 'by' quantity=INT |
    'reduce' 'sanity' 'by' quantity=INT |
    'reduce' 'wounds' 'and' 'sanity' 'by' quantity=INT
;

ConversionEffect:
    'count' quantity=INT ('elder' 'sign' | 'elder' 'signs' | 'arcane') 'as' ('success' | 'successes') |
    'count' 'any' 'number' 'of' ('elder' 'signs' | 'arcane') 'as' ('success' | 'successes')
;

ActionEffect:
    'perform' quantity=INT ('free' | 'standard') action=Action |
    'gain' quantity=INT ('free' | 'standard') action=Action
;

// Scope
Scope:
    'while' predicate=Predicate |
    'per' 'turn' |
    'once' 'per' 'turn' |
    'when' action=Action
;

Predicate:
    'attacking' |
    'sanity' 'is' 'on' 'red' |
    'sanity' 'on' 'red' |
    'attacked' |
    'rolling' 'for' 'fire'
;

// Keywords
COMMENT: /\/\/.*$/;
%import common.INT
%import common.ID
%import common.WS
%ignore WS
%ignore COMMENT
"""
```

---

## Example Parsing

### Example 1: Simple Dice Addition
**Input:** "Gain 1 green dice"

**Parsed Structure:**
```python
GameRule(
    conditions=[],
    effects=[
        DiceEffect(quantity=1, color="green")
    ],
    scope=None
)
```

---

### Example 2: Conditional Dice Addition
**Input:** "When you attack, gain 1 green dice"

**Parsed Structure:**
```python
GameRule(
    conditions=[
        WhenCondition(action=AttackAction())
    ],
    effects=[
        DiceEffect(quantity=1, color="green")
    ],
    scope=None
)
```

---

### Example 3: Complex Rule
**Input:** "When you attack, you may target figures in your space. Gain 1 green dice while attacking a target in your space."

**Parsed Structure:**
```python
GameRule(
    conditions=[
        WhenCondition(action=AttackAction(target=Target("figures in your space")))
    ],
    effects=[
        DiceEffect(quantity=1, color="green")
    ],
    scope=Scope(predicate="attacking a target in your space")
)
```

---

## Pydantic Model Representation

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Target(BaseModel):
    location: Literal["your space", "not in your space", "any"]
    type: Literal["figures", "target", "any"]

class Condition(BaseModel):
    type: Literal["when", "while", "if"]
    action: Optional[str] = None
    predicate: Optional[str] = None

class DiceEffect(BaseModel):
    quantity: int
    color: Literal["green", "black"]

class RerollEffect(BaseModel):
    quantity: int
    type: Literal["free", "standard"]

class HealingEffect(BaseModel):
    wounds: int = 0
    stress: int = 0

class DefensiveEffect(BaseModel):
    wound_reduction: int = 0
    sanity_reduction: int = 0

class ConversionEffect(BaseModel):
    elder_signs: int  # 0 means "any number"
    successes_per: int = 1  # Usually 1, can be 2

class Effect(BaseModel):
    type: Literal["dice", "reroll", "healing", "defensive", "conversion", "action"]
    dice: Optional[DiceEffect] = None
    reroll: Optional[RerollEffect] = None
    healing: Optional[HealingEffect] = None
    defensive: Optional[DefensiveEffect] = None
    conversion: Optional[ConversionEffect] = None

class Scope(BaseModel):
    type: Literal["while", "per_turn", "when"]
    predicate: Optional[str] = None
    action: Optional[str] = None

class GameRule(BaseModel):
    """Structured representation of a game rule/power."""
    conditions: List[Condition] = Field(default_factory=list)
    effects: List[Effect] = Field(default_factory=list)
    scope: Optional[Scope] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "conditions": [c.model_dump() for c in self.conditions],
            "effects": [e.model_dump() for e in self.effects],
            "scope": self.scope.model_dump() if self.scope else None
        }
```

---

## Translation Strategy

### Step 1: NLP Preprocessing (spaCy)
- Sentence segmentation
- Dependency parsing
- Entity extraction (numbers, dice types)
- Phrase chunking

### Step 2: Pattern Matching
- Match against grammar patterns
- Extract entities using NLP results
- Handle variations and synonyms

### Step 3: DSL Generation
- Map matched patterns to DSL structures
- Validate against schema
- Handle ambiguities

---

## Handling Variations

### Synonyms
- "gain" / "add" / "receive" → DiceEffect
- "when" / "while" / "if" → Condition
- "elder sign" / "arcane" / "elder signs" → ConversionEffect

### OCR Errors
- Pre-process with existing OCR correction system
- Use fuzzy matching for known OCR errors
- Validate against expected patterns

### Ambiguities
- "1 green dice" vs "1 green die" → Normalize to plural
- "when attacking" vs "while attacking" → Treat as equivalent
- Multiple effects in one sentence → Split and parse separately

---

## Testing Strategy

### Unit Tests
- Test each grammar rule individually
- Test pattern matching with variations
- Test edge cases and ambiguities

### Integration Tests
- Test full parsing pipeline
- Test with real power descriptions
- Validate against known correct structures

### Validation Tests
- Ensure parsed structures match expected game mechanics
- Verify statistics calculations match parsed effects
- Compare with manual analysis

---

## Next Steps

1. **Implement TextX grammar** - Start with simple rules
2. **Create Pydantic models** - Define structured representation
3. **Build NLP preprocessor** - Use spaCy for entity extraction
4. **Implement translator** - Map NLP → DSL
5. **Test with real data** - Validate against existing power descriptions

---

**Status:** Design Phase  
**Last Updated:** 2024-12-19

