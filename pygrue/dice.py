from __future__ import annotations
import enum
import random

class Advantage(enum.Enum):
    """
    The advantage state of a roll. May be combined with the addition operator,
    following normal 5e rules.
    """
    NONE = enum.auto()
    """
    No advantage state.
    """

    ADVANTAGE = enum.auto()
    """
    Roll has advantage.
    """

    DISADVANTAGE = enum.auto()
    """
    Roll has disadvantage.
    """

    CANCELLED = enum.auto()
    """
    Advantage has been cancelled, any additional sources will not apply.
    """

    FAIL = enum.auto()
    """
    Roll automatically fails.
    """

    def __add__(self, other: Advantage) -> Advantage:
        """
        Advantage states combine with the following rules:
        * Advantage and disadvantage cancel
        * Canceled advantage can never become advantage or disadvantage again
        * Automatic failures override any other advantage state

        :params other: The advantage state to combine with.
        """
        if not isinstance(other, Advantage):
            raise NotImplementedError()

        if self is Advantage.NONE:
            return other
        elif self is Advantage.ADVANTAGE:
            match other:
                case Advantage.NONE:
                    return self
                case Advantage.ADVANTAGE:
                    return self
                case Advantage.DISADVANTAGE:
                    return Advantage.CANCELLED
                case Advantage.CANCELLED:
                    return other
                case Advantage.FAIL:
                    return other
                case _:
                    pass
        elif self is Advantage.DISADVANTAGE:
            match other:
                case Advantage.NONE:
                    return self
                case Advantage.ADVANTAGE:
                    return Advantage.CANCELLED
                case Advantage.DISADVANTAGE:
                    return self
                case Advantage.CANCELLED:
                    return other
                case Advantage.FAIL:
                    return other
                case _:
                    pass
        elif self is Advantage.CANCELLED:
            return other if other is Advantage.FAIL else self
        elif self is Advantage.FAIL:
            return self

        # Fell through
        raise NotImplementedError(f"Cannot combine {self.name} and {other.name}")


class Roll:
    """
    A roll's result, with the ability to apply modifiers and advantage states.
    """
    __slots__ = {
         "_raw_vals": "All raw die values considered in this roll",
         "_vals": "All modified die values considered in this roll",
    }

    def __init__(self, *vals: int) -> None:
          """
          Codify rolled dice into a `Roll` object.

          :params vals: The raw die values for the roll to consider
          """
          self._raw_vals = list(vals)
          self._vals = list(vals)

    def modify(self, modifier: int) -> None:
         """
         Apply a modifier to the roll's results.

         :params modifier: The modifier to apply
         """
         for i in range(len(self._vals)):
              self._vals[i] += modifier

    def apply(self, advantage: Advantage = Advantage.NONE) -> int:
        """
        Apply an advantage state to the modified roll's results.
        Returns the highest roll if advantage is applied, the lowest for
        disadvantage, zero on an automatic failure, and the first roll
        otherwise.

        :params advantage: The advantage state to apply
        """
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
