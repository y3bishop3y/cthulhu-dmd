#!/usr/bin/env python3
"""
Pydantic models for trait-character assignments with parsing capabilities.

This module defines models for parsing and representing which characters
have which common traits, extracted from the traits booklet PDF.
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, computed_field

from scripts.models.constants import CommonPower


class CharacterReference(BaseModel):
    """Reference to a character with name and number."""

    name: str = Field(..., description="Character name")
    number: int = Field(..., ge=1, description="Character number")

    @classmethod
    def from_text(cls, text: str) -> Optional["CharacterReference"]:
        """Extract character name and number from text like 'Al Capone (20)' or 'Lord Adam Benchley (7)'.

        Args:
            text: Text containing character name and number in format "Name (Number)"

        Returns:
            CharacterReference if found, None otherwise
        """
        # Pattern: "Name (Number)" or "Name, Name (Number)"
        # Handle names with quotes, apostrophes, titles, etc.
        pattern = r"([A-Z][a-zA-Z\s'\-\.]+?)\s*\((\d+)\)"
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            number = int(match.group(2))
            return cls(name=name, number=number)
        return None

    def __str__(self) -> str:
        """String representation: 'Name (Number)'."""
        return f"{self.name} ({self.number})"


class TraitSection(BaseModel):
    """A trait section with its assigned characters."""

    trait_name: str = Field(..., description="Name of the trait")
    characters: List[CharacterReference] = Field(
        default_factory=list, description="Characters with this trait"
    )

    @classmethod
    def parse_from_text(cls, text: str, trait_name: str) -> "TraitSection":
        """Parse a trait section from PDF text to extract character assignments.

        Args:
            text: Full text from the PDF pages
            trait_name: Name of the trait (e.g., "Swiftness", "Toughness")

        Returns:
            TraitSection with parsed character assignments
        """
        characters: List[CharacterReference] = []

        # Find the trait section
        lines = text.split("\n")
        in_section = False

        # Get all common trait names for boundary detection
        all_trait_names = [cp.value for cp in CommonPower]

        for i, line in enumerate(lines):
            # Look for trait name as heading
            # Handle both "Trait Appendix" and "Trait Common Trait Quick" patterns
            trait_upper = trait_name.upper()
            line_upper = line.upper()
            if trait_upper in line_upper and (
                "Appendix" in line or "Common Trait" in line or "trait" in line.lower()
            ):
                in_section = True
                continue

            # Stop if we hit another trait section
            if in_section:
                for other_trait in all_trait_names:
                    if (
                        other_trait != trait_name
                        and other_trait.upper() in line.upper()
                        and "Appendix" in line
                    ):
                        return cls(trait_name=trait_name, characters=characters)

                # Extract character names from this line
                # Handle multiple characters per line: "Name1 (1), Name2 (2), Name3 (3)"
                # Split by comma first, then extract each
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    char_ref = CharacterReference.from_text(part)
                    if char_ref:
                        characters.append(char_ref)

        return cls(trait_name=trait_name, characters=characters)

    @computed_field
    @property
    def character_count(self) -> int:
        """Number of characters with this trait."""
        return len(self.characters)

    @computed_field
    @property
    def character_names(self) -> List[str]:
        """List of character names (with numbers) as strings."""
        return [str(char) for char in self.characters]


class TraitCharacterAssignments(BaseModel):
    """Complete trait-character assignments with parsing and analysis capabilities."""

    trait_sections: Dict[str, TraitSection] = Field(
        default_factory=dict,
        description="Mapping of trait names to their sections",
    )

    @classmethod
    def parse_from_text(cls, text: str) -> "TraitCharacterAssignments":
        """Parse trait-character assignments from PDF text.

        Args:
            text: Full text from PDF pages containing trait sections

        Returns:
            TraitCharacterAssignments with all parsed sections
        """
        trait_sections: Dict[str, TraitSection] = {}

        # Parse each common trait
        for common_power in CommonPower:
            trait_name = common_power.value
            section = TraitSection.parse_from_text(text, trait_name)
            trait_sections[trait_name] = section

        return cls(trait_sections=trait_sections)

    @computed_field
    @property
    def character_to_traits(self) -> Dict[str, Set[str]]:
        """Mapping of character references to their traits."""
        char_to_traits: Dict[str, Set[str]] = defaultdict(set)

        for trait_name, section in self.trait_sections.items():
            for char_ref in section.characters:
                char_key = str(char_ref)
                char_to_traits[char_key].add(trait_name)

        return dict(char_to_traits)

    @computed_field
    @property
    def characters_with_multiple_traits(self) -> Dict[str, Set[str]]:
        """Characters that have more than one trait."""
        char_to_traits = self.character_to_traits
        return {char: traits for char, traits in char_to_traits.items() if len(traits) > 1}

    def get_trait_section(self, trait_name: str) -> Optional[TraitSection]:
        """Get trait section by name."""
        return self.trait_sections.get(trait_name)

    def get_characters_for_trait(self, trait_name: str) -> List[CharacterReference]:
        """Get all characters with a specific trait."""
        section = self.get_trait_section(trait_name)
        return section.characters if section else []

    def get_traits_for_character(self, character_name: str) -> Set[str]:
        """Get all traits for a specific character."""
        char_to_traits = self.character_to_traits
        return char_to_traits.get(character_name, set())

    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            "total_traits": len(self.trait_sections),
            "total_characters": len(self.character_to_traits),
            "characters_with_multiple_traits": len(self.characters_with_multiple_traits),
        }
