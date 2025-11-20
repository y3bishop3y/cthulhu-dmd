#!/usr/bin/env python3
"""
Pydantic Settings model for parsing patterns configuration.

Loads regex patterns and keywords from TOML file for easy maintenance.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "Install with: uv add pydantic-settings\n",
        file=sys.stderr,
    )
    raise

# Path to parsing patterns TOML file
PARSING_PATTERNS_FILE: Path = Path(__file__).parent.parent / "data" / "parsing_patterns.toml"


class ParsingPatternsConfig(BaseSettings):
    """Parsing patterns loaded from TOML configuration file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Effect indicators (simple keywords only)
    effect_indicators: List[str] = Field(default_factory=list)

    # Power parsing keywords (simple strings, not regex)
    power_parsing_gain_patterns: List[str] = Field(default_factory=list)
    power_parsing_sanity_patterns: List[str] = Field(default_factory=list)

    # Key phrases for analysis (simple keywords)
    key_phrases_dice: List[str] = Field(default_factory=list)
    key_phrases_elder_sign: List[str] = Field(default_factory=list)
    key_phrases_success: List[str] = Field(default_factory=list)
    key_phrases_attack: List[str] = Field(default_factory=list)
    key_phrases_action: List[str] = Field(default_factory=list)

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "ParsingPatternsConfig":
        """Load parsing patterns from TOML file."""
        if file_path is None:
            file_path = PARSING_PATTERNS_FILE

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
                    import tomli

                    with open(file_path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    # Fallback to toml (pypi package)
                    import toml

                    with open(file_path, encoding="utf-8") as f:
                        data = toml.load(f)

            # Flatten nested structure
            config_data = {}
            patterns = data.get("patterns", {})

            # Effect indicators (simple keywords)
            config_data["effect_indicators"] = patterns.get("effect_indicators", {}).get("keywords", [])

            # Power parsing keywords (simple strings)
            power_parsing = patterns.get("power_parsing", {})
            config_data["power_parsing_gain_patterns"] = power_parsing.get("gain_patterns", [])
            config_data["power_parsing_sanity_patterns"] = power_parsing.get("sanity_patterns", [])

            # Key phrases (simple keywords)
            key_phrases = patterns.get("key_phrases", {})
            config_data["key_phrases_dice"] = key_phrases.get("dice", [])
            config_data["key_phrases_elder_sign"] = key_phrases.get("elder_sign", [])
            config_data["key_phrases_success"] = key_phrases.get("success", [])
            config_data["key_phrases_attack"] = key_phrases.get("attack", [])
            config_data["key_phrases_action"] = key_phrases.get("action", [])

            return cls(**config_data)
        except Exception as e:
            print(
                f"Warning: Could not load parsing patterns from {file_path}: {e}\n"
                "Using empty patterns.",
                file=sys.stderr,
            )
            return cls()


# Global instance - loaded on import
_parsing_config: Optional[ParsingPatternsConfig] = None


def get_parsing_patterns() -> ParsingPatternsConfig:
    """Get parsing patterns configuration.

    Loads from TOML file on first call, then caches the result.

    Returns:
        ParsingPatternsConfig instance with loaded patterns.
    """
    global _parsing_config
    if _parsing_config is None:
        _parsing_config = ParsingPatternsConfig.load_from_file()
    return _parsing_config

