#!/usr/bin/env python3
"""
Identify Lovecraft characters and add Wikipedia/Grokpedia links.

This script:
1. Loads all characters from all seasons
2. Matches character names against known Lovecraft characters
3. Updates character_links.json with Wikipedia/Grokpedia links
4. Updates character.json files with links
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTER_LINKS_FILE = DATA_DIR / "character_links.json"
MANUAL_MAPPINGS_FILE = DATA_DIR / "lovecraft_character_mappings.json"


# Known Lovecraft characters with their Wikipedia/Grokpedia links
LOVECRAFT_CHARACTERS = {
    # Main protagonists
    "randolph carter": {
        "wikipedia": "https://en.wikipedia.org/wiki/Randolph_Carter",
        "grokpedia": "https://grokipedia.com/page/Randolph_Carter",
        "stories": [
            "The Statement of Randolph Carter",
            "The Dream-Quest of Unknown Kadath",
            "The Silver Key",
        ],
    },
    "herbert west": {
        "wikipedia": "https://en.wikipedia.org/wiki/Herbert_West%E2%80%93Reanimator",
        "grokpedia": "https://grokipedia.com/page/Herbert_West",
        "stories": ["Herbert West–Reanimator"],
    },
    "charles dexter ward": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Charles_Dexter_Ward",
        "stories": ["The Case of Charles Dexter Ward"],
    },
    "richard upton pickman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Pickman%27s_Model",
        "grokpedia": "https://grokipedia.com/page/Richard_Upton_Pickman",
        "stories": ["Pickman's Model"],
    },
    "nathaniel wingate peaslee": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Shadow_Out_of_Time",
        "grokpedia": "https://grokipedia.com/page/Nathaniel_Wingate_Peaslee",
        "stories": ["The Shadow Out of Time"],
    },
    "wilbur whateley": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Wilbur_Whateley",
        "stories": ["The Dunwich Horror"],
    },
    "lavinia whateley": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Lavinia_Whateley",
        "stories": ["The Dunwich Horror"],
    },
    "asenath waite": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Thing_on_the_Doorstep",
        "grokpedia": "https://grokipedia.com/page/Asenath_Waite",
        "stories": ["The Thing on the Doorstep"],
    },
    "keziah mason": {
        "wikipedia": "https://en.wikipedia.org/wiki/Dreams_in_the_Witch_House",
        "grokpedia": "https://grokipedia.com/page/Keziah_Mason",
        "stories": ["Dreams in the Witch House"],
    },
    "edward derby": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Thing_on_the_Doorstep",
        "grokpedia": "https://grokipedia.com/page/Edward_Derby",
        "stories": ["The Thing on the Doorstep"],
    },
    "francis wayland thurston": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/Francis_Wayland_Thurston",
        "stories": ["The Call of Cthulhu"],
    },
    "henry armitage": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Henry_Armitage",
        "stories": ["The Dunwich Horror"],
    },
    "walter gilman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Dreams_in_the_Witch_House",
        "grokpedia": "https://grokipedia.com/page/Walter_Gilman",
        "stories": ["Dreams in the Witch House"],
    },
    "thomas olney": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Strange_High_House_in_the_Mist",
        "grokpedia": "https://grokipedia.com/page/Thomas_Olney",
        "stories": ["The Strange High House in the Mist"],
    },
    "george gammell angell": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/George_Gammell_Angell",
        "stories": ["The Call of Cthulhu"],
    },
    "johansen": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/Johansen",
        "stories": ["The Call of Cthulhu"],
    },
    "delapore": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Rats_in_the_Walls",
        "grokpedia": "https://grokipedia.com/page/Delapore",
        "stories": ["The Rats in the Walls"],
    },
    "joseph curwen": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Joseph_Curwen",
        "stories": ["The Case of Charles Dexter Ward"],
    },
    "ezra weeden": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Ezra_Weeden",
        "stories": ["The Case of Charles Dexter Ward"],
    },
    "danforth": {
        "wikipedia": "https://en.wikipedia.org/wiki/At_the_Mountains_of_Madness",
        "grokpedia": "https://grokipedia.com/page/Danforth",
        "stories": ["At the Mountains of Madness"],
    },
    "william dyer": {
        "wikipedia": "https://en.wikipedia.org/wiki/At_the_Mountains_of_Madness",
        "grokpedia": "https://grokipedia.com/page/William_Dyer",
        "stories": ["At the Mountains of Madness"],
    },
    "lake": {
        "wikipedia": "https://en.wikipedia.org/wiki/At_the_Mountains_of_Madness",
        "grokpedia": "https://grokipedia.com/page/Lake",
        "stories": ["At the Mountains of Madness"],
    },
    "carter": {
        "wikipedia": "https://en.wikipedia.org/wiki/Randolph_Carter",
        "grokpedia": "https://grokipedia.com/page/Randolph_Carter",
        "stories": ["Multiple stories"],
        "note": "May refer to Randolph Carter",
    },
    "west": {
        "wikipedia": "https://en.wikipedia.org/wiki/Herbert_West%E2%80%93Reanimator",
        "grokpedia": "https://grokipedia.com/page/Herbert_West",
        "stories": ["Herbert West–Reanimator"],
        "note": "May refer to Herbert West",
    },
    "ward": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Charles_Dexter_Ward",
        "stories": ["The Case of Charles Dexter Ward"],
        "note": "May refer to Charles Dexter Ward",
    },
    "pickman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Pickman%27s_Model",
        "grokpedia": "https://grokipedia.com/page/Richard_Upton_Pickman",
        "stories": ["Pickman's Model"],
        "note": "May refer to Richard Upton Pickman",
    },
    "peaslee": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Shadow_Out_of_Time",
        "grokpedia": "https://grokipedia.com/page/Nathaniel_Wingate_Peaslee",
        "stories": ["The Shadow Out of Time"],
        "note": "May refer to Nathaniel Wingate Peaslee",
    },
    "whateley": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Whateley",
        "stories": ["The Dunwich Horror"],
        "note": "May refer to Wilbur or Lavinia Whateley",
    },
    "derby": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Thing_on_the_Doorstep",
        "grokpedia": "https://grokipedia.com/page/Edward_Derby",
        "stories": ["The Thing on the Doorstep"],
        "note": "May refer to Edward Derby",
    },
    "armitage": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Henry_Armitage",
        "stories": ["The Dunwich Horror"],
        "note": "May refer to Henry Armitage",
    },
    "gilman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Dreams_in_the_Witch_House",
        "grokpedia": "https://grokipedia.com/page/Walter_Gilman",
        "stories": ["Dreams in the Witch House"],
        "note": "May refer to Walter Gilman",
    },
    "olney": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Strange_High_House_in_the_Mist",
        "grokpedia": "https://grokipedia.com/page/Thomas_Olney",
        "stories": ["The Strange High House in the Mist"],
        "note": "May refer to Thomas Olney",
    },
    "angell": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/George_Gammell_Angell",
        "stories": ["The Call of Cthulhu"],
        "note": "May refer to George Gammell Angell",
    },
    "curwen": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Joseph_Curwen",
        "stories": ["The Case of Charles Dexter Ward"],
        "note": "May refer to Joseph Curwen",
    },
    "weeden": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Ezra_Weeden",
        "stories": ["The Case of Charles Dexter Ward"],
        "note": "May refer to Ezra Weeden",
    },
    "dyer": {
        "wikipedia": "https://en.wikipedia.org/wiki/At_the_Mountains_of_Madness",
        "grokpedia": "https://grokipedia.com/page/William_Dyer",
        "stories": ["At the Mountains of Madness"],
        "note": "May refer to William Dyer",
    },
}


def normalize_name(name: str) -> str:
    """Normalize character name for matching."""
    # Remove common titles and normalize
    name = name.upper()
    name = name.replace("LORD ", "").replace("SERGEANT ", "").replace("SISTER ", "")
    name = name.replace("THE ", "").strip()
    return name.lower().strip()


def load_manual_mappings() -> Dict[str, str]:
    """Load manual character mappings from JSON file."""
    if not MANUAL_MAPPINGS_FILE.exists():
        return {}

    try:
        with open(MANUAL_MAPPINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("confirmed_mappings", {})
    except Exception as e:
        print(f"Warning: Error loading manual mappings: {e}")
        return {}


def match_character_name(
    character_name: str, char_id: str, manual_mappings: Dict[str, str]
) -> Optional[Tuple[str, Dict]]:
    """Match character name against Lovecraft characters."""
    # Check manual mappings first
    if char_id.lower() in manual_mappings:
        lovecraft_key = manual_mappings[char_id.lower()]
        if lovecraft_key in LOVECRAFT_CHARACTERS:
            return (lovecraft_key, LOVECRAFT_CHARACTERS[lovecraft_key])

    normalized = normalize_name(character_name)

    # Skip very short names (likely false positives)
    if len(normalized) < 3:
        return None

    # Direct exact match (full name)
    if normalized in LOVECRAFT_CHARACTERS:
        return (normalized, LOVECRAFT_CHARACTERS[normalized])

    # Only match distinctive full names to avoid false positives
    # For now, we'll be conservative and only match if manual mapping exists
    # or if it's a very distinctive match

    return None


def load_character_links() -> Dict[str, Dict[str, Any]]:
    """Load existing character links."""
    if not CHARACTER_LINKS_FILE.exists():
        return {}

    try:
        with open(CHARACTER_LINKS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            # Remove comment field if present
            return {k: v for k, v in data.items() if k != "_comment"}
    except Exception as e:
        print(f"Warning: Error loading character links: {e}")
        return {}


def save_character_links(links: Dict[str, Dict[str, Any]]):
    """Save character links to JSON file."""
    output = {
        "_comment": "Historical/fictional character links for Wikipedia and Grokpedia",
        **links,
    }

    try:
        with open(CHARACTER_LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving character links: {e}")
        return False


def load_all_characters() -> List[Dict[str, Any]]:
    """Load all characters from all seasons."""
    characters = []

    for season_dir in DATA_DIR.iterdir():
        if not season_dir.is_dir() or season_dir.name.startswith("."):
            continue

        chars_dir = season_dir / "characters"
        if not chars_dir.exists():
            continue

        for char_dir in chars_dir.iterdir():
            if not char_dir.is_dir():
                continue

            char_json = char_dir / "character.json"
            if not char_json.exists():
                continue

            try:
                with open(char_json, encoding="utf-8") as f:
                    char_data = json.load(f)
                    char_data["_season"] = season_dir.name
                    char_data["_char_dir"] = char_dir
                    characters.append(char_data)
            except Exception as e:
                print(f"Warning: Error loading {char_json}: {e}")

    return characters


def update_character_json(char_dir: Path, links: Dict[str, str]):
    """Update character.json with links."""
    char_json = char_dir / "character.json"

    if not char_json.exists():
        return False

    try:
        with open(char_json, encoding="utf-8") as f:
            data = json.load(f)

        # Update links
        if "links" not in data:
            data["links"] = {}

        data["links"]["wikipedia"] = links.get("wikipedia")
        data["links"]["grokpedia"] = links.get("grokpedia")
        if "other" not in data["links"]:
            data["links"]["other"] = links.get("other", [])

        with open(char_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"  Error updating {char_json}: {e}")
        return False


def main():
    """Identify Lovecraft characters and update links."""
    print("Identifying Lovecraft characters...")
    print("=" * 60)

    # Load manual mappings
    manual_mappings = load_manual_mappings()
    if manual_mappings:
        print(f"Loaded {len(manual_mappings)} manual mappings")

    # Load existing links
    character_links = load_character_links()

    # Load all characters
    characters = load_all_characters()

    matches_found = []
    matches_updated = []

    for char_data in characters:
        char_id = char_data.get("id", "")
        char_name = char_data.get("name", "")

        if not char_name:
            continue

        # Skip if char_id is empty
        if not char_id:
            continue

        # Check if already has links
        existing_links = char_data.get("links", {})
        if existing_links.get("wikipedia") or existing_links.get("grokpedia"):
            continue

        # Try to match
        match = match_character_name(char_name, char_id, manual_mappings)
        if match:
            lovecraft_name, link_data = match
            char_id_lower = char_id.lower()

            # Add to character_links.json
            character_links[char_id_lower] = {
                "wikipedia": link_data["wikipedia"],
                "grokpedia": link_data["grokpedia"],
                "other": [],
            }

            # Update character.json
            char_dir = char_data.get("_char_dir")
            if char_dir and update_character_json(char_dir, link_data):
                matches_updated.append((char_id, char_name, lovecraft_name))
                print(f"  ✓ {char_id} ({char_name}) → {lovecraft_name}")
            else:
                matches_found.append((char_id, char_name, lovecraft_name))
                print(f"  ⚠ {char_id} ({char_name}) → {lovecraft_name} (found but not updated)")

    # Save updated character_links.json
    if save_character_links(character_links):
        print("=" * 60)
        print(f"✓ Found {len(matches_found) + len(matches_updated)} Lovecraft character matches")
        print(f"✓ Updated {len(matches_updated)} character.json files")
        print("✓ Updated character_links.json")
    else:
        print("✗ Error saving character_links.json")


if __name__ == "__main__":
    main()
