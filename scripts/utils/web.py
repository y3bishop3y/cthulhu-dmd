#!/usr/bin/env python3
"""
Shared web scraping utilities.

This module provides common web scraping functions used across scripts.
"""

import sys
from pathlib import Path
from typing import Final, List, Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: pip install requests beautifulsoup4 lxml\n",
        file=sys.stderr,
    )
    raise

from scripts.models.web_config import get_web_settings

# Load web settings from TOML config
_web_settings = get_web_settings()
DEFAULT_TIMEOUT: Final[int] = _web_settings.http_default_timeout
DEFAULT_USER_AGENT: Final[str] = (
    _web_settings.http_default_user_agent
    if _web_settings.http_default_user_agent
    else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT) -> BeautifulSoup:
    """Fetch HTML content from URL and parse with BeautifulSoup.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        BeautifulSoup object
        
    Raises:
        requests.RequestException: If request fails
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.content, "lxml")


def download_file(
    url: str,
    output_path: Path,
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = 8192,
) -> None:
    """Download a file from URL to local path.
    
    Args:
        url: URL to download
        output_path: Local path to save file
        timeout: Request timeout in seconds
        chunk_size: Chunk size for streaming download
        
    Raises:
        requests.RequestException: If download fails
        OSError: If file cannot be written
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout, stream=True)
    response.raise_for_status()

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download in chunks
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)


def find_links(
    soup: BeautifulSoup,
    pattern: Optional[str] = None,
    link_type: str = "href",
) -> List[Tag]:
    """Find links in HTML that match a pattern.
    
    Args:
        soup: BeautifulSoup object
        pattern: Optional regex pattern to match against link URL
        link_type: Attribute to search ('href' or 'src')
        
    Returns:
        List of matching link tags
    """
    import re

    if link_type == "href":
        links = soup.find_all("a")
    else:
        links = soup.find_all(["img", "link", "script"])

    if pattern:
        regex = re.compile(pattern, re.I)
        links = [
            link
            for link in links
            if regex.search(str(link.get(link_type, "")))
        ]

    return links


def clean_url(url: str, base_url: Optional[str] = None) -> str:
    """Clean and normalize a URL.
    
    Args:
        url: URL to clean
        base_url: Optional base URL for resolving relative URLs
        
    Returns:
        Cleaned absolute URL
    """
    # Remove fragments
    url = url.split("#")[0]

    # Resolve relative URLs
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)

    return url


def extract_text_from_element(element: Tag, join_separator: str = " ") -> str:
    """Extract text from HTML element, handling nested elements.
    
    Args:
        element: BeautifulSoup Tag element
        join_separator: String to join text segments
        
    Returns:
        Extracted text
    """
    return join_separator.join(element.stripped_strings)

