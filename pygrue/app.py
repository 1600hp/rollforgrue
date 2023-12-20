import pathlib

from pygrue.pc import PC
from pygrue.ui import UI


class App:
    """
    Application entry point. Constructing an object of this class
    will immediately block and begin execution.
    """
    __slots__ = {
        "pcs": "A list of the Character objects tracked"
    }

    def __init__(self, character_dir: pathlib.Path) -> None:
        """
        :params character_dir: A directory with one or more character JSON files.
        """
        self.pcs = [
            PC(next_char)
            for next_char in character_dir.iterdir()
        ]
        UI(self.pcs)
