#!/usr/bin/env python3
"""
Character Pool Models

Models for managing pools of characters from different seasons.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from scripts.models.character import CharacterData
from scripts.models.character_build import CharacterBuild
from scripts.models.constants import Season

if TYPE_CHECKING:
    from scripts.models.character import CommonPower


class CharacterPool(BaseModel):
    """Represents a pool of characters from specified seasons."""

    season_filters: List[Season] = Field(
        default_factory=list, description="Seasons included in this pool"
    )
    characters: List[CharacterBuild] = Field(
        default_factory=list, description="Character builds in this pool"
    )
    data_dir: Path = Field(default=Path("data"), description="Data directory path")

    @computed_field
    @property
    def character_count(self) -> int:
        """Number of characters in the pool."""
        return len(self.characters)

    @computed_field
    @property
    def character_names(self) -> List[str]:
        """List of character names in the pool."""
        return [char.character_name for char in self.characters]

    def get_character(self, name: str) -> Optional[CharacterBuild]:
        """Get a character build by name."""
        for char in self.characters:
            if char.character_name.lower() == name.lower():
                return char
        return None

    @classmethod
    def from_seasons(
        cls,
        seasons: List[Season],
        data_dir: Path = Path("data"),
        power_data: Optional[Dict[str, "CommonPower"]] = None,
    ) -> "CharacterPool":
        """Create CharacterPool from list of seasons.

        Args:
            seasons: List of seasons to include
            data_dir: Root data directory
            power_data: Dictionary mapping power names to CommonPower objects

        Returns:
            CharacterPool with all characters from specified seasons
        """
        pool = cls(season_filters=seasons, data_dir=data_dir)
        pool.load_characters_from_seasons(seasons, power_data)
        return pool

    def load_characters_from_seasons(
        self,
        seasons: List[Season],
        power_data: Optional[Dict[str, "CommonPower"]] = None,
    ) -> None:
        """Load all characters from specified seasons.

        Args:
            seasons: List of seasons to load
            power_data: Dictionary mapping power names to CommonPower objects
        """

        # Load power data if not provided
        if power_data is None:
            power_data = self._load_common_powers()

        # Load characters from each season
        for season in seasons:
            season_dir = self.data_dir / season.value
            if not season_dir.exists():
                continue

            # Find all character directories
            for char_dir in season_dir.iterdir():
                if not char_dir.is_dir():
                    continue

                # Skip non-character directories
                if char_dir.name in ["character-book.pdf", ".git", "__pycache__"]:
                    continue

                # Load character data
                char_data = self._load_character_data(char_dir)
                if char_data is None:
                    continue

                # Create character build (default levels)
                build = CharacterBuild.from_character_data(
                    char_data,
                    special_power_level=1,
                    common_power_1_level=1,
                    common_power_2_level=1,
                    power_data=power_data,
                )

                self.characters.append(build)

    def _load_character_data(self, char_dir: Path) -> Optional[CharacterData]:
        """Load character data from JSON file."""
        json_file = char_dir / "character.json"
        if not json_file.exists():
            return None

        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            return CharacterData(**data)
        except Exception:
            return None

    def _load_common_powers(self) -> Dict[str, "CommonPower"]:
        """Load common powers from JSON file."""
        from scripts.models.character import CommonPower as CommonPowerModel

        common_powers_file = self.data_dir / "common_powers.json"
        if not common_powers_file.exists():
            return {}

        try:
            with open(common_powers_file, encoding="utf-8") as f:
                data = json.load(f)

            return {
                power_dict["name"]: CommonPowerModel.from_dict(power_dict) for power_dict in data
            }
        except Exception:
            return {}

    def filter_by_season(self, season: Season) -> "CharacterPool":
        """Create a new pool filtered by season."""
        filtered = CharacterPool(
            season_filters=[season],
            data_dir=self.data_dir,
        )
        filtered.characters = [
            char for char in self.characters if self._get_character_season(char) == season
        ]
        return filtered

    def _get_character_season(self, character: CharacterBuild) -> Optional[Season]:
        """Determine which season a character belongs to."""
        # Check each season directory
        for season in Season:
            season_dir = self.data_dir / season.value
            char_dir = season_dir / character.character_name.lower()
            if char_dir.exists():
                return season
        return None
