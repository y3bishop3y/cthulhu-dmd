#!/usr/bin/env python3
"""
Download Death May Die character card images from makecraftgame.com
Organizes images by season/box and character name.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple
from urllib.parse import urljoin

try:
    import click
    import requests
    from bs4 import BeautifulSoup, Tag
    from pydantic import BaseModel, Field
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.table import Table
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/download_characters.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/download_characters.py [options]\n"
        "  3. make setup (to install dependencies) then run directly\n\n"
        "Recommended: uv run ./scripts/download_characters.py --help\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# URL Constants
BASE_URL: Final[str] = "https://makecraftgame.com/2022/10/21/dmd-character-guide/"
UPLOAD_PATH_PATTERN: Final[str] = "wp-content/uploads/"
WP_CONTENT_KEYWORD: Final[str] = "wp-content"

# Regex Patterns
REGEX_NON_WORD_CHARS: Final[str] = r"[^\w\s-]"
REGEX_MULTIPLE_HYPHENS: Final[str] = r"[-\s]+"
REGEX_CAROUSEL_LINK: Final[str] = r"jp-carousel-\d+"
REGEX_CAROUSEL_ID: Final[str] = r"jp-carousel-(\d+)"
REGEX_CONTENT_CLASSES: Final[str] = r"entry-content|post-content|content"
REGEX_CHARACTER_IMAGE_PATH: Final[str] = r"wp-content/uploads/\d{4}/\d{2}/\d+[-.]"
REGEX_CHARACTER_IMAGE_URL: Final[str] = r".*wp-content/uploads/\d{4}/\d{2}/\d+[-.].*"
REGEX_IMAGE_SIZE_SUFFIX: Final[str] = r"-\d+x\d+"
REGEX_CHARACTER_FILENAME: Final[str] = r"(\d+)(?:\.1)?-([A-Z][A-Za-z-]+)"
REGEX_CHARACTER_KEYWORDS: Final[str] = r"(character|dmd|death)"

# HTML Tag Names
TAG_HEADING_LEVELS: Final[Tuple[str, ...]] = ("h2", "h3", "h4")
TAG_CONTENT_CONTAINERS: Final[Tuple[str, ...]] = ("div", "main", "article")
TAG_IMAGE: Final[str] = "img"
TAG_LINK: Final[str] = "a"
TAG_BOLD: Final[Tuple[str, ...]] = ("strong", "b")
TAG_TEXT_CONTAINERS: Final[Tuple[str, ...]] = ("p", "li")

# File Naming Constants
FILENAME_FRONT: Final[str] = "front.jpg"
FILENAME_BACK: Final[str] = "back.jpg"
FILENAME_CHARACTER_BOOK: Final[str] = "character-book.pdf"
FILENAME_CHARACTER_JSON: Final[str] = "character.json"
FILENAME_STORY_TXT: Final[str] = "story.txt"
BACK_CARD_SUFFIX: Final[str] = ".1"
QUERY_PARAM_SEPARATOR: Final[str] = "?"
PATH_SEPARATOR: Final[str] = "/"
HYPHEN: Final[str] = "-"
SPACE: Final[str] = " "

# Image Size Patterns to Remove
IMAGE_SIZE_150: Final[str] = "-150x"
IMAGE_SIZE_300: Final[str] = "-300x"
IMAGE_SIZE_768: Final[str] = "-768x"
IMAGE_SIZE_1024: Final[str] = "-1024x"

# Search Keywords
KEYWORD_CHARACTER: Final[str] = "character"
KEYWORD_DMD: Final[str] = "dmd"
KEYWORD_DEATH: Final[str] = "death"

# Numeric Constants
HTTP_TIMEOUT_SECONDS: Final[int] = 30
DOWNLOAD_CHUNK_SIZE: Final[int] = 8192
MAX_PARENT_LEVELS: Final[int] = 5
MAX_SIBLINGS_TO_CHECK: Final[int] = 50
MIN_CHAR_NAME_LENGTH: Final[int] = 2
MAX_CHAR_NAME_LENGTH: Final[int] = 30
MAX_IMAGES_PER_CHARACTER: Final[int] = 2
MAX_CHARS_TO_DISPLAY: Final[int] = 5


# Pydantic Models
class CharacterImage(BaseModel):
    """Represents front and back images for a character."""

    front: Optional[str] = None
    back: Optional[str] = None

    def get_image_urls(self) -> List[str]:
        """Get list of image URLs, front first."""
        urls = []
        if self.front:
            urls.append(self.front)
        if self.back:
            urls.append(self.back)
        return urls


class Character(BaseModel):
    """Represents a character with their images and metadata."""

    name: str
    images: CharacterImage
    heading: Optional[Tag] = Field(default=None, exclude=True)  # Exclude from serialization
    story: Optional[str] = None  # Story text extracted from HTML

    model_config = {"arbitrary_types_allowed": True}


class CharactersBySeason(BaseModel):
    """Container for characters organized by season/box."""

    characters: Dict[str, List[Character]] = Field(default_factory=dict)

    def add_character(self, season: str, character: Character) -> None:
        """Add a character to the specified season."""
        if season not in self.characters:
            self.characters[season] = []
        self.characters[season].append(character)

    def has_character(self, name: str) -> bool:
        """Check if a character with the given name exists."""
        for chars in self.characters.values():
            if any(c.name.lower() == name.lower() for c in chars):
                return True
        return False

    def get_total_count(self) -> int:
        """Get total number of characters across all seasons."""
        return sum(len(chars) for chars in self.characters.values())


# CSS Class Patterns
CLASS_ENTRY_CONTENT: Final[str] = "entry-content"
CLASS_POST_CONTENT: Final[str] = "post-content"
CLASS_CONTENT: Final[str] = "content"

# File Extensions
EXT_JPG: Final[str] = ".jpg"
EXT_PDF: Final[str] = ".pdf"

# Season/Box mappings based on the website structure
SEASON_MAPPINGS: Final[Dict[str, str]] = {
    "Base Box": "season1",
    "Season 2": "season2",
    "Season 3": "season3",
    "Fear of the Unknown": "season3",
    "Season 4": "season4",
    "Extra Promo": "extra-promos",
    "Extra Promos": "extra-promos",
    "Unspeakable Box": "unspeakable-box",
    "Unknowable Box": "unknowable-box",
    "Comic Book Extra": "comic-book-extras",
    "Comic Book Extras": "comic-book-extras",
    "Comic Book Vol. 2": "comic-book-v2",
    "Comic Book Volume 2": "comic-book-v2",
}

# Additional URLs for different seasons
SEASON_URLS: Final[Dict[str, str]] = {
    "season1": "https://makecraftgame.com/2022/10/21/dmd-character-guide/",
    "season2": "https://makecraftgame.com/2022/10/21/dmd-character-guide/",
    "season3": "https://makecraftgame.com/2025/01/17/dmd-fear-of-the-unknown/",
    "season4": "https://makecraftgame.com/2025/01/17/dmd-season-4/",
    "comic-book-v2": "https://makecraftgame.com/2025/01/17/dmd-comic-book-v2/",
    "unknowable-box": "https://makecraftgame.com/2025/01/17/dmd-unknowable-box/",
}

# PDF URLs for character booklets by season/box
SEASON_PDF_URLS: Final[Dict[str, str]] = {
    "season3": "https://makecraftgame.com/wp-content/uploads/2025/01/Chthulu-Death-May-Die-Character-Book-Fear-of-the-Unknown.pdf",
    "season4": "https://makecraftgame.com/wp-content/uploads/2025/01/Chthulu-Death-May-Die-Character-Book-Unknowable-Box.pdf",
    "unknowable-box": "https://makecraftgame.com/wp-content/uploads/2025/01/Chthulu-Death-May-Die-Character-Book-Unknowable-Box.pdf",
}


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(REGEX_NON_WORD_CHARS, "", text)
    text = re.sub(REGEX_MULTIPLE_HYPHENS, HYPHEN, text)
    return text.strip(HYPHEN)


def get_page_content(url: str) -> Optional[BeautifulSoup]:
    """Fetch and parse the webpage."""
    try:
        console.print(f"[cyan]Fetching[/cyan] {url}")
        response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        return BeautifulSoup(response.content, "lxml")
    except Exception as e:
        console.print(f"[red]Error fetching page:[/red] {e}")
        return None


def find_content_section(soup: BeautifulSoup) -> Tag:
    """Find the main content section of the page."""
    # Try to find entry-content div specifically (most reliable)
    content = soup.find("div", class_=re.compile(r"entry-content"))
    if not content:
        # Fallback to other content containers
        content = soup.find(TAG_CONTENT_CONTAINERS[0], class_=re.compile(REGEX_CONTENT_CLASSES))
    if not content:
        content = soup.find(TAG_CONTENT_CONTAINERS[1]) or soup.find(TAG_CONTENT_CONTAINERS[2])
    if not content or not isinstance(content, Tag):
        content = soup
    assert isinstance(content, Tag), "Content must be a Tag"
    return content


def clean_image_url(url: str) -> str:
    """Remove query parameters and image size suffixes from URL."""
    url = url.split(QUERY_PARAM_SEPARATOR)[0]
    url = re.sub(REGEX_IMAGE_SIZE_SUFFIX, "", url)
    url = (
        url.replace(IMAGE_SIZE_150, "")
        .replace(IMAGE_SIZE_300, "")
        .replace(IMAGE_SIZE_768, "")
        .replace(IMAGE_SIZE_1024, "")
    )
    return url


def extract_character_name_from_filename(filename: str) -> Optional[str]:
    """Extract character name from image filename."""
    match = re.match(REGEX_CHARACTER_FILENAME, filename)
    if match:
        _, char_name = match.groups()
        return char_name.replace(HYPHEN, SPACE)
    return None


def parse_character_image(img_tag: Tag) -> Optional[Tuple[str, bool]]:
    """Parse character image tag and return (character_name, is_back)."""
    src_attr = img_tag.get("src", "")
    # Handle case where get() might return a list
    if isinstance(src_attr, list):
        src = src_attr[0] if src_attr else ""
    else:
        src = src_attr if src_attr else ""

    if not src or not isinstance(src, str):
        return None

    full_src = clean_image_url(src)
    filename = full_src.split(PATH_SEPARATOR)[-1]
    char_name = extract_character_name_from_filename(filename)

    if char_name:
        is_back = BACK_CARD_SUFFIX in filename
        return (char_name, is_back)

    return None


def group_images_by_character(content: Tag) -> Dict[str, CharacterImage]:
    """Extract and group all character images from content."""
    char_images: Dict[str, CharacterImage] = {}
    all_imgs = content.find_all(TAG_IMAGE, src=re.compile(REGEX_CHARACTER_IMAGE_URL))

    for img in all_imgs:
        result = parse_character_image(img)
        if result:
            char_name, is_back = result
            src_attr = img.get("src", "")
            # Handle case where get() might return a list
            if isinstance(src_attr, list):
                src_str = src_attr[0] if src_attr else ""
            else:
                src_str = src_attr if src_attr else ""

            if isinstance(src_str, str):
                src = clean_image_url(src_str)

                if char_name not in char_images:
                    char_images[char_name] = CharacterImage()

                if is_back:
                    char_images[char_name].back = src
                else:
                    char_images[char_name].front = src

    return char_images


def find_season_for_heading(heading_text: str) -> Optional[str]:
    """Determine which season/box a heading belongs to."""
    for key, folder in SEASON_MAPPINGS.items():
        if key.lower() in heading_text.lower():
            return folder
    return None


def extract_story_text_for_character(char_name: str, content: Tag) -> Optional[str]:
    """Extract story text for a character from HTML content."""
    # Look for the character's name in headings, bold text, or strong tags
    char_name_variations = [
        char_name,
        char_name.replace(SPACE, HYPHEN),
        char_name.replace(SPACE, ""),
        char_name.replace("-", " "),  # Handle hyphenated names
    ]

    for variation in char_name_variations:
        # Try to find heading with character name first
        name_heading = None
        for tag_name in TAG_HEADING_LEVELS:
            headings = content.find_all(tag_name)
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                # More flexible matching - check if variation is in heading or vice versa
                heading_lower = heading_text.lower()
                variation_lower = variation.lower()
                if (
                    variation_lower in heading_lower
                    or heading_lower == variation_lower
                    or heading_lower.startswith(variation_lower)
                ):
                    name_heading = heading
                    break
            if name_heading:
                break

        # Also try to find character name in bold/strong tags near images
        if not name_heading:
            # Look for bold/strong tags containing the character name
            for bold_tag in content.find_all(["b", "strong"]):
                bold_text = bold_tag.get_text(strip=True)
                if variation.lower() in bold_text.lower() or bold_text.lower() == variation.lower():
                    # Check if there's an image nearby (within same parent or next siblings)
                    parent = bold_tag.parent if bold_tag.parent else None
                    if parent:
                        # Look for images in the same parent or nearby
                        nearby_imgs = parent.find_all(TAG_IMAGE)
                        if nearby_imgs:
                            # Found character name in bold near images, use parent as starting point
                            name_heading = parent
                            break

        # If we found a heading or parent element, get text from following siblings
        if name_heading:
            story_paragraphs = []
            # Start from the next sibling of the heading/parent
            current = name_heading.find_next_sibling()

            # Collect paragraphs until we hit another character heading or section
            for _ in range(20):  # Increased limit for better extraction
                if current is None:
                    break

                # Stop if we hit another character heading
                if current.name in TAG_HEADING_LEVELS:
                    heading_text = current.get_text(strip=True)
                    # Check if this is another character name (short, capitalized, not a section header)
                    if (
                        len(heading_text) < 50
                        and heading_text[0].isupper()
                        and heading_text.lower() != variation.lower()
                        and not any(
                            section in heading_text.lower()
                            for section in ["common", "trait", "season", "box", "characters", "set"]
                        )
                    ):
                        break

                # Collect paragraph text
                if current.name == "p":
                    text = current.get_text(strip=True)
                    # Skip very short text, navigation, or metadata
                    if (
                        len(text) > 30  # Lowered threshold to catch shorter stories
                        and not text.startswith("Share")
                        and "Jump To" not in text
                        and "Toggle" not in text
                        and not text.startswith("Check out")
                        and "Click to" not in text.lower()
                        and not text.lower().startswith("download")
                    ):
                        story_paragraphs.append(text)

                # Also check divs that might contain story text
                elif current.name == "div":
                    div_text = current.get_text(strip=True)
                    # If div contains substantial text and no images, it might be story text
                    if (
                        len(div_text) > 50
                        and not current.find_all(TAG_IMAGE)
                        and not any(
                            skip in div_text.lower()
                            for skip in ["share", "jump", "toggle", "check out", "click"]
                        )
                    ):
                        # Check if it's a paragraph-like div
                        if not current.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                            story_paragraphs.append(div_text)

                current = (
                    current.find_next_sibling() if hasattr(current, "find_next_sibling") else None
                )

            if story_paragraphs:
                # Join paragraphs and clean up
                story = " ".join(story_paragraphs)
                # Remove extra whitespace
                story = re.sub(r"\s+", " ", story).strip()
                # Remove common prefixes/suffixes that aren't part of the story
                story = re.sub(r"^(Share|Jump|Toggle|Check out).*?\.\s*", "", story, flags=re.I)
                return story if len(story) > 30 else None

    return None


def find_characters_in_section(
    heading: Tag,
    char_images: Dict[str, CharacterImage],
    seen_chars: set,
    content: Tag,
    max_siblings: int = MAX_SIBLINGS_TO_CHECK,
) -> List[Character]:
    """Find characters in the section following a heading."""
    characters = []
    next_elem = heading.find_next_sibling()

    for _ in range(max_siblings):
        if next_elem is None:
            break

        # Check for images in this element
        imgs = next_elem.find_all(TAG_IMAGE) if hasattr(next_elem, "find_all") else []
        for img in imgs:
            result = parse_character_image(img)
            if result:
                char_name, _ = result
                if char_name in char_images and char_name not in seen_chars:
                    seen_chars.add(char_name)
                    # Try to extract story text from HTML
                    story = extract_story_text_for_character(char_name, content)
                    character = Character(
                        name=char_name,
                        images=char_images[char_name],
                        heading=heading,
                        story=story,
                    )
                    characters.append(character)

        # Stop if we hit the next section heading
        if next_elem.name in TAG_HEADING_LEVELS[:2]:
            next_text = next_elem.get_text(strip=True)
            if find_season_for_heading(next_text):
                break

        next_elem = next_elem.find_next_sibling()

    return characters


def match_remaining_characters_to_seasons(
    content: Tag,
    char_images: Dict[str, CharacterImage],
    characters_by_season: CharactersBySeason,
) -> None:
    """Match remaining characters to seasons by searching HTML content."""
    for char_name, img_data in char_images.items():
        if characters_by_season.has_character(char_name):
            continue

        # Try to find which section this character belongs to
        char_name_variations = [
            char_name,
            char_name.replace(SPACE, HYPHEN),
            char_name.replace(SPACE, ""),
        ]

        for variation in char_name_variations:
            name_elem = content.find(string=re.compile(variation, re.I))
            if name_elem:
                prev_heading = name_elem.find_previous(list(TAG_HEADING_LEVELS[:2]))
                if prev_heading:
                    prev_text = prev_heading.get_text(strip=True)
                    season = find_season_for_heading(prev_text)
                    if season:
                        # Try to extract story
                        story = extract_story_text_for_character(char_name, content)
                        character = Character(
                            name=char_name, images=img_data, heading=None, story=story
                        )
                        characters_by_season.add_character(season, character)
                        break


def extract_characters_from_page(soup: BeautifulSoup) -> CharactersBySeason:
    """Extract all characters and their images from the page."""
    characters_by_season = CharactersBySeason()
    content = find_content_section(soup)

    # Group all character images by name
    char_images = group_images_by_character(content)

    # Find headings and match characters to seasons
    headings = content.find_all(list(TAG_HEADING_LEVELS[:2]))
    seen_chars: set = set()

    for heading in headings:
        heading_text = heading.get_text(strip=True)
        season = find_season_for_heading(heading_text)

        if season:
            console.print(f"[green]Found section:[/green] {heading_text} -> {season}")
            # Find characters in this section
            section_chars = find_characters_in_section(heading, char_images, seen_chars, content)
            for char in section_chars:
                characters_by_season.add_character(season, char)

    # Match any remaining characters to seasons
    match_remaining_characters_to_seasons(content, char_images, characters_by_season)

    # Try to extract stories for characters that don't have them yet
    for chars in characters_by_season.characters.values():
        for char in chars:
            if not char.story:
                story = extract_story_text_for_character(char.name, content)
                if story:
                    char.story = story

    return characters_by_season


def download_image(url: str, filepath: Path) -> bool:
    """Download an image from URL to filepath."""
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS, stream=True)
        response.raise_for_status()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)

        return True
    except Exception as e:
        console.print(f"[red]Error downloading {url}:[/red] {e}")
        return False


def find_pdf_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Find PDF links on the page, prioritizing character book PDFs."""
    pdf_urls: List[str] = []

    # Look for links with PDF extension
    pdf_links = soup.find_all(TAG_LINK, href=re.compile(r"\.pdf", re.I))

    for link in pdf_links:
        href_attr = link.get("href", "")
        if isinstance(href_attr, list):
            href = href_attr[0] if href_attr else ""
        else:
            href = href_attr if href_attr else ""

        if not isinstance(href, str):
            continue

        # Convert relative URLs to absolute
        if href.startswith("/"):
            # Relative to domain root
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
        elif href.startswith("http"):
            # Already absolute
            full_url = href
        else:
            # Relative to current page
            full_url = urljoin(base_url, href)

        # Prioritize character book PDFs
        href_lower = href.lower()
        if any(keyword in href_lower for keyword in ["character", "book", "booklet", "dmd"]):
            pdf_urls.insert(0, full_url)  # Add to front
        else:
            pdf_urls.append(full_url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in pdf_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def download_pdf(url: str, filepath: Path) -> bool:
    """Download a PDF from URL to filepath."""
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS, stream=True)
        response.raise_for_status()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)

        return True
    except Exception as e:
        console.print(f"[red]Error downloading PDF {url}:[/red] {e}")
        return False


def update_character_json(char_path: Path, character_name: str, story: Optional[str]) -> None:
    """Create or update character.json with name and story from HTML extraction."""
    json_filepath = char_path / FILENAME_CHARACTER_JSON

    # Load existing JSON if it exists, otherwise create new structure
    existing_data: Dict[str, Any] = {}
    if json_filepath.exists():
        try:
            existing_data = json.loads(json_filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception) as e:
            console.print(
                f"[yellow]Warning: Could not parse existing {FILENAME_CHARACTER_JSON} for {character_name}: {e}[/yellow]"
            )
            existing_data = {}

    # Update with HTML-extracted data (only if not already present or different)
    updated = False

    # Update name (always use the one from HTML as it's more reliable)
    if existing_data.get("name") != character_name:
        existing_data["name"] = character_name
        updated = True

    # Update story (only if we have one from HTML and it's different)
    if story and existing_data.get("story") != story:
        existing_data["story"] = story
        updated = True

    # Ensure structure matches CharacterData model from parse_characters.py
    if "location" not in existing_data:
        existing_data["location"] = None
    if "motto" not in existing_data:
        existing_data["motto"] = None
    if "special_power" not in existing_data:
        existing_data["special_power"] = None
    if "common_powers" not in existing_data:
        existing_data["common_powers"] = []

    # Write updated JSON
    if updated or not json_filepath.exists():
        json_filepath.parent.mkdir(parents=True, exist_ok=True)
        json_filepath.write_text(
            json.dumps(existing_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


@click.command()
@click.option("--data-dir", default="data", help="Directory to save character images")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading",
)
@click.option(
    "--season",
    type=click.Choice(
        [
            "all",
            "season1",
            "season2",
            "season3",
            "season4",
            "comic-book-v2",
            "unknowable-box",
        ],
        case_sensitive=False,
    ),
    default="all",
    help="Which season(s) to download (default: all)",
)
def main(data_dir: str, dry_run: bool, season: str):
    """Download Death May Die character card images from makecraftgame.com"""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Character Image Downloader[/bold cyan]\n"
            "Downloads character card images from makecraftgame.com",
            border_style="cyan",
        )
    )

    data_path = Path(data_dir)

    # Determine which URLs to fetch
    urls_to_fetch: List[Tuple[str, str]] = []  # (season_key, url)
    if season.lower() == "all":
        # Fetch all seasons
        for season_key, url in SEASON_URLS.items():
            urls_to_fetch.append((season_key, url))
    else:
        # Fetch specific season
        season_lower = season.lower()
        if season_lower in SEASON_URLS:
            urls_to_fetch.append((season_lower, SEASON_URLS[season_lower]))
        else:
            console.print(f"[red]Unknown season: {season}[/red]")
            sys.exit(1)

    # Fetch pages and extract characters
    all_characters_by_season = CharactersBySeason()
    discovered_pdfs: Dict[str, List[str]] = {}  # season -> list of PDF URLs

    for season_key, url in urls_to_fetch:
        console.print(f"\n[cyan]Fetching {season_key} from {url}[/cyan]")
        soup = get_page_content(url)
        if not soup:
            console.print(f"[yellow]Failed to fetch {season_key}, skipping...[/yellow]")
            continue

        # Discover PDF links on the page
        pdf_links = find_pdf_links(soup, url)
        if pdf_links:
            console.print(f"[green]Found {len(pdf_links)} PDF link(s) on {season_key} page[/green]")
            # Map to the actual season folder name
            for season_name in SEASON_MAPPINGS.values():
                if season_key == season_name or (
                    season_key in SEASON_URLS
                    and SEASON_URLS[season_key] == url
                ):
                    if season_name not in discovered_pdfs:
                        discovered_pdfs[season_name] = []
                    discovered_pdfs[season_name].extend(pdf_links)

        # Extract characters
        console.print(f"[cyan]Extracting character information from {season_key}...[/cyan]")
        characters_by_season = extract_characters_from_page(soup)

        if not characters_by_season:
            console.print(
                f"[yellow]No characters found in {season_key}. Trying alternative extraction method...[/yellow]"
            )
            # Fallback: look for all images with character-related keywords
            all_imgs = soup.find_all(TAG_IMAGE, src=re.compile(REGEX_CHARACTER_KEYWORDS, re.I))
            console.print(f"Found {len(all_imgs)} potential character images")
            # We'll need a different strategy here

        # Merge into combined structure
        for season_name, chars in characters_by_season.characters.items():
            for char in chars:
                all_characters_by_season.add_character(season_name, char)

    # Display summary
    total_chars = all_characters_by_season.get_total_count()
    console.print(
        f"\n[green]Found {total_chars} characters across {len(all_characters_by_season.characters)} seasons/boxes[/green]\n"
    )

    # Show table of characters
    table = Table(title="Characters by Season/Box")
    table.add_column("Season/Box", style="cyan")
    table.add_column("Character Count", style="magenta")
    table.add_column("Characters", style="white")

    for season, chars in all_characters_by_season.characters.items():
        char_names = ", ".join([c.name for c in chars[:MAX_CHARS_TO_DISPLAY]])
        if len(chars) > MAX_CHARS_TO_DISPLAY:
            char_names += f" ... and {len(chars) - MAX_CHARS_TO_DISPLAY} more"
        table.add_row(season, str(len(chars)), char_names)

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run mode - no files will be downloaded[/yellow]")
        return

    # Download PDFs for seasons that have them
    console.print("\n[cyan]Downloading character book PDFs...[/cyan]\n")
    pdf_downloaded = 0
    pdf_failed = 0

    # Combine discovered PDFs with hardcoded ones (hardcoded take precedence)
    all_pdf_urls: Dict[str, str] = {}

    # First, add discovered PDFs
    for season, pdf_list in discovered_pdfs.items():
        if pdf_list:
            # Use the first PDF found (prioritized by find_pdf_links)
            all_pdf_urls[season] = pdf_list[0]

    # Then, override with hardcoded PDFs if they exist
    for season, hardcoded_pdf_url in SEASON_PDF_URLS.items():
        all_pdf_urls[season] = hardcoded_pdf_url

    for season in all_characters_by_season.characters.keys():
        # Check both discovered and hardcoded PDFs
        pdf_url_to_download: Optional[str] = all_pdf_urls.get(season)

        if not pdf_url_to_download:
            continue

        season_path = data_path / season
        pdf_filepath = season_path / FILENAME_CHARACTER_BOOK

        # Skip if PDF already exists
        if pdf_filepath.exists():
            console.print(
                f"[yellow]Skipping PDF for {season} (already exists)[/yellow]"
            )
            continue

        console.print(f"[cyan]Downloading PDF for {season}...[/cyan]")
        if download_pdf(pdf_url_to_download, pdf_filepath):
            pdf_downloaded += 1
            console.print(f"[green]✓ Downloaded PDF for {season}[/green]")
        else:
            pdf_failed += 1
            console.print(f"[red]✗ Failed to download PDF for {season}[/red]")

    if pdf_downloaded > 0 or pdf_failed > 0:
        console.print(
            f"\n[green]✓ Downloaded:[/green] {pdf_downloaded} PDFs"
            + (f"\n[red]✗ Failed:[/red] {pdf_failed} PDFs" if pdf_failed > 0 else "")
        )

    # Download images
    console.print("\n[cyan]Downloading images...[/cyan]\n")

    downloaded = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        for season, characters in all_characters_by_season.characters.items():
            season_path = data_path / season

            for character in characters:
                char_slug = slugify(character.name)
                char_path = season_path / char_slug
                image_urls = character.images.get_image_urls()

                task = progress.add_task(
                    f"[cyan]{season}[/cyan] - {character.name}",
                    total=len(image_urls) or MAX_IMAGES_PER_CHARACTER,
                )

                # Download images
                if image_urls:
                    for i, img_url in enumerate(image_urls[:MAX_IMAGES_PER_CHARACTER]):
                        # Determine if front or back
                        if i == 0:
                            filename = FILENAME_FRONT
                        else:
                            filename = FILENAME_BACK

                        filepath = char_path / filename

                        # Skip if image already exists
                        if filepath.exists():
                            console.print(
                                f"[yellow]  Skipping {filename} for {character.name} (already exists)[/yellow]"
                            )
                            progress.update(task, advance=1)
                            continue

                        # Find the base URL for this character's season
                        base_url_for_season = BASE_URL
                        for season_key, url in SEASON_URLS.items():
                            if season == SEASON_MAPPINGS.get(season_key, ""):
                                base_url_for_season = url
                                break
                        full_url = urljoin(base_url_for_season, img_url)

                        if download_image(full_url, filepath):
                            downloaded += 1
                            progress.update(task, advance=1)
                        else:
                            failed += 1
                            progress.update(task, advance=1)

                    # Save story text if available
                    if character.story:
                        story_file = char_path / FILENAME_STORY_TXT
                        existing_story = None
                        if story_file.exists():
                            existing_story = story_file.read_text(encoding="utf-8").strip()

                        # Only write if story is different or doesn't exist
                        if existing_story != character.story:
                            story_file.write_text(character.story, encoding="utf-8")
                            console.print(f"[green]  Saved story for {character.name}[/green]")
                        else:
                            console.print(
                                f"[yellow]  Story for {character.name} already exists and matches[/yellow]"
                            )

                    # Always update character.json with name and story from HTML
                    update_character_json(char_path, character.name, character.story)
                else:
                    console.print(f"[yellow]No images found for {character.name}[/yellow]")
                    progress.update(task, advance=MAX_IMAGES_PER_CHARACTER)

    # Summary
    console.print(f"\n[green]✓ Downloaded:[/green] {downloaded} images")
    if failed > 0:
        console.print(f"[red]✗ Failed:[/red] {failed} images")
    console.print(f"\n[cyan]Images saved to:[/cyan] {data_path.absolute()}")


if __name__ == "__main__":
    main()
