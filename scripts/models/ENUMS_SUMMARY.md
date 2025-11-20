# Shared Enums and Constants Summary

## Enums Created

### 1. **ActionType** (`scripts/models/game_mechanics.py`)
   - `ATTACK`, `MOVE`, `RUN`, `REST`, `INVESTIGATE`, `TRADE`, `ACTION`
   - Used in: `ActionAddition` model

### 2. **CommonPower** (`scripts/models/constants.py`)
   - `ARCANE_MASTERY`, `BRAWLING`, `MARKSMAN`, `STEALTH`, `SWIFTNESS`, `TOUGHNESS`
   - Replaces: `COMMON_POWERS` lists in multiple scripts
   - Used in: `parse_characters.py`, `extract_and_update_common_powers.py`, `parse_trait_character_assignments.py`

### 3. **ImageType** (`scripts/models/constants.py`)
   - `FRONT`, `BACK`
   - Used for: Character card image types

### 4. **OutputFormat** (`scripts/models/constants.py`)
   - `JSON`, `YAML`, `MARKDOWN`, `TEXT`
   - Replaces: `OUTPUT_FORMAT_JSON`, `OUTPUT_FORMAT_YAML` constants

### 5. **FileExtension** (`scripts/models/constants.py`)
   - `.JPG`, `.JPEG`, `.WEBP`, `.PNG`, `.PDF`, `.JSON`, `.TXT`, `.YAML`, `.WAV`, `.MD`
   - Used for: File type validation and handling

### 6. **Season** (`scripts/models/constants.py`)
   - `SEASON1`, `SEASON2`, `SEASON3`, `SEASON4`, `UNSPEAKABLE_BOX`, `COMIC_BOOK_V2`
   - Replaces: Hardcoded season strings in `download_characters.py`

## Constants Classes

### 7. **Filename** (`scripts/models/constants.py`)
   - Centralized file name constants:
     - `FRONT = "front.jpg"`
     - `BACK = "back.jpg"`
     - `CHARACTER_JSON = "character.json"`
     - `STORY_TXT = "story.txt"`
     - `COMMON_POWERS = "common_powers.json"`
     - `TRAITS_BOOKLET = "traits_booklet.pdf"`
     - `CHARACTER_BOOK = "character-book.pdf"`
     - `RULEBOOK = "DMD_Rulebook_web.pdf"`
   - Replaces: `FILENAME_*` constants in multiple scripts

### 8. **Directory** (`scripts/models/constants.py`)
   - `DATA = "data"`
   - Replaces: `DATA_DIR` constants

## Existing Enums (Already Shared)

- **DiceType** (`game_mechanics.py`): `BLACK`, `GREEN`
- **DiceFaceSymbol** (`game_mechanics.py`): `SUCCESS`, `ELDER_SIGN`, `TENTACLE`, `BLANK`

## Next Steps: Refactoring Scripts

### High Priority
1. Replace `COMMON_POWERS` lists with `CommonPower` enum
2. Replace `FILENAME_*` constants with `Filename` class
3. Replace season strings with `Season` enum

### Medium Priority
4. Replace output format strings with `OutputFormat` enum
5. Use `ImageType` enum for image handling
6. Use `FileExtension` enum for file validation

## Usage Examples

```python
from scripts.models import CommonPower, Filename, Season, ImageType

# Instead of:
COMMON_POWERS = ["Arcane Mastery", "Brawling", ...]
if power_name in COMMON_POWERS:

# Use:
from scripts.models import CommonPower
if power_name == CommonPower.ARCANE_MASTERY.value:

# Instead of:
FILENAME_FRONT = "front.jpg"
front_path = char_dir / FILENAME_FRONT

# Use:
from scripts.models import Filename
front_path = char_dir / Filename.FRONT

# Instead of:
season = "season1"

# Use:
from scripts.models import Season
season = Season.SEASON1.value
```

