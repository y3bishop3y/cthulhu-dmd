#!/usr/bin/env python3
"""
Pydantic models for character parsing operations.

Provides type-safe data structures for parsing character cards with field-specific extraction.
"""

from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, Field, computed_field


class FrontCardFields(BaseModel):
    """Fields extracted from front card using field-specific optimal strategies."""

    name: Optional[str] = Field(default=None, description="Extracted character name")
    location: Optional[str] = Field(default=None, description="Extracted character location")
    motto: Optional[str] = Field(default=None, description="Extracted character motto")
    story: Optional[str] = Field(default=None, description="Extracted character story")

    @classmethod
    def from_dict(cls, data: dict) -> "FrontCardFields":
        """Create FrontCardFields from dictionary.

        Args:
            data: Dictionary with keys: name, location, motto, story

        Returns:
            FrontCardFields instance
        """
        return cls(
            name=data.get("name") or None,
            location=data.get("location") or None,
            motto=data.get("motto") or None,
            story=data.get("story") or None,
        )

    @classmethod
    def from_layout_results(cls, layout_results: Any) -> "FrontCardFields":
        """Create FrontCardFields from LayoutExtractionResults.

        Args:
            layout_results: LayoutExtractionResults from CardLayoutExtractor

        Returns:
            FrontCardFields instance
        """
        return cls(
            name=layout_results.name or None,
            location=layout_results.location or None,
            motto=layout_results.motto or None,
            story=layout_results.description or None,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_essential_fields(self) -> bool:
        """Check if essential fields (name or location) are present."""
        return bool(self.name or self.location)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_all_fields(self) -> bool:
        """Check if all fields are present."""
        return bool(self.name and self.location and self.motto and self.story)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def to_text(self) -> str:
        """Combine fields into text format for parsing."""
        parts: List[str] = []
        if self.name:
            parts.append(self.name)
        if self.location:
            parts.append(self.location)
        if self.motto:
            parts.append(self.motto)
        if self.story:
            parts.append(self.story)
        return "\n".join(parts)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_empty(self) -> bool:
        """Check if all fields are empty."""
        return not (self.name or self.location or self.motto or self.story)

    def to_front_card_data(self, story_override: Optional[str] = None) -> Any:
        """Convert to FrontCardData model.

        Args:
            story_override: Optional story text to override extracted story

        Returns:
            FrontCardData instance
        """
        from scripts.models.character import FrontCardData

        return FrontCardData(
            name=self.name,
            location=self.location,
            motto=self.motto,
            story=story_override or self.story,
        )


class FieldStrategies(BaseModel):
    """OCR strategies for each field type."""

    name: str = Field(description="OCR strategy for name extraction")
    location: str = Field(description="OCR strategy for location extraction")
    motto: str = Field(description="OCR strategy for motto extraction")
    story: str = Field(description="OCR strategy for story extraction")


class ImageRegions(BaseModel):
    """Region coordinates for front card fields."""

    name: Tuple[int, int, int, int] = Field(description="Name region (x, y, width, height)")
    location: Tuple[int, int, int, int] = Field(description="Location region (x, y, width, height)")
    motto: Tuple[int, int, int, int] = Field(description="Motto region (x, y, width, height)")
    story: Tuple[int, int, int, int] = Field(description="Story region (x, y, width, height)")
