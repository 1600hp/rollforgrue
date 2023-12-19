from __future__ import annotations
import enum
import random
from typing import Iterable

class Advantage(enum.Enum):
    NONE = enum.auto()
    ADVANTAGE = enum.auto()
    DISADVANTAGE = enum.auto()
    CANCELLED = enum.auto()
    FAIL = enum.auto()

    def __add__(self, other: Advantage) -> Advantage:
        if not isinstance(other, Advantage):
            raise NotImplementedError()

        if self is Advantage.NONE:
            return other
        elif self is Advantage.ADVANTAGE:
            if other is Advantage.NONE:
                return self
            elif other is Advantage.ADVANTAGE:
                return self
            elif other is Advantage.DISADVANTAGE:
                return Advantage.CANCELLED
            elif other is Advantage.CANCELLED:
                return other
            elif other is Advantage.FAIL:
                return other
            else:
                pass
        elif self is Advantage.DISADVANTAGE:
            if other is Advantage.NONE:
                return self
            elif other is Advantage.ADVANTAGE:
                return Advantage.CANCELLED
            elif other is Advantage.DISADVANTAGE:
                return self
            elif other is Advantage.CANCELLED:
                return other
            elif other is Advantage.FAIL:
                return other
            else:
                pass
        elif self is Advantage.CANCELLED:
            return other if other is Advantage.FAIL else self
        elif self is Advantage.FAIL:
            return self

        # Fell through
        raise NotImplementedError(f"Cannot combine {self.name} and {other.name}")


class Roll:
    def __init__(self, *vals: int) -> None:
          self._raw_vals = list(vals)
          self._vals = list(vals)

    def modify(self, modifier: int) -> None:
         for i in range(len(self._vals)):
              self._vals[i] += modifier

    def apply(self, advantage: Advantage = Advantage.NONE) -> int:
        if advantage is Advantage.NONE:
                return self._vals[0]
        elif advantage is Advantage.ADVANTAGE:
                return max(*self._vals)
        elif advantage is Advantage.DISADVANTAGE:
                return min(*self._vals)
        elif advantage is Advantage.CANCELLED:
                return self._vals[0]
        elif advantage is Advantage.FAIL:
                return 0


class Dice:
    @staticmethod
    def d_flat(sides: int) -> int:
        return random.randint(1, sides)

    @staticmethod
    def d(sides: int) -> int:
        roll1 = Dice.d_flat(sides)
        roll2 = Dice.d_flat(sides)
        return Roll(roll1, roll2)
