import pathlib

from pygrue.pc import PC
from pygrue.ui import UI


class App:
    __slots__ = {
        "pcs": "A list of the Character objects tracked"
    }

    def __init__(self, character_dir: pathlib.Path) -> None:
        self.pcs = [
            PC(next_char)
            for next_char in character_dir.iterdir()
        ]
        UI(self.pcs)
