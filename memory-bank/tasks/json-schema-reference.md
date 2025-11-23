# JSON Schema Reference

## Character JSON Schema

### Complete Example

```json
{
  "id": "adam",
  "name": "LORD ADAM BENCHLEY",
  "season": "season1",
  "motto": "Shoot first. Never ask,",
  "story": "Lord Adam Benchley is a man of action...",
  
  "location": {
    "original": "MANCHESTER, ENGLAND",
    "parsed": {
      "city": "Manchester",
      "state": null,
      "country": "England",
      "region": "Europe"
    },
    "coordinates": {
      "lat": 53.4808,
      "lon": -2.2426
    }
  },
  
  "special_power": {
    "name": "VENGEANCE OBSESSION",
    "is_special": true,
    "levels": [
      {
        "level": 1,
        "description": "When attack, if you are dealt any wounds..."
      }
    ],
    "has_levels": true,
    "is_complete": true
  },
  
  "common_powers": [
    "Swiftness",
    "Arcane Mastery"
  ],
  
  "links": {
    "wikipedia": "https://en.wikipedia.org/wiki/...",
    "other": [
      "https://game-wiki.com/characters/adam",
      "https://boardgamegeek.com/character/adam"
    ]
  },
  
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
  
  "has_audio": true,
  "audio_file": "adam_audio_p225.wav",
  
  "metadata": {
    "extracted_date": "2024-01-01",
    "last_updated": "2024-01-15",
    "data_source": "ocr",
    "completeness": 0.95
  }
}
```

### Minimal Example (Missing Fields)

```json
{
  "id": "jack",
  "name": "Jack",
  "season": "comic-book-extras",
  "motto": null,
  "story": null,
  
  "location": {
    "original": null,
    "parsed": {
      "city": null,
      "state": null,
      "country": null,
      "region": null
    },
    "coordinates": null
  },
  
  "special_power": null,
  "common_powers": ["Brawling", "Swiftness"],
  
  "links": {
    "wikipedia": null,
    "other": []
  },
  
  "images": {
    "front": {
      "jpg": "front.jpg",
      "webp": null
    },
    "back": {
      "jpg": "back.jpg",
      "webp": null
    }
  },
  
  "has_audio": false,
  "audio_file": null,
  
  "metadata": {
    "extracted_date": null,
    "last_updated": "2024-01-15",
    "data_source": "manual",
    "completeness": 0.60
  }
}
```

### Location Examples

#### USA Location (with state)
```json
"location": {
  "original": "FALL RIVER, MASSACHUSETTS",
  "parsed": {
    "city": "Fall River",
    "state": "Massachusetts",
    "country": "USA",
    "region": "North America"
  },
  "coordinates": {
    "lat": 41.7015,
    "lon": -71.1550
  }
}
```

#### UK Location (no state)
```json
"location": {
  "original": "MANCHESTER, ENGLAND",
  "parsed": {
    "city": "Manchester",
    "state": null,
    "country": "England",
    "region": "Europe"
  },
  "coordinates": {
    "lat": 53.4808,
    "lon": -2.2426
  }
}
```

#### Unknown Location
```json
"location": {
  "original": "UNKNOWN",
  "parsed": {
    "city": null,
    "state": null,
    "country": null,
    "region": null
  },
  "coordinates": null
}
```

---

## Season JSON Schema

### Complete Example

```json
{
  "id": "season1",
  "name": "Season 1",
  "description": "The first expansion for Cthulhu: Death May Die",
  "amazon_link": "https://www.amazon.com/...",
  "release_date": "2019-01-01",
  "box_type": "expansion",
  "character_count": 10,
  
  "images": {
    "box_art": "season-1-box.jpg",
    "character_book": "character-book.pdf"
  },
  
  "metadata": {
    "last_updated": "2024-01-15",
    "data_completeness": 0.90
  },
  
  "characters": [
    {
      "id": "adam",
      "name": "LORD ADAM BENCHLEY",
      "motto": "Shoot first. Never ask,",
      "location": {
        "original": "MANCHESTER, ENGLAND",
        "parsed": {
          "city": "Manchester",
          "state": null,
          "country": "England",
          "region": "Europe"
        }
      },
      "common_powers": ["Swiftness", "Arcane Mastery"],
      "has_audio": true,
      "links": {
        "wikipedia": null,
        "other": []
      }
    }
    // ... more characters
  ]
}
```

---

## Search Index Files

### powers.json

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

### locations.json

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

---

## Field Reference

### Character JSON Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Character ID (slug, lowercase) |
| `name` | string | Yes | Full display name |
| `season` | string | Yes | Season/box identifier |
| `motto` | string\|null | Yes | Character motto/quote |
| `story` | string\|null | Yes | Character background story |
| `location.original` | string\|null | Yes | Original scanned text from card |
| `location.parsed.city` | string\|null | Yes | Parsed city name |
| `location.parsed.state` | string\|null | Yes | State/Province (if applicable) |
| `location.parsed.country` | string\|null | Yes | Country name |
| `location.parsed.region` | string\|null | Yes | Geographic region |
| `location.coordinates.lat` | number\|null | No | Latitude |
| `location.coordinates.lon` | number\|null | No | Longitude |
| `special_power` | object\|null | Yes | Special power details |
| `common_powers` | array | Yes | List of common power names |
| `links.wikipedia` | string\|null | Yes | Wikipedia URL |
| `links.other` | array | Yes | Other reference URLs |
| `images.front.jpg` | string\|null | Yes | Front card JPG filename |
| `images.front.webp` | string\|null | Yes | Front card WEBP filename |
| `images.back.jpg` | string\|null | Yes | Back card JPG filename |
| `images.back.webp` | string\|null | Yes | Back card WEBP filename |
| `has_audio` | boolean | Yes | Whether audio file exists |
| `audio_file` | string\|null | Yes | Audio filename if exists |
| `metadata.extracted_date` | string\|null | Yes | ISO date when extracted |
| `metadata.last_updated` | string | Yes | ISO date of last update |
| `metadata.data_source` | string | Yes | Source: "ocr", "manual", "web_scrape" |
| `metadata.completeness` | number | Yes | Completeness score (0-1) |

### Season JSON Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Season ID (slug) |
| `name` | string | Yes | Display name |
| `description` | string\|null | Yes | Season description |
| `amazon_link` | string\|null | Yes | Purchase link |
| `release_date` | string\|null | Yes | ISO release date |
| `box_type` | string | Yes | "expansion", "standalone", "promo" |
| `character_count` | number | Yes | Number of characters |
| `images.box_art` | string\|null | Yes | Box art image filename |
| `images.character_book` | string\|null | Yes | Character book PDF filename |
| `metadata.last_updated` | string | Yes | ISO date of last update |
| `metadata.data_completeness` | number | Yes | Overall completeness (0-1) |
| `characters` | array | Yes | Array of character objects |

---

## Migration Notes

### Location Migration

**Before:**
```json
{
  "location": "MANCHESTER, ENGLAND"
}
```

**After:**
```json
{
  "location": {
    "original": "MANCHESTER, ENGLAND",
    "parsed": {
      "city": "Manchester",
      "state": null,
      "country": "England",
      "region": "Europe"
    },
    "coordinates": null
  }
}
```

### Adding Links

**Before:**
```json
{
  "name": "Adam"
}
```

**After:**
```json
{
  "name": "Adam",
  "links": {
    "wikipedia": null,
    "other": []
  }
}
```

### Adding Images Object

**Before:**
```json
{
  "name": "Adam"
}
```

**After:**
```json
{
  "name": "Adam",
  "images": {
    "front": {
      "jpg": "front.jpg",
      "webp": "front.webp"
    },
    "back": {
      "jpg": "back.jpg",
      "webp": "back.webp"
    }
  }
}
```

