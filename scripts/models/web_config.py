#!/usr/bin/env python3
"""
Pydantic Settings models for web scraping configuration.

Loads HTML tags, CSS classes, season mappings, and other web scraping
settings from TOML files.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\nInstall with: uv add pydantic-settings\n",
        file=sys.stderr,
    )
    raise

# Paths to config files
WEB_SCRAPING_CONFIG_FILE: Path = Path(__file__).parent.parent / "data" / "web_scraping_config.toml"
WEB_SETTINGS_FILE: Path = Path(__file__).parent.parent / "data" / "web_settings.toml"


class WebScrapingConfig(BaseSettings):
    """Web scraping configuration loaded from TOML file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # HTML tags
    html_tags_heading_levels: List[str] = Field(default_factory=list)
    html_tags_content_containers: List[str] = Field(default_factory=list)
    html_tags_image: Optional[str] = None
    html_tags_link: Optional[str] = None
    html_tags_bold: List[str] = Field(default_factory=list)
    html_tags_text_containers: List[str] = Field(default_factory=list)

    # CSS classes
    css_classes_entry_content: Optional[str] = None
    css_classes_post_content: Optional[str] = None
    css_classes_content: Optional[str] = None

    # File patterns
    file_patterns_back_image: List[str] = Field(default_factory=list)
    file_patterns_image_extensions: List[str] = Field(default_factory=list)
    file_patterns_pdf_extension: Optional[str] = None

    # Image sizes
    image_sizes_sizes: List[str] = Field(default_factory=list)

    # Search keywords
    search_keywords_character: Optional[str] = None
    search_keywords_dmd: Optional[str] = None
    search_keywords_death: Optional[str] = None

    # Season mappings
    season_mappings: Dict[str, str] = Field(default_factory=dict)

    # Limits
    limits_max_parent_levels: int = 5
    limits_max_siblings_to_check: int = 50
    limits_min_char_name_length: int = 2
    limits_max_char_name_length: int = 30
    limits_max_images_per_character: int = 2
    limits_max_chars_to_display: int = 5

    # Constants
    constants_query_param_separator: Optional[str] = None
    constants_path_separator: Optional[str] = None
    constants_hyphen: Optional[str] = None
    constants_space: Optional[str] = None
    constants_back_card_suffix: Optional[str] = None

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "WebScrapingConfig":
        """Load web scraping config from TOML file."""
        if file_path is None:
            file_path = WEB_SCRAPING_CONFIG_FILE

        if not file_path.exists():
            return cls()

        try:
            # Try using tomllib (Python 3.11+)
            try:
                import tomllib

                with open(file_path, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                # Fallback to tomli for older Python versions
                try:
                    import toml  # type: ignore[import-untyped]i

                    with open(file_path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    # Fallback to toml (pypi package)
                    import toml  # type: ignore[import-untyped]

                    with open(file_path, encoding="utf-8") as f:
                        data = toml.load(f)

            # Flatten nested structure
            config_data = {}

            # HTML tags
            html_tags = data.get("html_tags", {})
            config_data["html_tags_heading_levels"] = html_tags.get("heading_levels", [])
            config_data["html_tags_content_containers"] = html_tags.get("content_containers", [])
            config_data["html_tags_image"] = html_tags.get("image")
            config_data["html_tags_link"] = html_tags.get("link")
            config_data["html_tags_bold"] = html_tags.get("bold", [])
            config_data["html_tags_text_containers"] = html_tags.get("text_containers", [])

            # CSS classes
            css_classes = data.get("css_classes", {})
            config_data["css_classes_entry_content"] = css_classes.get("entry_content")
            config_data["css_classes_post_content"] = css_classes.get("post_content")
            config_data["css_classes_content"] = css_classes.get("content")

            # File patterns
            file_patterns = data.get("file_patterns", {})
            config_data["file_patterns_back_image"] = file_patterns.get("back_image", [])
            config_data["file_patterns_image_extensions"] = file_patterns.get(
                "image_extensions", []
            )
            config_data["file_patterns_pdf_extension"] = file_patterns.get("pdf_extension")

            # Image sizes
            image_sizes = data.get("image_sizes", {})
            config_data["image_sizes_sizes"] = image_sizes.get("sizes", [])

            # Search keywords
            search_keywords = data.get("search_keywords", {})
            config_data["search_keywords_character"] = search_keywords.get("character")
            config_data["search_keywords_dmd"] = search_keywords.get("dmd")
            config_data["search_keywords_death"] = search_keywords.get("death")

            # Season mappings
            config_data["season_mappings"] = data.get("season_mappings", {})

            # Limits
            limits = data.get("limits", {})
            config_data["limits_max_parent_levels"] = limits.get("max_parent_levels", 5)
            config_data["limits_max_siblings_to_check"] = limits.get("max_siblings_to_check", 50)
            config_data["limits_min_char_name_length"] = limits.get("min_char_name_length", 2)
            config_data["limits_max_char_name_length"] = limits.get("max_char_name_length", 30)
            config_data["limits_max_images_per_character"] = limits.get(
                "max_images_per_character", 2
            )
            config_data["limits_max_chars_to_display"] = limits.get("max_chars_to_display", 5)

            # Constants
            constants = data.get("constants", {})
            config_data["constants_query_param_separator"] = constants.get("query_param_separator")
            config_data["constants_path_separator"] = constants.get("path_separator")
            config_data["constants_hyphen"] = constants.get("hyphen")
            config_data["constants_space"] = constants.get("space")
            config_data["constants_back_card_suffix"] = constants.get("back_card_suffix")

            return cls(**config_data)
        except Exception as e:
            print(
                f"Warning: Could not load web scraping config from {file_path}: {e}\n"
                "Using defaults.",
                file=sys.stderr,
            )
            return cls()


class WebSettingsConfig(BaseSettings):
    """Web HTTP client settings loaded from TOML file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    http_default_timeout: int = Field(default=30, ge=1)
    http_default_user_agent: Optional[str] = None

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "WebSettingsConfig":
        """Load web settings from TOML file."""
        if file_path is None:
            file_path = WEB_SETTINGS_FILE

        if not file_path.exists():
            return cls()

        try:
            # Try using tomllib (Python 3.11+)
            try:
                import tomllib

                with open(file_path, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                # Fallback to tomli for older Python versions
                try:
                    import toml  # type: ignore[import-untyped]i

                    with open(file_path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    # Fallback to toml (pypi package)
                    import toml  # type: ignore[import-untyped]

                    with open(file_path, encoding="utf-8") as f:
                        data = toml.load(f)

            http_settings = data.get("http", {})
            return cls(
                http_default_timeout=http_settings.get("default_timeout", 30),
                http_default_user_agent=http_settings.get("default_user_agent"),
            )
        except Exception as e:
            print(
                f"Warning: Could not load web settings from {file_path}: {e}\nUsing defaults.",
                file=sys.stderr,
            )
            return cls()


# Global instances - loaded on import
_web_scraping_config: Optional[WebScrapingConfig] = None
_web_settings_config: Optional[WebSettingsConfig] = None


def get_web_scraping_config() -> WebScrapingConfig:
    """Get web scraping configuration.

    Loads from TOML file on first call, then caches the result.

    Returns:
        WebScrapingConfig instance with loaded config.
    """
    global _web_scraping_config
    if _web_scraping_config is None:
        _web_scraping_config = WebScrapingConfig.load_from_file()
    return _web_scraping_config


def get_web_settings() -> WebSettingsConfig:
    """Get web HTTP client settings.

    Loads from TOML file on first call, then caches the result.

    Returns:
        WebSettingsConfig instance with loaded settings.
    """
    global _web_settings_config
    if _web_settings_config is None:
        _web_settings_config = WebSettingsConfig.load_from_file()
    return _web_settings_config
