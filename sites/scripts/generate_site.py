#!/usr/bin/env python3
"""
Generate website HTML and JSON data from character data files.

This script reads character JSON files from the data directory and generates:
1. JSON files for seasons and characters
2. HTML pages for seasons and characters
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError:
    print("Error: Missing rich library. Install with: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()

# Constants
DATA_DIR = project_root / "data"
SITES_DIR = project_root / "sites"
SITES_DATA_DIR = SITES_DIR / "data"
SITES_SEASONS_DIR = SITES_DATA_DIR / "seasons"


def load_character_json(char_dir: Path) -> Optional[Dict]:
    """Load character.json from a character directory.
    
    Args:
        char_dir: Path to character directory
        
    Returns:
        Character data dict or None if not found
    """
    char_json = char_dir / "character.json"
    if not char_json.exists():
        return None
    
    try:
        with open(char_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load {char_json}: {e}[/yellow]")
        return None


def get_seasons() -> List[str]:
    """Get list of all season/box directories.
    
    Returns:
        List of directory names (e.g., ['season1', 'season2', 'unknowable-box', etc.])
    """
    if not DATA_DIR.exists():
        return []
    
    seasons = []
    excluded_dirs = {'.git', '__pycache__', '.DS_Store', 'indexes'}
    
    for item in DATA_DIR.iterdir():
        if item.is_dir() and item.name not in excluded_dirs:
            # Check if it contains character subdirectories directly
            has_characters = any(
                subitem.is_dir() and (subitem / "character.json").exists()
                for subitem in item.iterdir()
            )
            # Also check if it has a characters/ subdirectory (new structure)
            characters_dir = item / "characters"
            if characters_dir.exists() and characters_dir.is_dir():
                has_characters = has_characters or any(
                    char_dir.is_dir() and (char_dir / "character.json").exists()
                    for char_dir in characters_dir.iterdir()
                )
            if has_characters:
                seasons.append(item.name)
    
    return sorted(seasons)


def get_characters(season: str) -> List[str]:
    """Get list of character directories for a season.
    
    Args:
        season: Season directory name
        
    Returns:
        List of character directory names
    """
    season_dir = DATA_DIR / season
    if not season_dir.exists():
        return []
    
    characters = []
    # Check for characters/ subdirectory first (new structure)
    characters_dir = season_dir / "characters"
    if characters_dir.exists() and characters_dir.is_dir():
        for item in characters_dir.iterdir():
            if item.is_dir() and (item / "character.json").exists():
                characters.append(item.name)
    else:
        # Fall back to old structure (characters directly in season dir)
        for item in season_dir.iterdir():
            if item.is_dir() and (item / "character.json").exists():
                characters.append(item.name)
    
    return sorted(characters)


def generate_seasons_json() -> Dict:
    """Generate seasons.json with all seasons.
    
    Returns:
        Dict with seasons data
    """
    seasons = get_seasons()
    
    def format_season_name(season_id: str) -> str:
        """Format season ID into display name."""
        # Handle season1, season2, etc.
        if season_id.startswith('season'):
            num = season_id.replace('season', '')
            return f"Season {num}"
        # Handle kebab-case like "unknowable-box"
        return season_id.replace('-', ' ').title()
    
    # Amazon purchase links for seasons
    amazon_links = {
        'season2': 'https://www.amazon.com/Cthulu-Expansion-Mystery-Cooperative-Playtime/dp/B07Z7D443R/ref=sr_1_3?crid=UOJ1O5ZWZ8ZT&dib=eyJ2IjoiMSJ9.fz4MR9Iu7cP5_TLvVAgVs93ACJ45ErzfMjL_dW2-yPJ1-MGQguQjzN32jPYB5GxTPDA0lKX4xyFMcIcQ9wl_QLriD6yr7a-XeAFYGUlOgVU9ZHhJeoQA0YoUgVK2Ct3iN6zTDZFLMdFqS-F_dGjTQT6hbbRJf3Lfm_SqvG4Snf27KsD6FGonEKzzHvSkBdGcP6ljzzueUW2g2TPamLlEFtg_StF_Gn32MhmLhpoqOyMKfAiVSon5dElV0SbHeNGqQKGa8Ijy6EfWZ4eBhVNGxV4xHH9WANtsFRCrhUYlMiE.3Lq-9xGlIfi4yO3vAvOGdnK8RQwPcka2CqsiRNIHxC8&dib_tag=se&keywords=cthulhu+dead+may+die&qid=1763857033&sprefix=chathulu+dead+%2Caps%2C185&sr=8-3&ufe=app_do%3Aamzn1.fos.9fe8cbfa-bf43-43d1-a707-3f4e65a4b666',
        # Add more season links as needed
    }
    
    seasons_data = {
        "seasons": [
            {
                "id": season,
                "name": format_season_name(season),
                "amazon_link": amazon_links.get(season),
            }
            for season in seasons
        ]
    }
    
    return seasons_data


def generate_season_json(season: str) -> Optional[Dict]:
    """Generate JSON file for a specific season with all characters.
    
    Args:
        season: Season directory name
        
    Returns:
        Dict with season data or None if season not found
    """
    season_dir = DATA_DIR / season
    if not season_dir.exists():
        return None
    
    characters = get_characters(season)
    
    def format_season_name(season_id: str) -> str:
        """Format season ID into display name."""
        if season_id.startswith('season'):
            num = season_id.replace('season', '')
            return f"Season {num}"
        return season_id.replace('-', ' ').title()
    
    # Amazon purchase links for seasons
    amazon_links = {
        'season2': 'https://www.amazon.com/Cthulu-Expansion-Mystery-Cooperative-Playtime/dp/B07Z7D443R/ref=sr_1_3?crid=UOJ1O5ZWZ8ZT&dib=eyJ2IjoiMSJ9.fz4MR9Iu7cP5_TLvVAgVs93ACJ45ErzfMjL_dW2-yPJ1-MGQguQjzN32jPYB5GxTPDA0lKX4xyFMcIcQ9wl_QLriD6yr7a-XeAFYGUlOgVU9ZHhJeoQA0YoUgVK2Ct3iN6zTDZFLMdFqS-F_dGjTQT6hbbRJf3Lfm_SqvG4Snf27KsD6FGonEKzzHvSkBdGcP6ljzzueUW2g2TPamLlEFtg_StF_Gn32MhmLhpoqOyMKfAiVSon5dElV0SbHeNGqQKGa8Ijy6EfWZ4eBhVNGxV4xHH9WANtsFRCrhUYlMiE.3Lq-9xGlIfi4yO3vAvOGdnK8RQwPcka2CqsiRNIHxC8&dib_tag=se&keywords=cthulhu+dead+may+die&qid=1763857033&sprefix=chathulu+dead+%2Caps%2C185&sr=8-3&ufe=app_do%3Aamzn1.fos.9fe8cbfa-bf43-43d1-a707-3f4e65a4b666',
        # Add more season links as needed
    }
    
    season_data = {
        "id": season,
        "name": format_season_name(season),
        "amazon_link": amazon_links.get(season),
        "characters": []
    }
    
    for char_id in characters:
        char_dir = season_dir / char_id
        char_data = load_character_json(char_dir)
        
        if char_data:
            # Check for audio file
            audio_file = None
            # Try common audio file patterns
            for audio_file_path in char_dir.glob("*_audio*.wav"):
                audio_file = audio_file_path.name
                break
            
            # Get common powers
            common_powers = char_data.get("common_powers", [])
            
            character_info = {
                "id": char_id,
                "name": char_data.get("name", "Unknown"),
                "motto": char_data.get("motto"),
                "location": char_data.get("location"),
                "common_powers": common_powers if isinstance(common_powers, list) else [],
                "has_audio": audio_file is not None,
            }
            season_data["characters"].append(character_info)
    
    return season_data


def generate_all() -> None:
    """Generate all website data files."""
    console.print("[bold cyan]Generating website data files...[/bold cyan]")
    
    # Create output directories
    SITES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITES_SEASONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate seasons.json
    console.print("\n[cyan]Generating seasons.json...[/cyan]")
    seasons_data = generate_seasons_json()
    seasons_json_path = SITES_DATA_DIR / "seasons.json"
    with open(seasons_json_path, 'w', encoding='utf-8') as f:
        json.dump(seasons_data, f, indent=2, ensure_ascii=False)
    console.print(f"[green]✓ Generated {seasons_json_path}[/green]")
    console.print(f"  Found {len(seasons_data['seasons'])} seasons")
    
    # Generate season JSON files
    console.print("\n[cyan]Generating season JSON files...[/cyan]")
    seasons = get_seasons()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing seasons...", total=len(seasons))
        
        for season in seasons:
            progress.update(task, description=f"Processing {season}...")
            
            season_data = generate_season_json(season)
            if season_data:
                season_json_path = SITES_SEASONS_DIR / f"{season}.json"
                with open(season_json_path, 'w', encoding='utf-8') as f:
                    json.dump(season_data, f, indent=2, ensure_ascii=False)
                console.print(f"  [green]✓[/green] {season}: {len(season_data['characters'])} characters")
            
            progress.update(task, advance=1)
    
    console.print("\n[green]✓ Website data generation complete![/green]")
    console.print(f"[dim]Output directory: {SITES_DATA_DIR}[/dim]")


if __name__ == "__main__":
    generate_all()

