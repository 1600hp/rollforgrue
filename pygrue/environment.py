import enum


class Lighting(enum.Enum):
    DARK = enum.auto()
    DIM = enum.auto()
    BRIGHT = enum.auto()


class Sense(enum.Enum):
    SIGHT = enum.auto()
    HEARING = enum.auto()
    SMELL = enum.auto()
