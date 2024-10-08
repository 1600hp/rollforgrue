import pathlib

from .pc import PC
from .ui import GrueUI, VNUI
from .obs import OBSClient


class GrueApp:
    """
    Application entry point. Constructing an object of this class
    will immediately block and begin execution.
    """
    __slots__ = {
        "pcs": "A list of the Character objects tracked",
        "obs_client": "The client used to transfer data to/from OBS",
    }

    def __init__(self, character_dir: pathlib.Path, config_path: pathlib.Path) -> None:
        """
        :params character_dir: A directory with one or more character JSON files.
        """
        self.pcs = [
            PC(next_char)
            for next_char in character_dir.iterdir()
        ]

        self.obs_client = OBSClient(config_path)

        GrueUI(self.pcs, self.obs_client)


class VNApp:
    """
    Application entry point. Constructing an object of this class
    will immediately block and begin execution.
    """
    __slots__ = {
        "obs_client": "The client used to transfer data to/from OBS",
    }

    def __init__(self, config_path: pathlib.Path) -> None:
        """
        :params character_dir: A directory with one or more character JSON files.
        """
        self.obs_client = OBSClient(config_path)

        VNUI(self.obs_client)
