from __future__ import annotations
from collections import defaultdict
import enum
import json
import math
import pathlib

from .dice import Advantage, Dice
from .environment import Lighting


class Ability(enum.Enum):
    """
    Enumerated ability scores.
    """
    STRENGTH = enum.auto()
    DEXTERITY = enum.auto()
    CONSTITUTION = enum.auto()
    INTELLIGENCE = enum.auto()
    WISDOM = enum.auto()
    CHARISMA = enum.auto()

    @staticmethod
    def from_str(source: str) -> Ability:
        """
        Convert a string to an `Ability` enum. Returns the appropriate enum
        value for the source string, where the string must be the full name
        of the ability, case insensitive.

        :params source: The string to convert
        """
        for value in Ability:
            if value.name == source.upper():
                return value
        raise ValueError(f"Cannot interpret {source} as Ability")


class Proficiency(enum.Enum):
    """
    Enumerated possible proficienies.
    """
    INSIGHT = enum.auto()
    INVESTIGATION = enum.auto()
    PERCEPTION = enum.auto()
    STEALTH = enum.auto()

    @staticmethod
    def from_str(source: str) -> Proficiency:
        """
        Convert a string to a `Proficiency` enum. Returns the appropriate enum
        value for the source string, where the string must be the full name
        of the proficiency, case insensitive.

        :params source: The string to convert
        """
        for value in Proficiency:
            if value.name == source.upper():
                return value
        raise ValueError(f"Cannot interpret {source} as Proficiency")

    def sight_affected(self) -> bool:
        """
        Returns true if rolls using this proficiency can be affected by line of
        sight and lighting conditions.
        """
        return self in [
            Proficiency.INSIGHT,
            Proficiency.INVESTIGATION,
            Proficiency.PERCEPTION,
        ]


class ProficiencyLevel(enum.IntEnum):
    """
    Proficiency levels, as an integer. Multiplying this value by a character's
    proficiency bonus will result in the correct modifier for the given
    proficiency.
    """
    NONE = 0
    PROFICIENCY = 1
    EXPERTISE = 2


class PC:
    """
    A character with all relevant attributes for calculating behind-the-screen
    ability checks.
    """
    __slots__ = {
        "abilities": "A `dict` between `Ability`s and modifiers",
        "name": "The character name",
        "proficiencies": "A `defaultdict` between `Proficiency`s and `ProficiencyLevel`s (default 0)",
        "proficiency_advantages": "A `defaultdict` between `Proficiency`s and `Advantage`s (default `NONE`)",
        "proficiency_bonus": "The integer proficiency bonus the character uses",
        "darkvision": "`True` if the character has darkvision, false otherwise",
    }

    def __init__(self, character_sheet: pathlib.Path):
        """
        :params character_sheet: A path to a JSON-encoded character sheet
        """
        with open(character_sheet, 'r') as sheet:
            data = json.load(sheet)
            self.name = data["name"]

            self.abilities = {
                Ability.from_str(name): PC._modifier_from_score(value)
                for name, value in data["abilities"].items()
            }

            self.proficiencies = defaultdict(lambda: 0)
            for name, value in data["proficiencies"].items():
                self.proficiencies[Proficiency.from_str(name)] = ProficiencyLevel(value)

            self.proficiency_advantages = defaultdict(lambda: Advantage.NONE)
            for name, value in data["proficiency_advantages"].items():
                match value:
                    case 0:
                        self.proficiency_advantages[Proficiency.from_str(name)] = Advantage.NONE
                    case 1:
                        self.proficiency_advantages[Proficiency.from_str(name)] = Advantage.ADVANTAGE
                    case -1:
                        self.proficiency_advantages[Proficiency.from_str(name)] = Advantage.DISADVANTAGE
                    case _:
                        raise ValueError(f"Proficiency advantages must be from -1, 0, or 1, not {value}")

            self.proficiency_bonus = data["proficiency_bonus"]
            self.darkvision = data["darkvision"]

        assert all(a in self.abilities for a in Ability), f"Not all abilities populated for {self.name}"

    @staticmethod
    def _modifier_from_score(score: int) -> int:
        """
        Convert an ability score to the corresponding modifier
        (i.e. 8 -> -1, 11 -> 1, etc.)

        :params score: The ability score (usually from 1-20)
        """
        diff = score - 10
        return math.floor(diff / 2)

    def check(self,
              ability: Ability,
              proficiency: Proficiency | None = None,
              advantage: Advantage = Advantage.NONE) -> int:
        """
        Perform an ability check, with optional proficiency and advantage
        modifiers.

        :params ability: The ability to use for the check
        :params proficiency: A proficiency to apply to the check (by default, no proficiency applies)
        :params advantage: The advantage state to apply to the check
        """
        roll = Dice.d(20)
        roll.modify(self.abilities[ability] + self.proficiencies[proficiency] * self.proficiency_bonus)
        total_advantage = self.proficiency_advantages[proficiency] + advantage
        result = roll.apply(total_advantage)
        return result

    def with_lighting(self, lighting: Lighting) -> Advantage:
        """
        Return the advantage state of the character's sight-based checks under
        the given lighting condition, based on the character's darkvision.

        :params lighting: The lighting condition under which to sense
        """
        if lighting is Lighting.BRIGHT:
            return Advantage.NONE
        elif lighting is Lighting.DIM:
            return Advantage.NONE if self.darkvision else Advantage.DISADVANTAGE
        elif lighting is Lighting.DARK:
            return Advantage.DISADVANTAGE if self.darkvision else Advantage.FAIL
        else:
            raise NotImplementedError(f"Lighting type {lighting.name} not supported.")

    def sight_based_check(self,
                          ability: Ability,
                          lighting: Lighting,
                          proficiency: Proficiency | None = None,
                          advantage: Advantage = Advantage.NONE) -> int:
        """
        Perform an ability check, with optional proficiency and advantage
        modifiers, applying the intrinsic advantage state the results from
        the lighting conditions and the character's darkvision.

        :params ability: The ability to use for the check
        :params lighting: The lighting conditions under which the check is made
        :params proficiency: A proficiency to apply to the check, before lighting conditions (by default, none)
        :params advantage: The advantage state to apply to the check
        """
        total_advantage = advantage + self.with_lighting(lighting)
        return self.check(ability, proficiency, total_advantage)
