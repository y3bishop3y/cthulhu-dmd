#!/usr/bin/env python3
"""
Pydantic models for character data with parsing capabilities.

This module defines models for characters, their powers, and related data
extracted from character cards and HTML pages. Parsing logic is encapsulated
within the models themselves for better organization and reusability.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from pydantic import BaseModel, Field, computed_field

from scripts.models.character_constants import (
    COMMON_POWER_FUZZY_THRESHOLD,
    COMMON_POWER_LENGTH_TOLERANCE,
    LOCATION_MAX_LENGTH,
    MAX_POWER_LEVELS,
    MIN_POWER_DESCRIPTION_WORDS,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    POWER_ACTION_PATTERNS,
)
from scripts.models.character_parsing_helpers import (
    extract_motto_from_multiline,
    extract_motto_from_quotes,
    extract_motto_from_single_line,
    fix_story_ocr_errors,
    is_common_power_description_line,
    is_game_rules_line,
    score_story_paragraph,
)
from scripts.models.constants import CommonPower as CommonPowerEnum

if TYPE_CHECKING:
    from scripts.cli.analyze.powers import PowerLevelAnalysis
    from scripts.cli.update.cleanup import (
        ConditionalEffects,
        DefensiveEffects,
        HealingEffects,
        RerollEffects,
    )


class PowerLevelStatistics(BaseModel):
    """Statistics for a power level from common_powers.json."""

    green_dice_added: int = Field(default=0, ge=0, description="Number of green dice added")
    black_dice_added: int = Field(default=0, ge=0, description="Number of black dice added")
    base_expected_successes: float = Field(
        default=0.0, ge=0.0, description="Expected successes with base dice"
    )
    enhanced_expected_successes: float = Field(
        default=0.0, ge=0.0, description="Expected successes with enhancement"
    )
    expected_successes_increase: float = Field(
        default=0.0, description="Absolute increase in expected successes"
    )
    expected_successes_percent_increase: float = Field(
        default=0.0, description="Percentage increase in expected successes"
    )
    max_successes_increase: int = Field(
        default=0, ge=0, description="Increase in maximum possible successes"
    )
    tentacle_risk: float = Field(
        default=0.0, ge=0.0, description="Expected tentacles with enhancement"
    )
    base_tentacle_risk: float = Field(
        default=0.0, ge=0.0, description="Expected tentacles with base dice"
    )
    is_conditional: bool = Field(
        default=False, description="Whether this power has conditional effects"
    )
    conditions: List[str] = Field(default_factory=list, description="List of condition strings")
    rerolls_added: int = Field(default=0, ge=0, description="Number of rerolls added")
    reroll_type: Optional[str] = Field(
        default=None, description="Type of reroll: 'free' or 'standard'"
    )
    has_reroll: bool = Field(default=False, description="Whether this power adds any rerolls")
    wounds_healed: int = Field(default=0, ge=0, description="Number of wounds healed")
    stress_healed: int = Field(default=0, ge=0, description="Number of stress healed")
    has_healing: bool = Field(
        default=False, description="Whether this power has any healing effects"
    )
    wound_reduction: int = Field(default=0, ge=0, description="Wound damage reduction")
    sanity_reduction: int = Field(default=0, ge=0, description="Sanity loss reduction")
    has_defensive: bool = Field(
        default=False, description="Whether this power has any defensive effects"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_any_improvements(self) -> bool:
        """Check if this power level has any improvements (conditional, reroll, healing, or defensive)."""
        return self.is_conditional or self.has_reroll or self.has_healing or self.has_defensive

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
            improvements.append(
                f"Healing: {self.wounds_healed} wounds, {self.stress_healed} stress"
            )
        if self.has_defensive:
            improvements.append(
                f"Defensive: {self.wound_reduction} wounds, {self.sanity_reduction} sanity"
            )
        return improvements

    @classmethod
    def from_analysis(
        cls,
        analysis: "PowerLevelAnalysis",
        conditional_effects: "ConditionalEffects",
        reroll_effects: "RerollEffects",
        healing_effects: "HealingEffects",
        defensive_effects: "DefensiveEffects",
    ) -> "PowerLevelStatistics":
        """Create PowerLevelStatistics from analysis and extracted effects.

        Args:
            analysis: PowerLevelAnalysis from analyze_power_level()
            conditional_effects: Extracted conditional effects
            reroll_effects: Extracted reroll effects
            healing_effects: Extracted healing effects
            defensive_effects: Extracted defensive effects

        Returns:
            PowerLevelStatistics instance with all calculated statistics
        """
        return cls(
            green_dice_added=analysis.green_dice_added,
            black_dice_added=analysis.black_dice_added,
            base_expected_successes=round(analysis.base_expected_successes, 3),
            enhanced_expected_successes=round(analysis.enhanced_expected_successes, 3),
            expected_successes_increase=round(analysis.expected_successes_increase, 3),
            expected_successes_percent_increase=round(
                analysis.expected_successes_percent_increase, 2
            ),
            max_successes_increase=analysis.max_successes_increase,
            tentacle_risk=round(analysis.tentacle_risk, 3),
            base_tentacle_risk=round(analysis.base_tentacle_risk, 3),
            is_conditional=conditional_effects.is_conditional,
            conditions=conditional_effects.conditions,
            rerolls_added=reroll_effects.rerolls_added,
            reroll_type=reroll_effects.reroll_type,
            has_reroll=reroll_effects.has_reroll,
            wounds_healed=healing_effects.wounds_healed,
            stress_healed=healing_effects.stress_healed,
            has_healing=healing_effects.has_healing,
            wound_reduction=defensive_effects.wound_reduction,
            sanity_reduction=defensive_effects.sanity_reduction,
            has_defensive=defensive_effects.has_defensive,
        )


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_levels(self) -> bool:
        """Whether this power has any levels."""
        return len(self.levels) > 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_complete(self) -> bool:
        """Whether this power has all expected levels."""
        if self.is_special:
            return len(self.levels) >= 4  # Special powers have 4 levels
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
    def parse_from_text(cls, text: str, image_path: Optional[Path] = None) -> "FrontCardData":
        """Parse front card text to extract name, location, motto, and story.

        Args:
            text: OCR-extracted text
            image_path: Optional path to image file for layout-aware extraction
        """
        from scripts.core.parsing.text import clean_ocr_text

        # If image path is provided, try layout-aware extraction first
        if image_path and image_path.exists():
            try:
                from scripts.core.parsing.layout import extract_text_layout_aware

                layout_results = extract_text_layout_aware(image_path)

                # Use layout-aware results if they look good
                data = cls()
                if layout_results.name:
                    data.name = layout_results.name
                if layout_results.location:
                    data.location = layout_results.location
                if layout_results.motto:
                    data.motto = layout_results.motto
                # Don't use layout-aware description - it's often garbled
                # We'll extract story from the OCR text instead

                # If we got name/location/motto from layout-aware, use them
                # But still parse story from OCR text
            except Exception:
                # Fall back to text parsing if layout-aware fails
                pass

        # Clean the text first, preserving newlines for line-by-line parsing
        cleaned_text = clean_ocr_text(text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        data = cls()

        # Look for name (usually in all caps, first few lines, looks like a name)
        for line in lines[:10]:
            # Check if it's all caps and looks like a name (has letters, reasonable length)
            if (
                line.isupper()
                and len(line) > NAME_MIN_LENGTH
                and len(line) < NAME_MAX_LENGTH
                and re.match(r"^[A-Z\s]+$", line)
                and not re.match(r"^[A-Z\s]{1,3}$", line)  # Not just initials
            ):
                # Convert to Title Case
                data.name = line.title()
                break

        # Look for location (usually after name, in format "CITY, COUNTRY" or "CITY, STATE")
        for line in lines:
            # Look for location pattern: CITY, COUNTRY/STATE
            if (
                "," in line
                and line.isupper()
                and len(line) < LOCATION_MAX_LENGTH
                and re.match(r"^[A-Z\s,]+$", line)
            ):
                if data.location is None:
                    data.location = line.title()
                    break

        # Look for motto (usually in quotes, may span multiple lines)
        # Mottos are typically:
        # 1. Short phrases (2-10 words)
        # 2. Near the top (after name/location, before story)
        # 3. May be in quotes or not
        # 4. Often split across 2 lines (e.g., "Shoot first.\nNever ask.")

        # Strategy 1: Look for quoted text first
        data.motto = extract_motto_from_quotes(cleaned_text)

        # Strategy 2: Look for multi-line mottos
        if not data.motto:
            data.motto = extract_motto_from_multiline(lines)

        # Strategy 3: Look for single-line mottos without quotes
        if not data.motto:
            data.motto = extract_motto_from_single_line(lines, data.name, data.location)

        # Story is usually the longest paragraph after the motto
        # Find paragraphs (separated by blank lines or significant whitespace)
        paragraphs = re.split(r"\n\s*\n+", cleaned_text)
        # Also try splitting by single newlines if no double newlines found
        if len(paragraphs) == 1:
            paragraphs = [p.strip() for p in cleaned_text.split("\n") if p.strip()]

        # Filter and score paragraphs for story quality
        scored_paragraphs = []
        for p in paragraphs:
            p_stripped = p.strip()
            score = score_story_paragraph(p_stripped, data.name, data.location, data.motto)
            if score > 0:  # Only include paragraphs with positive scores
                scored_paragraphs.append((score, p_stripped))

        if scored_paragraphs:

            # Sort by score and take the best
            scored_paragraphs.sort(reverse=True, key=lambda x: x[0])

            # Try to combine top paragraphs if they're complementary
            if len(scored_paragraphs) > 1 and scored_paragraphs[0][0] > 50:
                best_para = scored_paragraphs[0][1]
                # Check if second paragraph continues the story
                second_para = scored_paragraphs[1][1]
                # If second paragraph doesn't overlap much and is story-like, combine
                overlap = len(set(best_para.lower().split()) & set(second_para.lower().split()))
                if overlap < len(set(second_para.lower().split())) * 0.3:  # Less than 30% overlap
                    best_para = best_para + " " + second_para
            else:
                best_para = scored_paragraphs[0][1] if scored_paragraphs else None

            if best_para:
                # Clean up the story text
                story = clean_ocr_text(best_para)
                # Remove any remaining OCR artifacts
                story = re.sub(r"\s+", " ", story).strip()
                # Fix common OCR errors in story text (AFTER clean_ocr_text and whitespace normalization)
                story = fix_story_ocr_errors(story)
                # Final whitespace normalization (fix_story_ocr_errors may have introduced spaces)
                story = re.sub(r"\s+", " ", story).strip()
                # One final pass to fix any issues created by normalization
                story = re.sub(r"\brereserve\b", "reserve", story, flags=re.I)

                # Try to truncate at a reasonable stopping point if story is too long
                # Look for "Lord" as a potential stopping point (common in character stories)
                # Find the last occurrence of ". Lord" or "Lord" followed by end/punctuation
                story_lower = story.lower()

                # Look for ". Lord" pattern (most common - sentence ending with "Lord")
                lord_match = None
                # Try to find ". Lord" pattern
                for i in range(len(story) - 10, -1, -1):  # Search backwards
                    if story_lower[i : i + 6] == ". lord":
                        # Check if it's followed by end of string or space/newline
                        if i + 6 >= len(story) or story[i + 6] in [" ", "\n", "\t"]:
                            lord_match = i + 6  # Include ". Lord"
                            break

                # If not found, try just "Lord" at end
                if lord_match is None:
                    lord_pos = story_lower.rfind(" lord")
                    if lord_pos != -1:
                        # Check if it's near the end or followed by punctuation/end
                        if lord_pos + 5 >= len(story) - 10:  # Within last 10 chars
                            lord_match = lord_pos + 5  # Include " Lord"
                        elif lord_pos + 5 < len(story) and story[lord_pos + 5] in [
                            ".",
                            "!",
                            "?",
                            " ",
                        ]:
                            lord_match = lord_pos + 5

                if lord_match and lord_match > 200:  # Only truncate if reasonable length
                    truncated = story[:lord_match].strip()
                    # Ensure it ends properly
                    if not truncated.endswith((".", "!", "?")):
                        truncated += "."
                    story = truncated

                data.story = story

        return data

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_complete(self) -> bool:
        """Whether all required fields are present."""
        return bool(self.name and self.location and self.motto and self.story)


class BackCardData(BaseModel):
    """Parsed data from back card with parsing capabilities."""

    special_power: Optional[Power] = Field(default=None, description="Character's special power")
    common_powers: List[Power] = Field(default_factory=list, description="List of common powers")

    @staticmethod
    def _is_game_rules_line(line: str) -> bool:
        """Check if a line is a game rules section that should be skipped.

        Args:
            line: Line to check

        Returns:
            True if line should be skipped
        """
        return is_game_rules_line(line)

    @staticmethod
    def _detect_fueled_by_madness(lines: List[str], i: int) -> Optional[str]:
        """Detect 'Fueled by Madness' special power name.

        Args:
            lines: All lines from back card
            i: Current line index

        Returns:
            Power name if detected, None otherwise
        """
        line_lower = lines[i].lower()
        if "fueled" in line_lower and "madness" in line_lower:
            words = lines[i].split()
            power_words = []
            for word in words:
                if word[0].isupper() or word.lower() in ["by", "the"]:
                    power_words.append(word)
                elif power_words:
                    break
            if power_words:
                return " ".join(power_words)
        return None

    @staticmethod
    def _detect_healing_prayer(lines: List[str], i: int) -> Optional[str]:
        """Detect 'Healing Prayer' special power name.

        Args:
            lines: All lines from back card
            i: Current line index

        Returns:
            Power name if detected, None otherwise
        """
        line_lower = lines[i].lower()
        is_healing_pattern = ("healing" in line_lower and "prayer" in line_lower) or (
            ("at the end" in line_lower or "atthe end" in line_lower)
            and "turn" in line_lower
            and ("heal" in line_lower or "wound" in line_lower)
        )

        if is_healing_pattern:
            # Look backwards for power name
            power_name_candidates = []
            for j in range(max(0, i - 5), i):
                prev_line = lines[j].strip()
                prev_lower = prev_line.lower()
                if "healing" in prev_lower and "prayer" in prev_lower:
                    words = prev_line.split()
                    healing_idx = None
                    prayer_idx = None
                    for idx, word in enumerate(words):
                        if "healing" in word.lower():
                            healing_idx = idx
                        if "prayer" in word.lower():
                            prayer_idx = idx
                    if healing_idx is not None and prayer_idx is not None:
                        power_name_candidates.append(
                            " ".join(
                                words[
                                    min(healing_idx, prayer_idx) : max(healing_idx, prayer_idx) + 1
                                ]
                            )
                        )

            if power_name_candidates:
                return power_name_candidates[-1]
            return "Healing Prayer"
        return None

    @staticmethod
    def _detect_gain_sanity_pattern(lines: List[str], i: int, found_common_power: bool) -> Optional[str]:
        """Detect 'Fueled by Madness' pattern via gain/sanity keywords.

        Args:
            lines: All lines from back card
            i: Current line index
            found_common_power: Whether we've already found a common power

        Returns:
            Power name if detected, None otherwise
        """
        if found_common_power:
            return None

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

        line_lower = lines[i].lower()
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

        if has_gain and has_sanity:
            return "Fueled by Madness"
        return None

    @staticmethod
    def _extract_power_name_from_context(
        lines: List[str], i: int, found_common_power: bool
    ) -> Optional[str]:
        """Extract power name by looking backwards in context.

        Args:
            lines: All lines from back card
            i: Current line index
            found_common_power: Whether we've already found a common power

        Returns:
            Power name if found, None otherwise
        """
        if found_common_power:
            return None

        line_lower = lines[i].lower()
        action_patterns = [
            "when you run",
            "when attacking",
            "when you attack",
            "when attacked",
            "during a run",
            "you may",
            "deal",
            "wound",
            "heal",
            "stress",
            "move",
            "additional",
            "sneak",
            "free",
            "reroll",
        ]

        has_action_pattern = any(pattern in line_lower for pattern in action_patterns)
        has_level_indicator = bool(re.search(r"^(?:level\s*)?[1234][:\-]?\s*", line_lower))

        # Check if next few lines also look like power descriptions
        looks_like_power_sequence = False
        if has_action_pattern or has_level_indicator:
            continuation_count = 0
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].lower() if j < len(lines) else ""
                if any(pattern in next_line for pattern in POWER_ACTION_PATTERNS):
                    continuation_count += 1
                if re.search(r"^(?:level\s*)?[1234][:\-]?\s*", next_line):
                    continuation_count += 1
                if next_line.startswith("instead"):
                    continuation_count += 1

            looks_like_power_sequence = continuation_count >= 1

        if not (has_action_pattern or has_level_indicator) or not looks_like_power_sequence:
            return None

        # Look backwards for power name
        power_name_candidates = []
        for j in range(max(0, i - 5), i):
            prev_line = lines[j].strip()
            prev_lower = prev_line.lower()

            # Skip game rules
            if any(
                skip in prev_lower
                for skip in [
                    "your turn",
                    "take",
                    "draw",
                    "investigate",
                    "fight",
                    "resolve",
                    "mythos",
                    "card",
                    "actions",
                    "safe space",
                ]
            ):
                continue

            # Skip quotes/mottos
            is_quote = (
                prev_line.startswith('"')
                or prev_line.startswith("'")
                or prev_line.endswith('"')
                or prev_line.endswith("'")
                or "certain" in prev_lower
                or "life" in prev_lower
                or "things" in prev_lower
            )

            if is_quote:
                continue

            # Check if previous line looks like a title/name
            word_count = len(prev_line.split())
            if (
                word_count >= 1
                and word_count <= 4
                and prev_line[0].isupper()
                and not any(
                    cp.value.upper() in prev_line.upper() for cp in CommonPowerEnum
                )
                and not prev_line.endswith(".")
                and not prev_line.endswith(",")
                and not prev_line.endswith(":")
            ):
                power_name_candidates.append(prev_line)

        if power_name_candidates:
            return power_name_candidates[-1]

        # Generate name based on first action words
        first_words = line_lower.split()[:5]
        if "run" in first_words or "move" in first_words:
            return "Movement Power"
        elif "attack" in first_words or "wound" in first_words or "deal" in first_words:
            return "Combat Power"
        elif "heal" in first_words or "stress" in first_words:
            return "Healing Power"
        elif "sneak" in first_words:
            return "Stealth Power"
        elif "reroll" in first_words:
            return "Reroll Power"
        else:
            # Use first capitalized words from the line
            words = lines[i].split()
            name_words = []
            for word in words[:3]:
                if word[0].isupper() and len(word) > 2:
                    name_words.append(word)
                elif name_words:
                    break
            if name_words:
                return " ".join(name_words)
            return "Special Power"

    @staticmethod
    def _find_missed_common_powers(data: "BackCardData", text: str) -> None:
        """Scan entire text for any common power names we might have missed.

        This is a fallback to catch powers that weren't detected line-by-line.
        Only looks for power names that appear as standalone lines or short lines,
        not embedded in descriptions.

        Args:
            data: BackCardData instance to update
            text: Full cleaned text from back card
        """
        import re

        found_power_names = {cp.name for cp in data.common_powers}
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Check each common power name
        for common_power in CommonPowerEnum:
            power_name = common_power.value
            power_upper = power_name.upper()

            # Skip if we already found this power
            if power_name in found_power_names:
                continue

            # Look for power name as a standalone line or very short line (likely a power header)
            for line in lines:
                line_upper = line.upper().strip()
                line_len = len(line.strip())

                # Skip lines that look like descriptions
                if is_common_power_description_line(line):
                    continue

                # Check for exact match on short lines
                if line_upper == power_upper:
                    if not any(cp.name == power_name for cp in data.common_powers):
                        data.common_powers.append(
                            Power(name=power_name, is_special=False, levels=[])
                        )
                    break

                # Check if power name appears as a word in short lines
                pattern = r"\b" + re.escape(power_upper) + r"\b"
                if re.search(pattern, line_upper) and line_len <= len(power_upper) + 10:
                    # Line is close to power name length (allow small OCR errors)
                    if not any(cp.name == power_name for cp in data.common_powers):
                        data.common_powers.append(
                            Power(name=power_name, is_special=False, levels=[])
                        )
                    break

                # Try fuzzy matching on short lines only
                try:
                    from rapidfuzz import fuzz

                    ratio = fuzz.ratio(line_upper, power_upper)
                    if ratio >= COMMON_POWER_FUZZY_THRESHOLD and line_len <= len(power_upper) + COMMON_POWER_LENGTH_TOLERANCE:
                        # High similarity and similar length
                        if not any(cp.name == power_name for cp in data.common_powers):
                            data.common_powers.append(
                                Power(name=power_name, is_special=False, levels=[])
                            )
                        break
                except ImportError:
                    pass

    @staticmethod
    def _detect_common_power(line: str) -> Optional[str]:
        """Detect if a line contains a common power name.

        Args:
            line: Line to check

        Returns:
            Common power name if found, None otherwise
        """
        import re

        line_upper = line.upper()

        # First try exact match (check if power name is in the line or line equals power name)
        for common_power in CommonPowerEnum:
            power_name = common_power.value
            power_upper = power_name.upper()

            # Exact match
            if line_upper == power_upper:
                return power_name
            # Power name appears as a word in the line
            pattern = r"\b" + re.escape(power_upper) + r"\b"
            if re.search(pattern, line_upper):
                return power_name
            # Power name is contained in line (for OCR errors)
            if power_upper in line_upper and len(line_upper) <= len(power_upper) + COMMON_POWER_LENGTH_TOLERANCE:
                # Line is close to power name length (allow small OCR errors)
                return power_name

        # Try fuzzy matching for OCR errors
        try:
            from rapidfuzz import fuzz

            best_match = None
            best_ratio = 0.0
            line_clean = line.strip().upper()

            for common_power in CommonPowerEnum:
                power_name = common_power.value
                ratio1 = fuzz.ratio(line_clean, power_name.upper())
                ratio2 = fuzz.partial_ratio(line_clean, power_name.upper())
                ratio3 = fuzz.token_sort_ratio(line_clean, power_name.upper())

                ratio = max(ratio1, ratio2, ratio3)

                # Lower threshold to 60% to catch more OCR errors
                if ratio > best_ratio and ratio >= 60.0:
                    best_ratio = ratio
                    best_match = power_name

            return best_match
        except ImportError:
            return None

    @staticmethod
    def _process_level_indicator(
        current_power: Power, power_content_lines: List[str], line: str, line_lower: str
    ) -> Tuple[List[str], bool]:
        """Process a line with a level indicator (Level 1, Level 2, etc.).

        Args:
            current_power: Current power being processed
            power_content_lines: Accumulated content lines for current level
            line: Current line
            line_lower: Lowercase version of current line

        Returns:
            Tuple of (updated power_content_lines, whether level was processed)
        """
        level_match = re.search(r"^(?:level\s*)?(\d+)[:\-]?\s*", line_lower)
        if not level_match:
            return power_content_lines, False

        # Save previous level if we have accumulated content
        if power_content_lines:
            level_num = min(len(current_power.levels) + 1, MAX_POWER_LEVELS)
            description = " ".join(power_content_lines).strip()
            if description and len(description.split()) > MIN_POWER_DESCRIPTION_WORDS:
                # Only add if we don't already have this level and haven't exceeded max
                if level_num not in [lev.level for lev in current_power.levels] and len(current_power.levels) < MAX_POWER_LEVELS:
                    current_power.add_level_from_text(level_num, description)

        # Start new level (cap at max, OCR might extract invalid numbers)
        extracted_level = int(level_match.group(1))
        level_num = min(max(extracted_level, 1), MAX_POWER_LEVELS)
        description = re.sub(r"^(?:level\s*)?\d+[:\-]?\s*", "", line, flags=re.I).strip()
        if description:
            return [description], True
        return [], True

    @staticmethod
    def _process_instead_indicator(
        current_power: Power, power_content_lines: List[str], line: str, line_lower: str
    ) -> Tuple[List[str], bool]:
        """Process a line starting with 'Instead' (indicates new level).

        Args:
            current_power: Current power being processed
            power_content_lines: Accumulated content lines for current level
            line: Current line
            line_lower: Lowercase version of current line

        Returns:
            Tuple of (updated power_content_lines, whether instead was processed)
        """
        is_instead = line_lower.strip().startswith("instead")
        if not is_instead:
            return power_content_lines, False

        # Save previous level if we have accumulated content
        if power_content_lines and current_power.levels:
            prev_level_num = min(len(current_power.levels), MAX_POWER_LEVELS)
            description = " ".join(power_content_lines).strip()
            if description and len(description.split()) > 2:
                # Only add if we don't already have this level
                if prev_level_num not in [lev.level for lev in current_power.levels]:
                    current_power.add_level_from_text(prev_level_num, description)

        # Start new level
        description = re.sub(r"^instead[,\s]*", "", line, flags=re.I).strip()
        if description:
            return [description], True
        return [], True

    @staticmethod
    def _process_power_content_line(
        current_power: Power,
        power_content_lines: List[str],
        line: str,
        line_lower: str,
        line_upper: str,
        lines: List[str],
        i: int,
    ) -> List[str]:
        """Process a line that's part of power content (description continuation).

        Args:
            current_power: Current power being processed
            power_content_lines: Accumulated content lines
            line: Current line
            line_lower: Lowercase version of line
            line_upper: Uppercase version of line
            lines: All lines
            i: Current line index

        Returns:
            Updated power_content_lines
        """
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
            and line_upper not in [cp.value.upper() for cp in CommonPowerEnum]
        )

        # Check if this is a continuation of the current description
        is_continuation = (
            len(line.split()) <= 8
            and not line[0].isupper()
            and power_content_lines
            and not any(cp.value.upper() in line_upper for cp in CommonPowerEnum)
        )

        if is_description or is_continuation:
            power_content_lines.append(line)
        elif power_content_lines:
            # Check if next line is a new power
            next_is_power = False
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_upper = next_line.upper()
                if any(
                    cp.value.upper() in next_upper or next_upper == cp.value.upper()
                    for cp in CommonPowerEnum
                ):
                    next_is_power = True

            # Save accumulated level if we have enough content
            max_levels = 4
            if len(current_power.levels) < max_levels and not next_is_power:
                level_num = min(len(current_power.levels) + 1, MAX_POWER_LEVELS)
                description = " ".join(power_content_lines).strip()
                if description and len(description.split()) > 2:
                    # Only add if we don't already have this level
                    if level_num not in [lev.level for lev in current_power.levels]:
                        current_power.add_level_from_text(level_num, description)
                return []

        return power_content_lines

    @classmethod
    def parse_from_text(cls, text: str) -> "BackCardData":
        """Parse back card text to extract powers and their levels."""
        from scripts.core.parsing.text import clean_ocr_text

        # Clean the text first, preserving newlines for line-by-line parsing
        cleaned_text = clean_ocr_text(text, preserve_newlines=True)
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]

        data = cls()
        current_power: Optional[Power] = None
        power_content_lines: List[str] = []
        found_common_power = False

        i = 0
        while i < len(lines):
            line = lines[i]
            line_lower = line.lower()
            line_upper = line.upper()

            # Skip game rules sections
            if is_game_rules_line(line):
                i += 1
                continue

            # Detect special power names (try multiple strategies)
            special_power_name = None
            is_special_power = False

            # Strategy 1: Explicit "Fueled by Madness"
            special_power_name = cls._detect_fueled_by_madness(lines, i)
            if special_power_name:
                is_special_power = True

            # Strategy 2: "Healing Prayer" pattern
            if not is_special_power:
                special_power_name = cls._detect_healing_prayer(lines, i)
                if special_power_name:
                    is_special_power = True

            # Strategy 3: Gain/sanity pattern (Fueled by Madness)
            if not is_special_power:
                special_power_name = cls._detect_gain_sanity_pattern(lines, i, found_common_power)
                if special_power_name:
                    is_special_power = True

            # Strategy 4: Extract from context (action-based patterns)
            if not is_special_power:
                special_power_name = cls._extract_power_name_from_context(lines, i, found_common_power)
                if special_power_name:
                    is_special_power = True

            # Detect common power names
            common_power_name = cls._detect_common_power(line)
            is_common_power = common_power_name is not None
            if is_common_power:
                found_common_power = True

            # Handle power name detection
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
                        # Only add if we don't already have this common power
                        if not any(cp.name == current_power.name for cp in data.common_powers):
                            data.common_powers.append(current_power)

                # Check if we already have this common power (avoid duplicates)
                if any(cp.name == common_power_name for cp in data.common_powers):
                    # Skip duplicate, but continue processing content for the existing power
                    current_power = None
                    power_content_lines = []
                    i += 1
                    continue

                # Start tracking common power
                current_power = Power(name=common_power_name, is_special=False, levels=[])
                power_content_lines = []
                i += 1
                continue

            # Process power content and levels
            if current_power:
                # Try processing level indicator
                updated_lines, processed = cls._process_level_indicator(
                    current_power, power_content_lines, line, line_lower
                )
                if processed:
                    power_content_lines = updated_lines
                    i += 1
                    continue

                # Try processing "Instead" indicator
                updated_lines, processed = cls._process_instead_indicator(
                    current_power, power_content_lines, line, line_lower
                )
                if processed:
                    power_content_lines = updated_lines
                    i += 1
                    continue

                # Handle special power "Instead" in middle of line
                if current_power.is_special:
                    instead_match = re.search(r"^[^a-z]*instead[,\s]+", line_lower)
                    if instead_match and current_power.levels:
                        if power_content_lines:
                            prev_level_num = len(current_power.levels)
                            description = " ".join(power_content_lines).strip()
                            if description and len(description.split()) > 2:
                                current_power.add_level_from_text(prev_level_num, description)
                            power_content_lines = []

                        description = re.sub(
                            r"^[^a-z]*instead[,\s]+", "", line, flags=re.I
                        ).strip()
                        if description:
                            power_content_lines = [description]
                        i += 1
                        continue

                # Process content line
                power_content_lines = cls._process_power_content_line(
                    current_power, power_content_lines, line, line_lower, line_upper, lines, i
                )

            i += 1

        # Finalize last power
        cls._finalize_power(current_power, power_content_lines, data, cleaned_text, lines)

        return data

    @staticmethod
    def _finalize_power(
        current_power: Optional[Power],
        power_content_lines: List[str],
        data: "BackCardData",
        cleaned_text: str,
        lines: List[str],
    ) -> None:
        """Finalize the last power being processed.

        Args:
            current_power: Current power being processed (may be None)
            power_content_lines: Accumulated content lines
            data: BackCardData instance to update
            cleaned_text: Full cleaned text for post-processing
            lines: All lines for post-processing
        """
        if not current_power:
            return

        # Save any remaining accumulated level content
        if power_content_lines and len(current_power.levels) < MAX_POWER_LEVELS:
            level_num = min(len(current_power.levels) + 1, MAX_POWER_LEVELS)
            description = " ".join(power_content_lines).strip()
            if description and len(description.split()) > MIN_POWER_DESCRIPTION_WORDS:
                # Only add if we don't already have this level
                if level_num not in [lev.level for lev in current_power.levels]:
                    current_power.add_level_from_text(level_num, description)

        # For special powers, ensure we have 4 levels by checking if descriptions contain "Instead"
        if current_power.is_special and len(current_power.levels) < MAX_POWER_LEVELS:
            # Strategy 1: Check if any level description contains multiple "Instead" markers
            for level in current_power.levels:
                desc = level.description
                # Count "Instead" occurrences (case-insensitive, handle OCR errors)
                instead_patterns = [
                    r"\binstead\b",
                    r"\binstea\b",  # OCR error
                    r"\binste\b",  # OCR error
                    r"\binstea\s+",  # OCR error with space
                ]
                instead_count = 0
                for pattern in instead_patterns:
                    instead_count += len(re.findall(pattern, desc, re.I))

                if instead_count > 1 and len(current_power.levels) < MAX_POWER_LEVELS:
                    # Try to split on "Instead" (and variants) to create additional levels
                    split_patterns = [
                        r"\s+instead[,\s]+",
                        r"\s+instea[,\s]+",
                        r"\s+inste[,\s]+",
                        r"[,\s]+instead[,\s]+",
                    ]
                    parts = None
                    for split_pattern in split_patterns:
                        parts = re.split(split_pattern, desc, flags=re.I)
                        if len(parts) > 1:
                            break

                    if parts and len(parts) > 1:
                        # Update current level with first part
                        level.description = parts[0].strip()
                        # Add remaining parts as new levels (but don't exceed 4 levels total)
                        for part in parts[1:]:
                            part_clean = part.strip()
                            if (
                                part_clean
                                and len(part_clean.split()) > 2
                                and len(current_power.levels) < MAX_POWER_LEVELS
                            ):
                                # Ensure we don't exceed max levels
                                new_level_num = min(len(current_power.levels) + 1, MAX_POWER_LEVELS)
                                # Only add if we don't already have this level
                                if new_level_num not in [lev.level for lev in current_power.levels]:
                                    current_power.add_level_from_text(new_level_num, part_clean)

            # Strategy 2: If still missing levels, try to extract from the full text
            # Look for patterns like "Level 1:", "Level 2:", etc. in the original text
            if len(current_power.levels) < MAX_POWER_LEVELS:
                # Re-scan the cleaned text for explicit level markers
                level_markers = re.finditer(
                    r"(?:level\s*)?([1234])[:\-]?\s*([^0-9]+?)(?=(?:level\s*)?[1234][:\-]|\Z)",
                    cleaned_text,
                    re.IGNORECASE | re.DOTALL,
                )

                found_levels = {}
                for match in level_markers:
                    level_num = int(match.group(1))
                    level_desc = match.group(2).strip()
                    # Clean up the description
                    level_desc = re.sub(
                        r"^\s*instead[,\s]+", "", level_desc, flags=re.I
                    ).strip()
                    if level_desc and len(level_desc.split()) > 2:
                        found_levels[level_num] = level_desc

                # Add missing levels if we found them
                for level_num in range(1, MAX_POWER_LEVELS + 1):
                    if (
                        level_num not in [level.level for level in current_power.levels]
                        and level_num in found_levels
                    ):
                        current_power.add_level_from_text(level_num, found_levels[level_num])

            # Strategy 3: If still missing, try to infer from "Instead" patterns in full text
            if len(current_power.levels) < MAX_POWER_LEVELS:
                # Find all "Instead" occurrences in the text after the power name
                instead_matches = list(
                    re.finditer(
                        r"\b(?:instead|instea|inste)[,\s]+([^\.]+?)(?=\b(?:instead|instea|inste)[,\s]|\b(?:level\s*)?[1234][:\-]|\Z)",
                        cleaned_text,
                        re.IGNORECASE | re.DOTALL,
                    )
                )

                # If we found multiple "Instead" patterns, they might be separate levels
            # Only process up to MAX_POWER_LEVELS total
            if len(instead_matches) >= len(current_power.levels):
                # Try to map them to levels
                for idx, match in enumerate(instead_matches):
                    level_num = min(idx + 1, MAX_POWER_LEVELS)
                    if (
                        level_num not in [level.level for level in current_power.levels]
                        and len(current_power.levels) < MAX_POWER_LEVELS
                    ):
                        desc = match.group(1).strip()
                        if desc and len(desc.split()) > MIN_POWER_DESCRIPTION_WORDS:
                            current_power.add_level_from_text(level_num, desc)

        if current_power:
            if current_power.is_special:
                data.special_power = current_power
            else:
                # Only add if we don't already have this common power (avoid duplicates)
                if not any(cp.name == current_power.name for cp in data.common_powers):
                    data.common_powers.append(current_power)

        # Post-process: scan entire text for any missed common power names
        BackCardData._find_missed_common_powers(data, cleaned_text)

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
            for line_idx, line in enumerate(lines):
                line_lower = line.lower()
                # Check if this line has gain pattern
                has_gain = any(g in line_lower for g in gain_patterns)
                has_sanity = any(s in line_lower for s in sanity_patterns)

                # Also check surrounding lines for multi-line patterns
                if has_gain and not has_sanity and line_idx + 1 < len(lines):
                    for j in range(line_idx + 1, min(line_idx + 4, len(lines))):
                        if any(s in lines[j].lower() for s in sanity_patterns):
                            has_sanity = True
                            break

                if has_gain and has_sanity:
                    # Collect multi-line description
                    desc_lines = [line.strip()]
                    # Look ahead for continuation (up to 3 more lines)
                    for j in range(line_idx + 1, min(line_idx + 4, len(lines))):
                        next_line = lines[j].strip()
                        # Skip empty lines and common power names
                        if not next_line or any(
                            cp.value.upper() in next_line.upper() for cp in CommonPowerEnum
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

    @computed_field  # type: ignore[prop-decorator]
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
        # For motto, prefer the longer/more complete one (likely the extracted one)
        motto_to_use = None
        if prefer_html and other.motto:
            motto_to_use = other.motto
        elif self.motto and other.motto:
            # Prefer the longer motto (more complete)
            motto_to_use = other.motto if len(other.motto) > len(self.motto) else self.motto
        else:
            motto_to_use = self.motto or other.motto

        # For story, prefer extracted story (other.story) if it exists and prefer_html is True
        # Otherwise prefer existing story if it exists, then extracted story
        story_to_use = None
        if prefer_html and other.story:
            story_to_use = other.story
        elif self.story and other.story:
            # If both exist, prefer the longer/more complete one (likely the extracted one with corrections)
            story_to_use = other.story if len(other.story) > len(self.story) else self.story
        else:
            story_to_use = self.story or other.story

        merged = CharacterData(
            name=other.name if prefer_html else (self.name or other.name),
            location=self.location or other.location,
            motto=motto_to_use,
            story=story_to_use,
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
        elif len(self.common_powers) != 2:
            issues.append(f"Found {len(self.common_powers)} common power(s), expected exactly 2")

        return issues

    def has_common_power(self, power: CommonPowerEnum) -> bool:
        """Check if character has a specific common power."""
        return power.value in self.common_powers

    def get_common_power_names(self) -> List[str]:
        """Get list of common power names."""
        return self.common_powers.copy()


class CommonPowerLevelData(BaseModel):
    """Represents a power level from common_powers.json with statistics."""

    level: int = Field(..., ge=1, le=4, description="Power level (1-4)")
    description: str = Field(..., description="Power level description")
    statistics: PowerLevelStatistics = Field(
        ..., description="Statistical analysis of this power level"
    )
    effect: str = Field(..., description="Summary of what this power level does")


class CommonPower(BaseModel):
    """Represents a common power with all its levels."""

    name: str = Field(..., description="Name of the common power")
    is_special: bool = Field(
        default=False, description="Whether this is a special power (vs common)"
    )
    levels: List[CommonPowerLevelData] = Field(
        default_factory=list, description="Power levels (1-4)"
    )

    @classmethod
    def from_dict(cls, data: dict) -> "CommonPower":
        """Create CommonPower from dictionary (e.g., from JSON)."""
        levels = [
            CommonPowerLevelData(
                level=level_dict["level"],
                description=level_dict["description"],
                statistics=PowerLevelStatistics(**level_dict.get("statistics", {})),
                effect=level_dict.get("effect", ""),
            )
            for level_dict in data.get("levels", [])
        ]
        return cls(
            name=data["name"],
            is_special=data.get("is_special", False),
            levels=levels,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "is_special": self.is_special,
            "levels": [level.model_dump() for level in self.levels],
        }
