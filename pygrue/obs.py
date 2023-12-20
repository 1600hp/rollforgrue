import pathlib
import json

from obswebsocket import obsws, requests
from obswebsocket.exceptions import ConnectionFailure


class OBSClient:
    __slots__ = {
        "address": "The OBS server address",
        "checked": "`True` if a caller has queried `get_scene`, `False` previously.",
        "client": "The OBS client",
        "password": "The OBS server password",
        "port": "The OBS server port",
        "scenes": "The list of available scene names, or an empty list if the connection failed",
    }

    def __init__(self, config: pathlib.Path) -> None:
        with open(config, 'r') as config_file:
            config_data = json.load(config_file)
            self.address = config_data["address"]
            self.port = config_data["port"]
            self.password = config_data["password"]

        self.client = obsws(self.address, self.port, self.password)

        try:
            self.client.connect()
            scene_req = self.client.call(requests.GetSceneList())
            self.scenes = [scene["sceneName"] for scene in scene_req.getScenes()]
        except ConnectionFailure:
            self.client = None
            self.scenes = None

    def set_scene(self, scene_name: str, ignore_unchecked: bool) -> None:
        if ignore_unchecked and not self.checked:
            return

        current = self.get_scene()
        if current != scene_name:
            self.client.call(requests.SetCurrentProgramScene(sceneName=scene_name))

    def get_scene(self) -> None:
        self.checked = True
        return self.client.call(requests.GetCurrentProgramScene()).getCurrentProgramSceneName()
