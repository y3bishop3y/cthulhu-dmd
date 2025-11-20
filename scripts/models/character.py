#!/usr/bin/env python3
"""
Pydantic models for character data with parsing capabilities.

This module defines models for characters, their powers, and related data
extracted from character cards and HTML pages. Parsing logic is encapsulated
within the models themselves for better organization and reusability.
"""

import re
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from scripts.models.constants import CommonPower


class PowerLevelStatistics(BaseModel):
    """Statistics for a power level from common_powers.json."""

    green_dice_added: int = Field(default=0, ge=0, description="Number of green dice added")
    black_dice_added: int = Field(default=0, ge=0, description="Number of black dice added")
    base_expected_successes: float = Field(default=0.0, ge=0.0, description="Expected successes with base dice")
    enhanced_expected_successes: float = Field(default=0.0, ge=0.0, description="Expected successes with enhancement")
    expected_successes_increase: float = Field(default=0.0, description="Absolute increase in expected successes")
    expected_successes_percent_increase: float = Field(default=0.0, description="Percentage increase in expected successes")
    max_successes_increase: int = Field(default=0, ge=0, description="Increase in maximum possible successes")
    tentacle_risk: float = Field(default=0.0, ge=0.0, description="Expected tentacles with enhancement")
    base_tentacle_risk: float = Field(default=0.0, ge=0.0, description="Expected tentacles with base dice")
    is_conditional: bool = Field(default=False, description="Whether this power has conditional effects")
    conditions: List[str] = Field(default_factory=list, description="List of condition strings")
    rerolls_added: int = Field(default=0, ge=0, description="Number of rerolls added")
    reroll_type: Optional[str] = Field(default=None, description="Type of reroll: 'free' or 'standard'")
    has_reroll: bool = Field(default=False, description="Whether this power adds any rerolls")
    wounds_healed: int = Field(default=0, ge=0, description="Number of wounds healed")
    stress_healed: int = Field(default=0, ge=0, description="Number of stress healed")
    has_healing: bool = Field(default=False, description="Whether this power has any healing effects")
    wound_reduction: int = Field(default=0, ge=0, description="Wound damage reduction")
    sanity_reduction: int = Field(default=0, ge=0, description="Sanity loss reduction")
    has_defensive: bool = Field(default=False, description="Whether this power has any defensive effects")

    @computed_field
    @property
    def has_any_improvements(self) -> bool:
        """Check if this power level has any improvements (conditional, reroll, healing, or defensive)."""
        return (
            self.is_conditional
            or self.has_reroll
            or self.has_healing
            or self.has_defensive
        )

    def get_improvements_list(self) -> List[str]:
        """Get a list of human-readable improvement descriptions.

        Returns:
            List of improvement description strings
        """
        improvements = []
        if self.is_conditional:
            improvements.append(f"Conditional: {', '.join(self.conditions)}")
        if self.has_reroll:
            improvements.append(f"Rerolls: {self.rerolls_added} ({self.reroll_type})")
        if self.has_healing:
            improvements.append(f"Healing: {self.wounds_healed} wounds, {self.stress_healed} stress")
        if self.has_defensive:
            improvements.append(f"Defensive: {self.wound_reduction} wounds, {self.sanity_reduction} sanity")
        return improvements


class PowerLevel(BaseModel):
    """Represents a single level of a power."""

    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    description: str = Field(..., description="Power level description")

    @classmethod
    def from_text(cls, level_num: int, description: str) -> "PowerLevel":
        """Create a PowerLevel from parsed text."""
        return cls(level=level_num, description=description.strip())


class Power(BaseModel):
    """Represents a character power (special or common)."""

    name: str = Field(..., description="Name of the power")
    is_special: bool = Field(
        default=False, description="Whether this is a special power (vs common)"
    )
    levels: List[PowerLevel] = Field(default_factory=list, description="Power levels (1-4)")

    @computed_field
    @property
    def has_levels(self) -> bool:
        """Whether this power has any levels."""
        return len(self.levels) > 0

    @computed_field
    @property
    def is_complete(self) -> bool:
        """Whether this power has all expected levels."""
        if self.is_special:
            return len(self.levels) >= 1
        return len(self.levels) >= 4

    def add_level(self, level: PowerLevel) -> None:
        """Add a level to this power."""
        self.levels.append(level)

    def add_level_from_text(self, level_num: int, description: str) -> None:
        """Add a level from parsed text."""
        self.levels.append(PowerLevel.from_text(level_num, description))


class FrontCardData(BaseModel):
    """Parsed data from front card with parsing capabilities."""

    name: Optional[str] = Field(default=None, description="Character name")
    location: Optional[str] = Field(default=None, description="Character location")
    motto: Optional[str] = Field(default=None, description="Character motto")
    story: Optional[str] = Field(default=None, description="Character backstory")

    @classmethod
    def parse_from_text(cls, text: str) -> "FrontCardData":
        """Parse front card text to extract name, location, motto, and story."""
        from scripts.utils.parsing import clean_ocr_text

        # Clean the text first, preserving newlines for line-by-line parsing
        cleaned_text = clean_ocr_text(text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        data = cls()

        # Look for name (usually in all caps, first few lines, looks like a name)
        for line in lines[:10]:
            # Check if it's all caps and looks like a name (has letters, reasonable length)
            if (
                line.isupper()
                and len(line) > 5
                and len(line) < 60
                and re.match(r"^[A-Z\s]+$", line)
                and not re.match(r"^[A-Z\s]{1,3}$", line)  # Not just initials
            ):
                # Convert to Title Case
                data.name = line.title()
                break

        # Look for location (usually after name, in format "CITY, COUNTRY" or "CITY, STATE")
        for line in lines:
            # Look for location pattern: CITY, COUNTRY/STATE
            if "," in line and line.isupper() and len(line) < 60 and re.match(r"^[A-Z\s,]+$", line):
                if data.location is None:
                    data.location = line.title()
                    break

        # Look for motto (usually in quotes, may span multiple lines)
        # First try to find quoted text
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, cleaned_text)
        if quotes:
            # Take the first complete quote
            data.motto = quotes[0].strip()
        else:
            # Look for multi-line quotes or motto-like text
            # Motto is usually short, not all caps, and may contain keywords
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if (
                    len(line) < 150
                    and not line.isupper()
                    and not line.isdigit()
                    and data.motto is None
                ):
                    # Check if it looks like a motto (short, may have keywords)
                    if any(
                        word in line_lower
                        for word in ["first", "never", "always", "shoot", "ask", "trust"]
                    ):
                        # Check if next line completes it
                        if i + 1 < len(lines) and len(lines[i + 1]) < 100:
                            combined = f"{line} {lines[i + 1]}"
                            if len(combined) < 150:
                                data.motto = combined.strip()
                                break
                        else:
                            data.motto = line.strip()
                            break

        # Story is usually the longest paragraph after the motto
        # Find paragraphs (separated by blank lines or significant whitespace)
        paragraphs = re.split(r"\n\s*\n+", cleaned_text)
        # Filter out very short paragraphs and the name/location/motto
        story_paragraphs = [
            p.strip()
            for p in paragraphs
            if len(p.strip()) > 100
            and not p.strip().isupper()
            and (not data.name or data.name not in p)
            and (not data.location or data.location not in p)
            and (not data.motto or data.motto not in p)
        ]

        if story_paragraphs:
            # Take the longest paragraph as the story
            longest_para = max(story_paragraphs, key=len)
            # Clean up the story text
            story = clean_ocr_text(longest_para)
            # Remove any remaining OCR artifacts
            story = re.sub(r"\s+", " ", story).strip()
            data.story = story

        return data

    @computed_field
    @property
    def is_complete(self) -> bool:
        """Whether all required fields are present."""
        return bool(self.name and self.location and self.motto and self.story)


class BackCardData(BaseModel):
    """Parsed data from back card with parsing capabilities."""

    special_power: Optional[Power] = Field(default=None, description="Character's special power")
    common_powers: List[Power] = Field(default_factory=list, description="List of common powers")

    @classmethod
    def parse_from_text(cls, text: str) -> "BackCardData":
        """Parse back card text to extract powers and their levels."""
        from scripts.utils.parsing import clean_ocr_text

        # Clean the text first, preserving newlines for line-by-line parsing
        cleaned_text = clean_ocr_text(text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        data = cls()

        # Look for special power (usually mentioned first, has unique name)
        current_power: Optional[Power] = None
        power_content_lines: List[str] = []
        found_common_power = False

        i = 0
        while i < len(lines):
            line = lines[i]
            line_lower = line.lower()
            line_upper = line.upper()

            # Skip game rules sections (YOUR TURN, TAKE ACTIONS, etc.)
            if any(
                keyword in line_upper
                for keyword in [
                    "YOUR TURN",
                    "TAKE",
                    "DRAW MYTHOS",
                    "INVESTIGATE",
                    "FIGHT",
                    "RESOLVE",
                    "OR FIGHT!",
                    "INVESTIGATE OR FIGHT!",
                ]
            ):
                i += 1
                continue

            # Check for special power BEFORE we find any common powers
            is_special_power = False
            special_power_name = None

            # Check for "Fueled by Madness" pattern
            if "fueled" in line_lower and "madness" in line_lower:
                # Extract the power name
                words = line.split()
                power_words = []
                for word in words:
                    if word[0].isupper() or word.lower() in ["by", "the"]:
                        power_words.append(word)
                    elif power_words:
                        break
                if power_words:
                    special_power_name = " ".join(power_words)
                    is_special_power = True

            # Check for special power description pattern (Gain X while your sanity...)
            # Load simple keywords from TOML config
            from scripts.models.parsing_config import get_parsing_patterns

            patterns_config = get_parsing_patterns()
            gain_patterns = (
                patterns_config.power_parsing_gain_patterns
                if patterns_config.power_parsing_gain_patterns
                else ["gain", "goin", "go in"]
            )
            sanity_patterns = (
                patterns_config.power_parsing_sanity_patterns
                if patterns_config.power_parsing_sanity_patterns
                else ["sanity", "santiy"]
            )

            # Check current line and surrounding lines for the pattern
            has_gain = any(g in line_lower for g in gain_patterns)
            has_sanity = any(s in line_lower for s in sanity_patterns)

            # Check next few lines for sanity if current line has gain
            if has_gain and not has_sanity and i + 1 < len(lines):
                for j in range(i + 1, min(i + 4, len(lines))):
                    if any(s in lines[j].lower() for s in sanity_patterns):
                        has_sanity = True
                        break

            # Check previous lines for gain if current line has sanity
            if has_sanity and not has_gain and i > 0:
                for j in range(max(0, i - 3), i):
                    if any(g in lines[j].lower() for g in gain_patterns):
                        has_gain = True
                        break

            # Only detect special power if we haven't found any common powers yet
            # and the pattern appears before any common power names
            if not is_special_power and not found_common_power and (has_gain and has_sanity):
                special_power_name = "Fueled by Madness"
                is_special_power = True

            # Check if it's a common power name (all caps, matches known powers)
            is_common_power = False
            common_power_name = None

            for common_power in CommonPower:
                power_name = common_power.value
                if power_name.upper() in line_upper or line_upper == power_name.upper():
                    common_power_name = power_name
                    is_common_power = True
                    found_common_power = True
                    break

            # If we found a power name, save previous power and start new one
            if is_special_power and special_power_name:
                # Save previous power
                if current_power:
                    if current_power.is_special:
                        data.special_power = current_power
                    else:
                        data.common_powers.append(current_power)

                # Start tracking special power
                current_power = Power(name=special_power_name, is_special=True, levels=[])
                power_content_lines = [line]  # Include current line
                i += 1
                continue

            elif is_common_power and common_power_name:
                # Save previous power
                if current_power:
                    if current_power.is_special:
                        data.special_power = current_power
                    else:
                        data.common_powers.append(current_power)

                # Start tracking common power
                current_power = Power(name=common_power_name, is_special=False, levels=[])
                power_content_lines = []
                i += 1
                continue

            # If we're tracking a power, collect content lines
            if current_power:
                # Check for level indicators (Level 1, Level 2, etc. or just numbers at start)
                level_match = re.search(r"^(?:level\s*)?(\d+)[:\-]?\s*", line_lower)
                if level_match:
                    # Save previous level if we have accumulated content
                    if power_content_lines:
                        level_num = len(current_power.levels) + 1
                        description = " ".join(power_content_lines).strip()
                        if description and len(description.split()) > 2:
                            current_power.add_level_from_text(level_num, description)
                        power_content_lines = []

                    # Start new level
                    level_num = int(level_match.group(1))
                    description = re.sub(
                        r"^(?:level\s*)?\d+[:\-]?\s*", "", line, flags=re.I
                    ).strip()
                    if description:
                        power_content_lines = [description]
                else:
                    # Check if this looks like a level description continuation
                    is_description = any(
                        line_lower.startswith(prefix)
                        for prefix in [
                            "you may",
                            "instead",
                            "gain",
                            "when",
                            "reduce",
                            "attacking",
                            "target",
                        ]
                    ) or (
                        re.match(r"^[A-Z]", line)
                        and len(line.split()) > 2
                        and line_upper not in [cp.value.upper() for cp in CommonPower]
                    )

                    # Check if this is a continuation of the current description
                    is_continuation = (
                        len(line.split()) <= 8
                        and not line[0].isupper()
                        and power_content_lines
                        and not any(cp.value.upper() in line_upper for cp in CommonPower)
                    )

                    if is_description or is_continuation:
                        power_content_lines.append(line)
                    elif power_content_lines:
                        # We have accumulated content but hit something that doesn't look like continuation
                        # Check if next line is a new power or if we should save this level
                        next_is_power = False
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            next_upper = next_line.upper()
                            # Check if next line is a common power name
                            if any(
                                cp.value.upper() in next_upper or next_upper == cp.value.upper()
                                for cp in CommonPower
                            ):
                                next_is_power = True

                        # Save accumulated level if we have enough content and haven't hit max levels
                        if len(current_power.levels) < 4 and not next_is_power:
                            level_num = len(current_power.levels) + 1
                            description = " ".join(power_content_lines).strip()
                            if description and len(description.split()) > 2:
                                current_power.add_level_from_text(level_num, description)
                            power_content_lines = []

            i += 1

        # Don't forget the last power
        if current_power:
            # Save any remaining accumulated level content
            if power_content_lines and len(current_power.levels) < 4:
                level_num = len(current_power.levels) + 1
                description = " ".join(power_content_lines).strip()
                if description and len(description.split()) > 2:
                    current_power.add_level_from_text(level_num, description)

            if current_power.is_special:
                data.special_power = current_power
            else:
                data.common_powers.append(current_power)

        # Post-process: ensure special power has at least one level with description
        if data.special_power and not data.special_power.has_levels:
            # Try to extract description from the text
            # Load simple keywords from TOML config
            from scripts.models.parsing_config import get_parsing_patterns

            patterns_config = get_parsing_patterns()
            gain_patterns = (
                patterns_config.power_parsing_gain_patterns
                if patterns_config.power_parsing_gain_patterns
                else ["gain", "goin", "go in"]
            )
            sanity_patterns = (
                patterns_config.power_parsing_sanity_patterns
                if patterns_config.power_parsing_sanity_patterns
                else ["sanity", "santiy"]
            )
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Check if this line has gain pattern
                has_gain = any(g in line_lower for g in gain_patterns)
                has_sanity = any(s in line_lower for s in sanity_patterns)

                # Also check surrounding lines for multi-line patterns
                if has_gain and not has_sanity and i + 1 < len(lines):
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if any(s in lines[j].lower() for s in sanity_patterns):
                            has_sanity = True
                            break

                if has_gain and has_sanity:
                    # Collect multi-line description
                    desc_lines = [line.strip()]
                    # Look ahead for continuation (up to 3 more lines)
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        # Skip empty lines and common power names
                        if not next_line or any(
                            cp.value.upper() in next_line.upper() for cp in CommonPower
                        ):
                            break
                        # Include short lines that might be continuation
                        if len(next_line.split()) <= 10:
                            desc_lines.append(next_line)
                        else:
                            break
                    description = " ".join(desc_lines).strip()
                    if description and len(description) > 10:
                        data.special_power.add_level_from_text(1, description)
                        break

        return data

    @computed_field
    @property
    def is_complete(self) -> bool:
        """Whether all required powers are present and complete."""
        if not self.special_power or not self.special_power.is_complete:
            return False
        if len(self.common_powers) < 2:
            return False
        return all(cp.is_complete for cp in self.common_powers)


class CharacterData(BaseModel):
    """Complete character data with parsing and merging capabilities."""

    name: str = Field(..., description="Character name")
    location: Optional[str] = Field(default=None, description="Character location")
    motto: Optional[str] = Field(default=None, description="Character motto/quote")
    story: Optional[str] = Field(default=None, description="Character story/background")
    special_power: Optional[Power] = Field(default=None, description="Character's special power")
    common_powers: List[str] = Field(
        default_factory=list,
        description="List of common power names (references to CommonPower enum)",
    )

    @classmethod
    def from_images(
        cls,
        front_text: str,
        back_text: str,
        story_text: Optional[str] = None,
    ) -> "CharacterData":
        """Create CharacterData by parsing front and back card text."""
        front_data = FrontCardData.parse_from_text(front_text)
        back_data = BackCardData.parse_from_text(back_text)

        # Use provided story text if available, otherwise use parsed story
        story = story_text or front_data.story

        # Convert Power objects to common power names (strings)
        common_power_names = [cp.name for cp in back_data.common_powers]

        return cls(
            name=front_data.name or "Unknown",
            location=front_data.location,
            motto=front_data.motto,
            story=story,
            special_power=back_data.special_power,
            common_powers=common_power_names,
        )

    def merge_with(self, other: "CharacterData", prefer_html: bool = True) -> "CharacterData":
        """Merge with another CharacterData instance, preferring HTML-extracted data if prefer_html is True."""
        merged = CharacterData(
            name=other.name if prefer_html else (self.name or other.name),
            location=self.location or other.location,
            motto=self.motto or other.motto,
            story=other.story if prefer_html else (self.story or other.story),
        )

        # Merge powers - prefer existing if they exist and are complete
        if self.special_power and self.special_power.is_complete:
            merged.special_power = self.special_power
        elif other.special_power:
            merged.special_power = other.special_power

        # Merge common powers - prefer existing if they exist
        if self.common_powers:
            merged.common_powers = self.common_powers
        elif other.common_powers:
            merged.common_powers = other.common_powers

        return merged

    def detect_issues(self) -> List[str]:
        """Detect issues with parsed character data."""
        issues: List[str] = []

        # Check front card issues
        if not self.name or len(self.name) < 3:
            issues.append(f"Missing or invalid character name: '{self.name}'")

        if not self.location:
            issues.append("Missing location")

        if not self.motto:
            issues.append("Missing motto")

        if not self.story:
            issues.append("Missing story")

        # Check back card issues
        if not self.special_power:
            issues.append("Missing special power")
        elif not self.special_power.is_complete:
            issues.append("Special power is incomplete")

        if not self.common_powers:
            issues.append("Missing common powers")
        elif len(self.common_powers) < 2:
            issues.append(f"Only found {len(self.common_powers)} common power(s), expected 2")

        return issues

    def has_common_power(self, power: CommonPower) -> bool:
        """Check if character has a specific common power."""
        return power.value in self.common_powers

    def get_common_power_names(self) -> List[str]:
        """Get list of common power names."""
        return self.common_powers.copy()


class CommonPowerLevelData(BaseModel):
    """Represents a power level from common_powers.json with statistics."""

    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    description: str = Field(..., description="Power level description")
    statistics: PowerLevelStatistics = Field(..., description="Statistical analysis of this power level")
    effect: str = Field(..., description="Summary of what this power level does")
