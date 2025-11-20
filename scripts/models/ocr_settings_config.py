#!/usr/bin/env python3
"""
Pydantic Settings model for OCR settings configuration.

Loads Tesseract OCR and image preprocessing settings from TOML file.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\nInstall with: uv add pydantic-settings\n",
        file=sys.stderr,
    )
    raise

# Path to OCR settings TOML file
OCR_SETTINGS_FILE: Path = Path(__file__).parent.parent / "data" / "ocr_settings.toml"


class OCRSettingsConfig(BaseSettings):
    """OCR settings loaded from TOML configuration file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ocr_tesseract_default_psm_mode: int = Field(default=3, ge=0, le=13)
    ocr_tesseract_default_oem_mode: int = Field(default=3, ge=0, le=3)
    ocr_preprocessing_enhance_contrast: bool = Field(default=True)
    ocr_preprocessing_denoise_strength: int = Field(default=10, ge=0, le=100)

    @classmethod
    def load_from_file(cls, file_path: Optional[Path] = None) -> "OCRSettingsConfig":
        """Load OCR settings from TOML file."""
        if file_path is None:
            file_path = OCR_SETTINGS_FILE

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

            ocr = data.get("ocr", {})
            tesseract = ocr.get("tesseract", {})
            preprocessing = ocr.get("preprocessing", {})

            return cls(
                ocr_tesseract_default_psm_mode=tesseract.get("default_psm_mode", 3),
                ocr_tesseract_default_oem_mode=tesseract.get("default_oem_mode", 3),
                ocr_preprocessing_enhance_contrast=preprocessing.get("enhance_contrast", True),
                ocr_preprocessing_denoise_strength=preprocessing.get("denoise_strength", 10),
            )
        except Exception as e:
            print(
                f"Warning: Could not load OCR settings from {file_path}: {e}\nUsing defaults.",
                file=sys.stderr,
            )
            return cls()


# Global instance - loaded on import
_ocr_settings_config: Optional[OCRSettingsConfig] = None


def get_ocr_settings() -> OCRSettingsConfig:
    """Get OCR settings configuration.

    Loads from TOML file on first call, then caches the result.

    Returns:
        OCRSettingsConfig instance with loaded settings.
    """
    global _ocr_settings_config
    if _ocr_settings_config is None:
        _ocr_settings_config = OCRSettingsConfig.load_from_file()
    return _ocr_settings_config
