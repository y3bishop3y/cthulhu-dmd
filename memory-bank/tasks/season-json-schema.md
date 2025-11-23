# Season JSON Schema Reference

## Overview

Each season directory should contain a `season.json` file with comprehensive metadata about the season/expansion box, including purchase links, images, and publication information.

## Complete Schema

```json
{
  "id": "season1",
  "name": "Season 1",
  "display_name": "Season 1: Base Game",
  "description": "The original Cthulhu: Death May Die expansion featuring 10 investigators battling the Old Ones.",
  "year_published": 2019,
  "release_date": "2019-06-01",
  "box_type": "base_game",
  "character_count": 10,
  "images": {
    "box_art": "season-1-box.jpg",
    "box_art_webp": "season-1-box.webp",
    "character_book": "character-book.pdf"
  },
  "purchase_links": {
    "amazon": "https://www.amazon.com/...",
    "publisher": "https://www.cmon.com/...",
    "boardgamegeek": "https://boardgamegeek.com/...",
    "other": []
  },
  "metadata": {
    "last_updated": "2025-01-15",
    "data_completeness": 0.95,
    "characters_complete": true,
    "audio_complete": true,
    "images_complete": true
  },
  "characters": [
    {
      "id": "adam",
      "name": "LORD ADAM BENCHLEY"
    }
  ]
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Season ID (slug, matches directory name) |
| `name` | string | Yes | Short name (e.g., "Season 1") |
| `display_name` | string | Yes | Full display name (e.g., "Season 1: Base Game") |
| `description` | string\|null | Yes | Season description/overview |
| `year_published` | number\|null | Yes | Year the season/box was published |
| `release_date` | string\|null | Yes | ISO date (YYYY-MM-DD) of release |
| `box_type` | string | Yes | Type: "base_game", "expansion", "standalone", "promo", "comic" |
| `character_count` | number | Yes | Number of characters in this season |
| `images.box_art` | string\|null | Yes | Box art image filename (JPG/PNG) |
| `images.box_art_webp` | string\|null | Yes | Box art WebP version (optional) |
| `images.character_book` | string\|null | Yes | Character book PDF filename |
| `purchase_links.amazon` | string\|null | Yes | Amazon affiliate/purchase link |
| `purchase_links.publisher` | string\|null | Yes | Publisher's direct purchase link |
| `purchase_links.boardgamegeek` | string\|null | Yes | BoardGameGeek page link |
| `purchase_links.other` | array | Yes | Array of other purchase links |
| `metadata.last_updated` | string | Yes | ISO date of last update |
| `metadata.data_completeness` | number | Yes | Overall completeness score (0-1) |
| `metadata.characters_complete` | boolean | Yes | Whether all characters have complete data |
| `metadata.audio_complete` | boolean | Yes | Whether all characters have audio files |
| `metadata.images_complete` | boolean | Yes | Whether all characters have images |
| `characters` | array | Yes | Array of character summary objects (id, name) |

## Box Types

- `base_game`: Core/base game
- `expansion`: Expansion box (requires base game)
- `standalone`: Standalone game/box
- `promo`: Promotional content
- `comic`: Comic book tie-in

## Minimal Example

```json
{
  "id": "season2",
  "name": "Season 2",
  "display_name": "Season 2: Expansion",
  "description": null,
  "year_published": null,
  "release_date": null,
  "box_type": "expansion",
  "character_count": 10,
  "images": {
    "box_art": "season-2-expansion-box.jpg",
    "box_art_webp": null,
    "character_book": "character-book.pdf"
  },
  "purchase_links": {
    "amazon": null,
    "publisher": null,
    "boardgamegeek": null,
    "other": []
  },
  "metadata": {
    "last_updated": "2025-01-15",
    "data_completeness": 0.3,
    "characters_complete": false,
    "audio_complete": false,
    "images_complete": true
  },
  "characters": []
}
```

## File Location

Season JSON files should be placed in:
```
data/{season-id}/season.json
```

Example:
```
data/season1/season.json
data/season2/season.json
data/unknowable-box/season.json
```

