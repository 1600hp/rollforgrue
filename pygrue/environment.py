import enum


class Lighting(enum.Enum):
    """
    The lighting state of the environment.
    """
    DARK = enum.auto()
    """
    The environment is dark. Characters without darkvision cannot see,
    and characters with darkvision see at disadvantage.
    """

    DIM = enum.auto()
    """
    The environment is dim. Characters without darkvision see at
    disadvantage.
    """

    BRIGHT = enum.auto()
    """
    The environment is bright. Characters can see normally.
    """


class Sense(enum.Enum):
    """
    The sense used to perceive the environment.
    """
    SIGHT = enum.auto()
    """
    Characters perceive using sight, and lighting must be considered.
    """

    HEARING = enum.auto()
    """
    Characters perceive using hearing.
    """

    SMELL = enum.auto()
    """
    Characters perceive using smell.
    """
