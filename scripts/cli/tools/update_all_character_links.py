#!/usr/bin/env python3
"""
Update character_links.json for all characters across all seasons.
Identifies historical figures and Lovecraft characters.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTER_LINKS_FILE = DATA_DIR / "character_links.json"

# Historical figures database
HISTORICAL_FIGURES = {
    "al capone": {
        "wikipedia": "https://en.wikipedia.org/wiki/Al_Capone",
        "grokpedia": None,
    },
    "albert einstein": {
        "wikipedia": "https://en.wikipedia.org/wiki/Albert_Einstein",
        "grokpedia": None,
    },
    "ernest hemingway": {
        "wikipedia": "https://en.wikipedia.org/wiki/Ernest_Hemingway",
        "grokpedia": None,
    },
    "lizzie borden": {
        "wikipedia": "https://en.wikipedia.org/wiki/Lizzie_Borden",
        "grokpedia": "https://grokipedia.com/page/Lizzie_Borden",
    },
    "grigori rasputin": {
        "wikipedia": "https://en.wikipedia.org/wiki/Grigori_Rasputin",
        "grokpedia": "https://grokipedia.com/page/Grigori_Rasputin",
    },
    "josephine baker": {
        "wikipedia": "https://en.wikipedia.org/wiki/Josephine_Baker",
        "grokpedia": None,
    },
}

# Lovecraft characters (from identify_lovecraft_characters.py)
LOVECRAFT_CHARACTERS = {
    "randolph carter": {
        "wikipedia": "https://en.wikipedia.org/wiki/Randolph_Carter",
        "grokpedia": "https://grokipedia.com/page/Randolph_Carter",
    },
    "herbert west": {
        "wikipedia": "https://en.wikipedia.org/wiki/Herbert_West%E2%80%93Reanimator",
        "grokpedia": "https://grokipedia.com/page/Herbert_West",
    },
    "charles dexter ward": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Charles_Dexter_Ward",
    },
    "richard upton pickman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Pickman%27s_Model",
        "grokpedia": "https://grokipedia.com/page/Richard_Upton_Pickman",
    },
    "nathaniel wingate peaslee": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Shadow_Out_of_Time",
        "grokpedia": "https://grokipedia.com/page/Nathaniel_Wingate_Peaslee",
    },
    "wilbur whateley": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Wilbur_Whateley",
    },
    "lavinia whateley": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Lavinia_Whateley",
    },
    "asenath waite": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Thing_on_the_Doorstep",
        "grokpedia": "https://grokipedia.com/page/Asenath_Waite",
    },
    "keziah mason": {
        "wikipedia": "https://en.wikipedia.org/wiki/Dreams_in_the_Witch_House",
        "grokpedia": "https://grokipedia.com/page/Keziah_Mason",
    },
    "edward derby": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Thing_on_the_Doorstep",
        "grokpedia": "https://grokipedia.com/page/Edward_Derby",
    },
    "francis wayland thurston": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/Francis_Wayland_Thurston",
    },
    "henry armitage": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Dunwich_Horror",
        "grokpedia": "https://grokipedia.com/page/Henry_Armitage",
    },
    "walter gilman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Dreams_in_the_Witch_House",
        "grokpedia": "https://grokipedia.com/page/Walter_Gilman",
    },
    "thomas olney": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Strange_High_House_in_the_Mist",
        "grokpedia": "https://grokipedia.com/page/Thomas_Olney",
    },
    "george gammell angell": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Call_of_Cthulhu",
        "grokpedia": "https://grokipedia.com/page/George_Gammell_Angell",
    },
    "carter": {
        "wikipedia": "https://en.wikipedia.org/wiki/Randolph_Carter",
        "grokpedia": "https://grokipedia.com/page/Randolph_Carter",
        "note": "May refer to Randolph Carter",
    },
    "west": {
        "wikipedia": "https://en.wikipedia.org/wiki/Herbert_West%E2%80%93Reanimator",
        "grokpedia": "https://grokipedia.com/page/Herbert_West",
        "note": "May refer to Herbert West",
    },
    "ward": {
        "wikipedia": "https://en.wikipedia.org/wiki/The_Case_of_Charles_Dexter_Ward",
        "grokpedia": "https://grokipedia.com/page/Charles_Dexter_Ward",
        "note": "May refer to Charles Dexter Ward",
    },
    "pickman": {
        "wikipedia": "https://en.wikipedia.org/wiki/Pickman%27s_Model",
        "grokpedia": "https://grokipedia.com/page/Richard_Upton_Pickman",
        "note": "May refer to Richard Upton Pickman",
    },
}


def normalize_name(name: str) -> str:
    """Normalize a name for matching."""
    # Remove common titles and prefixes
    name = re.sub(r"^(lord|lady|sir|dame|dr\.?|doctor|professor|prof\.?|sergeant|sgt\.?|captain|capt\.?|lieutenant|lt\.?)\s+", "", name, flags=re.IGNORECASE)
    # Remove punctuation and extra spaces
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip().lower()


def match_character(name: str, char_id: str) -> Optional[Tuple[str, Dict]]:
    """Try to match a character name against historical/Lovecraft databases."""
    name_norm = normalize_name(name)
    name_lower = name.lower()
    char_id_lower = char_id.lower()
    
    # Direct char_id matches (already handled, but check anyway)
    if char_id_lower in HISTORICAL_FIGURES:
        return (char_id_lower, HISTORICAL_FIGURES[char_id_lower])
    
    # Check historical figures by name
    for hist_name, links in HISTORICAL_FIGURES.items():
        # Exact match
        if hist_name == name_norm or hist_name == char_id_lower:
            return (hist_name, links)
        # Contains match
        if hist_name in name_norm or name_norm in hist_name:
            return (hist_name, links)
        # Check if key parts match (first 2 words)
        hist_parts = hist_name.split()
        name_parts = name_norm.split()
        if len(hist_parts) >= 2 and len(name_parts) >= 2:
            # Check if first two significant words match
            if hist_parts[0] in name_parts and hist_parts[1] in name_parts:
                return (hist_name, links)
        # Check last name match for longer names
        if len(hist_parts) >= 2:
            hist_last = hist_parts[-1]
            if hist_last in name_parts and len(hist_last) > 4:
                return (hist_name, links)
    
    # Check Lovecraft characters
    for lovecraft_name, links in LOVECRAFT_CHARACTERS.items():
        # Exact or contains match
        if lovecraft_name in name_norm or name_norm in lovecraft_name:
            return (lovecraft_name, links)
        # Last name match
        lovecraft_parts = lovecraft_name.split()
        if len(lovecraft_parts) >= 1:
            lovecraft_last = lovecraft_parts[-1]
            if lovecraft_last in name_norm and len(lovecraft_last) > 4:
                return (lovecraft_name, links)
    
    return None


def load_character_links() -> Dict:
    """Load existing character links."""
    if CHARACTER_LINKS_FILE.exists():
        with open(CHARACTER_LINKS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"_comment": "Historical/fictional character links for Wikipedia and Grokpedia"}


def save_character_links(links: Dict) -> bool:
    """Save character links to file."""
    try:
        with open(CHARACTER_LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving character_links.json: {e}")
        return False


def main():
    """Update character_links.json for all characters."""
    print("Updating character_links.json for all characters...")
    print("=" * 60)
    
    # Load existing links
    char_links = load_character_links()
    
    # Find all characters
    all_chars = []
    for root, dirs, files in os.walk(DATA_DIR):
        if "character.json" in files and "characters" in root:
            char_path = Path(root) / "character.json"
            try:
                with open(char_path, encoding="utf-8") as f:
                    data = json.load(f)
                    char_id = data.get("id")
                    name = data.get("name", "").strip()
                    if char_id and name and name != "Unknown":
                        all_chars.append((char_id, name, root))
            except Exception:
                pass
    
    print(f"Found {len(all_chars)} characters\n")
    
    matches_found = []
    matches_updated = []
    
    for char_id, name, char_dir in sorted(all_chars, key=lambda x: x[1].upper()):
        # Skip if already has links
        if char_id.lower() in char_links and char_id != "_comment":
            continue
        
        # Try to match
        match = match_character(name, char_id)
        if match:
            matched_name, link_data = match
            char_links[char_id.lower()] = {
                "wikipedia": link_data.get("wikipedia"),
                "grokpedia": link_data.get("grokpedia"),
                "other": [],
            }
            matches_found.append((char_id, name, matched_name))
            print(f"  ✓ {char_id:20} | {name:40} → {matched_name}")
    
    # Save updated links
    if save_character_links(char_links):
        print("\n" + "=" * 60)
        print(f"✓ Found {len(matches_found)} matches")
        print(f"✓ Updated character_links.json with {len(char_links) - 1} total entries")
    else:
        print("\n✗ Error saving character_links.json")


if __name__ == "__main__":
    main()

