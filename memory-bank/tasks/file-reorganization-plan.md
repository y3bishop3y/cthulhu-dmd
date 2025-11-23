# File Reorganization & JSON Schema Enhancement Plan

## Current State Analysis

### Directory Structure Issues
- **Inconsistent nesting**: `season1` uses `data/season1/characters/{char}/` while others use `data/{season}/{char}/`
- **Mixed file naming**: Some have `front.jpg`/`back.jpg`, others have `front.png`/`back_annotated.png`
- **Story storage inconsistency**: Some have `story.txt` files, others have `story` in JSON

### JSON Schema Issues
- **Character JSON**: Varies in completeness (some have `story`, `special_power`, others don't)
- **Season JSON**: Simplified summaries in `sites/data/seasons/` missing full character details
- **Missing fields**: No standardized fields for images, audio, metadata

---

## Phase 1: Standardize Directory Structure

### Goal
Create consistent directory structure across all seasons/boxes.

### Actions
1. **Standardize to flat structure**: `data/{season}/{character}/`
   - Move `season1/characters/*` → `season1/*` (remove `characters/` subdirectory)
   - Ensure all seasons follow same pattern

2. **Standardize file naming**:
   - `front.jpg` / `front.webp` (primary formats)
   - `back.jpg` / `back.webp` (primary formats)
   - `character.json` (always present)
   - `story.txt` (optional, if story exists separately)
   - Remove/consolidate `*_annotated.png` files (move to archive or delete)

3. **Create consistent subdirectories** (if needed):
   - `images/` - for organized image storage (optional)
   - `audio/` - for audio files (if any)
   - `animation/` - for animation-related files (if any)

### Expected Outcome
```
data/
  season1/
    adam/
      character.json
      front.jpg
      front.webp
      back.jpg
      back.webp
      story.txt (optional)
    ...
  season2/
    adilah/
      character.json
      front.jpg
      back.jpg
      story.txt (optional)
    ...
```

---

## Location Parsing Strategy

### Goal
Parse location strings from cards into structured data for search optimization while preserving original text.

### Location Format Examples
- `"MANCHESTER, ENGLAND"` → `{city: "Manchester", country: "England", region: "Europe"}`
- `"FALL RIVER, MASSACHUSETTS"` → `{city: "Fall River", state: "Massachusetts", country: "USA", region: "North America"}`
- `"UNKNOWN"` → `{city: null, state: null, country: null, region: null}`

### Parsing Rules
1. **Preserve original**: Always keep the exact scanned text in `location.original`
2. **Parse components**: Extract city, state, country from comma-separated format
3. **Map to regions**: Assign geographic regions:
   - Europe: England, France, Germany, Russia, etc.
   - North America: USA, Canada, Mexico
   - South America: Brazil, Colombia, etc.
   - Asia: Japan, China, India, etc.
   - Africa: Egypt, etc.
   - Oceania: Australia, New Zealand
4. **Handle special cases**:
   - "UNKNOWN" → all null
   - City only → try to infer country from context
   - State abbreviations → expand to full names

### Implementation
- Create `scripts/utils/location_parser.py` with:
  - `parse_location(location_string)` - Main parsing function
  - `get_region(country)` - Map country to region
  - `geocode_location(location_string)` - Optional: Get coordinates
  - Manual mapping dictionary for known locations

---

## Phase 2: Enhance Character JSON Schema

### Goal
Create comprehensive, standardized character JSON schema with all metadata, enhanced location data, and external links.

### Proposed Character JSON Schema
```json
{
  "id": "adam",                    // NEW: Character ID (slug)
  "name": "LORD ADAM BENCHLEY",    // Full display name
  "season": "season1",              // NEW: Season/box identifier
  "motto": "Shoot first. Never ask,",
  "story": "...",                   // Full story text
  
  // ENHANCED: Location with original + parsed data
  "location": {
    "original": "MANCHESTER, ENGLAND",  // Original text from card (what was scanned)
    "parsed": {                          // Parsed/computed values for search
      "city": "Manchester",
      "state": null,                     // State/Province (if applicable)
      "country": "England",
      "region": "Europe"                 // Geographic region (continent/macro-region)
    },
    "coordinates": {                     // Optional: GPS coordinates for mapping
      "lat": 53.4808,
      "lon": -2.2426
    }
  },
  
  "special_power": {                // Special power object (if exists)
    "name": "...",
    "levels": [...]
  },
  "common_powers": ["Swiftness", "Arcane Mastery"],
  
  // NEW: External links (open in new tab)
  "links": {
    "wikipedia": "https://en.wikipedia.org/wiki/...",  // Wikipedia URL (if exists)
    "other": [                                          // Other reference URLs
      "https://example.com/character/adam",
      "https://game-wiki.com/characters/adam"
    ]
  },
  
  // NEW: File references
  "images": {
    "front": {
      "jpg": "front.jpg",
      "webp": "front.webp"
    },
    "back": {
      "jpg": "back.jpg",
      "webp": "back.webp"
    }
  },
  
  // NEW: Audio/Media
  "has_audio": false,
  "audio_file": null,               // Filename if exists
  
  // NEW: Metadata
  "metadata": {
    "extracted_date": "2024-01-01", // When data was extracted
    "last_updated": "2024-01-15",   // Last update timestamp
    "data_source": "ocr",            // Source: ocr, manual, web_scrape
    "completeness": 0.95             // 0-1 score of data completeness
  }
}
```

### Actions
1. Add `id` field to all character JSON files (derived from directory name)
2. Add `season` field to all character JSON files
3. **Transform `location` from string to object**:
   - Keep original scanned text in `location.original`
   - Parse and add structured data in `location.parsed` (city, state, country, region)
   - Add optional coordinates for mapping
4. Add `links` object for external references (Wikipedia, game wikis, etc.)
5. Consolidate `story.txt` files into `story` field in JSON (or keep both for reference)
6. Add `images` object referencing available image files
7. Add `has_audio` and `audio_file` fields
8. Add `metadata` object with extraction/update info
9. Ensure all required fields are present (set to `null` if missing)

---

## Phase 3: Enhance Season JSON Schema

### Goal
Create comprehensive season JSON files with full character details and season metadata.

### Proposed Season JSON Schema
```json
{
  "id": "season1",
  "name": "Season 1",
  "description": "...",              // NEW: Season description
  "amazon_link": "...",
  "release_date": null,              // NEW: Release date
  "box_type": "expansion",           // NEW: expansion, standalone, promo
  "character_count": 10,             // NEW: Number of characters
  
  // NEW: Season-level images
  "images": {
    "box_art": "season-1-box.jpg",   // Box art image
    "character_book": "character-book.pdf"
  },
  
  // NEW: Metadata
  "metadata": {
    "last_updated": "2024-01-15",
    "data_completeness": 0.90        // Overall completeness score
  },
  
  "characters": [
    {
      // Full character object (same as Phase 2 schema)
      "id": "adam",
      "name": "LORD ADAM BENCHLEY",
      ...
    }
  ]
}
```

### Actions
1. Update `generate_site.py` to include full character objects (not just summaries)
2. Add season-level metadata fields
3. Add season-level image references
4. Calculate and include completeness scores
5. Add `character_count` field

---

## Phase 4: Update Generation Scripts & Add Search System

### Goal
Update scripts to work with new schema and structure, and implement search functionality.

### Actions
1. **Update `generate_site.py`**:
   - Read from standardized directory structure
   - Generate character JSON with new schema fields
   - Generate season JSON with enhanced metadata
   - Handle missing fields gracefully
   - **Generate inverted index files for search**:
     - `powers.json` - Maps powers to character IDs
     - `locations.json` - Maps locations (city/state/country/region) to character IDs
     - `characters.json` - Full character data array for search

2. **Update parsing scripts**:
   - Ensure they write to new schema format
   - Populate `id` and `season` fields automatically
   - Update `images` object when files are processed
   - Parse location strings into structured format
   - Extract/validate external links

3. **Create location parsing utility**:
   - Parse location strings like "MANCHESTER, ENGLAND" into structured format
   - Map to regions (Europe, North America, etc.)
   - Optionally geocode for coordinates

4. **Create migration script**:
   - Script to migrate existing JSON files to new schema
   - Transform `location` strings to objects (preserve original, add parsed)
   - Consolidate `story.txt` files into JSON
   - Add missing fields with defaults
   - Validate schema compliance

5. **Create search index builder** (`build-indexes.js` or Python equivalent):
   - Build `powers.json` - index by common_powers
   - Build `locations.json` - index by parsed location fields (city, state, country, region)
   - Support fast O(1) lookups for search

---

## Phase 5: Validation & Testing

### Goal
Ensure all data is valid and consistent.

### Actions
1. **Schema validation**:
   - Create JSON schema files for validation
   - Validate all character JSON files
   - Validate all season JSON files

2. **Data completeness check**:
   - Identify missing fields
   - Identify missing files
   - Generate completeness report

3. **Cross-reference validation**:
   - Ensure all characters in season JSON exist in data directory
   - Ensure all referenced files exist
   - Check for orphaned files

---

## Phase 6: Website Enhancements (Search & UI)

### Search System Architecture

#### Inverted Index Structure

**powers.json** - Maps powers to character IDs:
```json
{
  "Swiftness": ["adam", "ian", "morgan"],
  "Arcane Mastery": ["adam", "ahmed", "ian", "rasputin", "the-kid"],
  "Brawling": ["borden", "fatima", "morgan", "rasputin", "sister-beth"],
  "Marksman": ["elizabeth", "the-kid"],
  "Stealth": ["ahmed", "elizabeth"],
  "Toughness": ["borden", "fatima", "sister-beth"]
}
```

**locations.json** - Maps locations to character IDs:
```json
{
  "regions": {
    "Europe": ["adam", "elizabeth", "rasputin"],
    "North America": ["borden", "ian", "morgan", "the-kid"],
    "South America": ["sister-beth"],
    "Africa": ["ahmed", "fatima"]
  },
  "countries": {
    "England": ["adam", "elizabeth"],
    "USA": ["borden", "ian", "morgan", "the-kid"],
    "Russia": ["rasputin"],
    "Colombia": ["sister-beth"],
    "Turkey": ["ahmed"],
    "Egypt": ["fatima"]
  },
  "states": {
    "Massachusetts": ["borden"],
    "Maine": ["ian"],
    "Indiana": ["morgan"]
  },
  "cities": {
    "Manchester": ["adam"],
    "London": ["elizabeth"],
    "Fall River": ["borden"],
    "Moscow": ["rasputin"]
  }
}
```

#### Search Functions (Client-Side)

```javascript
// Load indexes on page load
async function initializeSearch() {
  const [powers, locations, characters] = await Promise.all([
    fetch('data/powers.json').then(r => r.json()),
    fetch('data/locations.json').then(r => r.json()),
    fetch('data/characters.json').then(r => r.json())
  ]);
  // Store globally
  window.searchIndexes = { powers, locations, characters };
}

// Find by power (O(1) lookup)
function findByPower(power) {
  return window.searchIndexes.powers[power] || [];
}

// Find by location (searches all levels)
function findByLocation(location) {
  const loc = location.toLowerCase();
  const results = new Set();
  
  // Search cities, states, countries, regions
  ['cities', 'states', 'countries', 'regions'].forEach(level => {
    const matches = window.searchIndexes.locations[level][location] || [];
    matches.forEach(id => results.add(id));
  });
  
  return Array.from(results);
}

// Find by multiple powers (intersection)
function findByMultiplePowers(powerList) {
  if (powerList.length === 0) return [];
  const sets = powerList.map(p => new Set(findByPower(p)));
  return [...sets[0]].filter(id => sets.every(s => s.has(id)));
}

// Combined search
function findByPowerAndLocation(power, location) {
  const powerMatches = new Set(findByPower(power));
  const locationMatches = findByLocation(location);
  return locationMatches.filter(id => powerMatches.has(id));
}
```

### UI Components

#### Search Bar (Top of index.html)
- Power dropdown (multi-select or single)
- Location input (autocomplete from known locations)
- Search button
- Clear filters button

#### Results Display
- Filter existing table (hide/show rows)
- Highlight matching characters
- Show filter badges (e.g., "Power: Swiftness", "Location: Europe")

#### Character Card Modal
- Click on card image → opens modal
- Modal shows:
  - Full-size front card image
  - Full-size back card image (side-by-side or tabs)
  - Close button (X)
  - Click outside to close
  - Keyboard support (ESC to close)

#### External Links Display
- Character detail page: Links section with icons
- Season table: Link icon column (if character has links)
- All links open in new tab: `target="_blank" rel="noopener noreferrer"`

---

### Goal
Add search functionality and improve character display with clickable cards and external links.

### Actions
1. **Add search functionality** (`sites/js/search.js`):
   - Load inverted index files (`powers.json`, `locations.json`, `characters.json`)
   - Implement search functions:
     - `findByPower(power)` - Find characters by power
     - `findByLocation(location)` - Find by city/state/country/region
     - `findByMultiplePowers(powerList)` - Find characters with ALL powers
     - `findByPowerAndLocation(power, location)` - Combined search
     - `getCharacterDetails(name)` - Get full character object
   - Add search UI to `index.html`:
     - Power dropdown/selector
     - Location search input
     - Results display area
     - Filter by multiple criteria

2. **Enhance character card display**:
   - Make character cards clickable (in table view)
   - Add modal/lightbox for larger card view:
     - Click on card image → opens modal with full-size image
     - Modal shows front/back cards side-by-side
     - Close button or click outside to dismiss
   - Add external links section:
     - Display Wikipedia link (if exists) - opens in new tab
     - Display other links - opens in new tab
     - Use `target="_blank" rel="noopener noreferrer"` for security

3. **Update character detail page** (`character.html`):
   - Display enhanced location info (show both original and parsed)
   - Add external links section with proper new-tab behavior
   - Make card images clickable for full-size modal view
   - Improve card display with better image handling

4. **Update season page** (`index.html`):
   - Add search bar at top
   - Make character cards in table clickable for modal view
   - Add external links column or icon in table
   - Integrate search results with existing table display

---

## Phase 7: Documentation & Cleanup

### Goal
Document new structure and clean up old files.

### Actions
1. **Update documentation**:
   - Document new JSON schema (with location structure)
   - Document search system and inverted indexes
   - Document directory structure standards
   - Update README files
   - Document external links format

2. **Cleanup**:
   - Remove duplicate files
   - Archive old structure if needed
   - Remove unused `*_annotated.png` files

---

## Implementation Order

1. **Phase 1** - Standardize directories (foundation)
2. **Phase 2** - Enhance character JSON (data layer)
   - Transform location to object structure
   - Add links field
3. **Phase 3** - Enhance season JSON (aggregation layer)
4. **Phase 4** - Update scripts & add search system (automation)
   - Update generation scripts
   - Create location parser
   - Build search index generator
5. **Phase 5** - Validate (quality assurance)
6. **Phase 6** - Website enhancements (search & UI)
   - Add search functionality
   - Add clickable cards with modal
   - Add external links display
7. **Phase 7** - Documentation & cleanup (finalization)

---

## Questions to Resolve

1. **Story storage**: Keep `story.txt` files or consolidate entirely into JSON?
2. **Image formats**: Standardize on JPG only, or keep both JPG and WEBP?
3. **Annotated images**: Archive `*_annotated.png` or delete?
4. **Metadata fields**: Which metadata fields are most important?
5. **Backward compatibility**: Need to maintain old schema for any reason?
6. **Location parsing**: Use manual mapping or geocoding API? (Manual mapping recommended for accuracy)
7. **Search UI**: Inline search bar or separate search page?
8. **Modal library**: Use custom modal or library (e.g., Lightbox.js, Fancybox)?

---

## Files to Modify

### Data Files
- All `data/{season}/{character}/character.json` files
- All `sites/data/seasons/{season}.json` files
- `sites/data/seasons.json` - Main seasons index

### Scripts
- `sites/scripts/generate_site.py` - Main generation script (add search index generation)
- `scripts/cli/parse/characters.py` - Character parsing (location parsing)
- `scripts/cli/download/characters.py` - Download script
- **NEW**: `sites/scripts/build_indexes.py` - Search index builder
- **NEW**: `scripts/utils/location_parser.py` - Location parsing utility

### Website Files
- `sites/index.html` - Add search UI, clickable cards
- `sites/character.html` - Add external links, clickable cards
- `sites/js/app.js` - Add search integration, modal functionality
- `sites/js/character.js` - Add external links, modal for cards
- **NEW**: `sites/js/search.js` - Search functionality
- **NEW**: `sites/js/modal.js` - Modal/lightbox functionality

### Generated Files (by scripts)
- `sites/data/powers.json` - Power index (generated)
- `sites/data/locations.json` - Location index (generated)
- `sites/data/characters.json` - Full character array (generated, optional)

