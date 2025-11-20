#!/usr/bin/env python3
"""
Pydantic Settings model for OCR corrections configuration.

Loads OCR corrections from TOML file for easy maintenance.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

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

# Path to OCR corrections TOML file
OCR_CORRECTIONS_FILE: Path = Path(__file__).parent.parent / "data" / "ocr_corrections.toml"


class OCRCorrectionsConfig(BaseSettings):
    """OCR corrections loaded from TOML configuration file."""

    model_config = SettingsConfigDict(
        env_file=None,  # Don't use .env file
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    corrections: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of OCR errors to corrections",
    )

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "OCRCorrectionsConfig":
        """Load OCR corrections from TOML file.

        Args:
            file_path: Path to TOML file. If None, uses default location.

        Returns:
            OCRCorrectionsConfig instance with loaded corrections.
        """
        if file_path is None:
            file_path = OCR_CORRECTIONS_FILE

        if not file_path.exists():
            # Return empty config if file doesn't exist
            return cls(corrections={})

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

            corrections = data.get("corrections", {})
            return cls(corrections=corrections)
        except Exception as e:
            print(
                f"Warning: Could not load OCR corrections from {file_path}: {e}\n"
                "Using empty corrections dictionary.",
                file=sys.stderr,
            )
            return cls(corrections={})

    def get_corrections_dict(self) -> Dict[str, str]:
        """Get corrections as a dictionary.

        Returns:
            Dictionary mapping OCR errors to corrections.
        """
        return self.corrections.copy()


# Global instance - loaded on import
_ocr_config: Optional[OCRCorrectionsConfig] = None


def get_ocr_corrections() -> Dict[str, str]:
    """Get OCR corrections dictionary.

    Loads from TOML file on first call, then caches the result.

    Returns:
        Dictionary mapping OCR errors to corrections.
    """
    global _ocr_config
    if _ocr_config is None:
        _ocr_config = OCRCorrectionsConfig.load_from_file()
    return _ocr_config.get_corrections_dict()

