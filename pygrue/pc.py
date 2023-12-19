from __future__ import annotations
from collections import defaultdict
import enum
import json
import math
import pathlib

from .dice import Advantage, Dice
from .environment import Lighting


class Ability(enum.Enum):
    STRENGTH = enum.auto()
    DEXTERITY = enum.auto()
    CONSTITUTION = enum.auto()
    INTELLIGENCE = enum.auto()
    WISDOM = enum.auto()
    CHARISMA = enum.auto()

    @staticmethod
    def from_str(source: str) -> Ability:
        for value in Ability:
            if value.name == source.upper():
                return value
        raise ValueError(f"Cannot interpret {source} as Ability")


class Proficiency(enum.Enum):
    INSIGHT = enum.auto()
    INVESTIGATION = enum.auto()
    PERCEPTION = enum.auto()

    @staticmethod
    def from_str(source: str) -> Proficiency:
        for value in Proficiency:
            if value.name == source.upper():
                return value
        raise ValueError(f"Cannot interpret {source} as Proficiency")


class ProficiencyLevel(enum.IntEnum):
    NONE = 0
    PROFICIENCY = 1
    EXPERTISE = 2


class PC:
    __slots__ = {
        "abilities": "A `dict` between `Ability`s and modifiers",
        "name": "The character name",
        "proficiencies": "A `defaultdict` between `Proficiency`s and `ProficiencyLevel`s (default 0)",
        "proficiency_bonus": "The integer proficiency bonus the character uses",
        "darkvision": "`True` if the character has darkvision, false otherwise",
    }

    def __init__(self, character_sheet: pathlib.Path):
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

            self.proficiency_bonus = data["proficiency_bonus"]
            self.darkvision = data["darkvision"]

        assert all(a in self.abilities for a in Ability), f"Not all abilities populated for {self.name}"

    @staticmethod
    def _modifier_from_score(score: int) -> int:
        diff = score - 10
        return math.floor(diff / 2)

    def check(self,
              ability: Ability,
              proficiency: Proficiency | None = None,
              advantage: Advantage = Advantage.NONE) -> int:
        roll = Dice.d(20)
        roll.modify(self.abilities[ability] + self.proficiencies[proficiency] * self.proficiency_bonus)
        result = roll.apply(advantage)
        return result

    def with_lighting(self, lighting: Lighting) -> Advantage:
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
        total_advantage = advantage + self.with_lighting(lighting)
        return self.check(ability, proficiency, total_advantage)
