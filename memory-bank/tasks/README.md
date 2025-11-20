# Tasks & Planning Directory

This directory contains planning documents and progress tracking for major features and refactoring efforts.

## Documents

### `00-power-analysis-system-plan.md`
**Master plan for the Power Analysis System**

Comprehensive plan covering:
- Natural Language to Game Rules DSL parsing
- Power combination system
- Upgrade optimization
- Character synergy analysis

Includes:
- Implementation phases with checkboxes
- Library/framework research and recommendations
- File structure planning
- Success metrics

**Status:** Planning Phase  
**Last Updated:** 2024-12-19

---

### `01-dsl-grammar-design.md`
**DSL Grammar Design for Game Rules**

Detailed design for the Domain-Specific Language grammar:
- TextX grammar definition
- Pydantic model representations
- Translation strategy
- Testing approach

**Status:** Design Phase  
**Last Updated:** 2024-12-19

---

### `02-health-stress-mechanics.md`
**Health and Stress Mechanics Documentation**

Core game mechanics for character survival:
- Health track (5 slots, 6th hit = death)
- Stress track (5 slots, max 5)
- Rest action (3 healing points)
- Turn structure (3 actions per turn)

**Status:** Implemented  
**Last Updated:** 2024-12-19

---

### `03-insanity-track-mechanics.md`
**Insanity/Madness Track Mechanics Documentation**

Critical system affecting power upgrades and tentacle risk:
- Insanity track (20 slots, slot 21 = death)
- Red swirls (6 level-up opportunities at slots 5, 9, 13, 16, 19, 20)
- Green dice bonuses (4 permanent bonuses from red swirls 2, 4, 5, 6)
- Tentacle risk = death risk (especially at high insanity)
- Limited upgrades (only 6 total) - optimization critical

**Status:** Implemented  
**Last Updated:** 2024-12-19

---

### `04-character-build-analysis.md`
**Character Build Analysis Plan**

Bridges individual power statistics with full character analysis:
- Character build models (combining all powers)
- Full character statistics calculation
- Power value metrics
- Build comparison and optimization

**Status:** Planning Phase  
**Last Updated:** 2024-12-19

---

### `07-ocr-iteration-strategy.md`
**OCR Iteration Strategy Plan**

Systematic approach to testing and comparing OCR preprocessing + engine combinations:
- Multi-strategy testing framework (11+ combinations)
- Comparison against ground truth (character.json)
- Scoring by similarity and key phrase detection
- Plans for additional OCR engines (PaddleOCR, cloud APIs)
- Advanced preprocessing techniques
- Result combination strategies

**Status:** In Progress  
**Current Best**: Deskew preprocessing + Tesseract PSM 3 (35% similarity on Ahmed)  
**Last Updated:** 2024-12-19

---

## How to Use

1. **Review plans** - Read through the planning documents to understand the scope
2. **Track progress** - Update checkboxes as tasks are completed
3. **Update status** - Mark phases as "In Progress", "Complete", etc.
4. **Add notes** - Document decisions, challenges, or changes to the plan

## Status Legend

- ⏳ Not Started
- 🚧 In Progress
- ✅ Complete
- ❌ Blocked/Cancelled

---

**Note:** These are living documents - update them as the project evolves!

