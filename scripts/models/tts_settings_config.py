#!/usr/bin/env python3
"""
Pydantic Settings model for TTS settings configuration.

Loads TTS model settings from TOML file.
"""

import sys
from pathlib import Path
from typing import Optional

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

# Path to TTS settings TOML file
TTS_SETTINGS_FILE: Path = Path(__file__).parent.parent / "data" / "tts_settings.toml"


class TTSSettingsConfig(BaseSettings):
    """TTS settings loaded from TOML configuration file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    tts_default_model: Optional[str] = Field(default=None, description="Default TTS model to use")

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "TTSSettingsConfig":
        """Load TTS settings from TOML file."""
        if file_path is None:
            file_path = TTS_SETTINGS_FILE

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

            tts = data.get("tts", {})
            return cls(tts_default_model=tts.get("default_model"))
        except Exception as e:
            print(
                f"Warning: Could not load TTS settings from {file_path}: {e}\n"
                "Using defaults.",
                file=sys.stderr,
            )
            return cls()


# Global instance - loaded on import
_tts_settings_config: Optional[TTSSettingsConfig] = None


def get_tts_settings() -> TTSSettingsConfig:
    """Get TTS settings configuration.

    Loads from TOML file on first call, then caches the result.

    Returns:
        TTSSettingsConfig instance with loaded settings.
    """
    global _tts_settings_config
    if _tts_settings_config is None:
        _tts_settings_config = TTSSettingsConfig.load_from_file()
    return _tts_settings_config

