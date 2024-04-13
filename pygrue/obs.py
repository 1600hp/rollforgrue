from dataclasses import dataclass
import pathlib
import json
from typing import Any

from obswebsocket import obsws, requests
from obswebsocket.exceptions import ConnectionFailure


STINGER_GROUP_SUFFIX = "STINGERS"
"""
The suffix to attach to groups containing stingers. These groups are
structured as [SCENE_NAME].[STINGER_GROUP_SUFFIX] in all caps.
"""

MEDIA_INPUT_ACTION_RESTART = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
"""
The string to command in order to restart a media input.
"""


@dataclass
class Hotkey:
    keybind: dict[str, Any]
    scene: str | None


class OBSClient:
    """
    A client for OBS communication via websocket.

    An object of this class will form a connection with the OBS instance upon
    initialization, and then will accept future manipulation/queries of that
    instance via function calls.

    Scene names are only enumarated upon initialization; if new scenes are
    added later, the client must be reinitialized.
    """

    __slots__ = {
        "address": "The OBS server address",
        "client": "The OBS client",
        "hotkeys": "A dict from hotkey names to keybinds",
        "password": "The OBS server password",
        "port": "The OBS server port",
        "profile": "The path to the OBS profile to use",
        "scenes": "The list of available scene names, or an empty list if the connection failed",
    }

    def __init__(self, config: pathlib.Path) -> None:
        """
        :params config: A path to a websocket configuration file containing the JSON keys "address", "port", and "password"
        """
        with open(config, 'r') as config_file:
            config_data = json.load(config_file)
            self.address = config_data["address"]
            self.port = config_data["port"]
            self.password = config_data["password"]
            self.profile = pathlib.Path(config_data["profile"])

        self.client = obsws(self.address, self.port, self.password)

        try:
            self.client.connect()
            scene_req = self.client.call(requests.GetSceneList())
            self.scenes = [scene["sceneName"] for scene in scene_req.getScenes()]
            self.hotkeys: dict[str, Hotkey] = dict()
            self._load_hotkeys()
        except ConnectionFailure:
            self.client = None
            self.scenes = None
            self.hotkeys = None

    def set_scene(self, scene_name: str) -> None:
        """
        Transition to the target scene.
        """
        current = self.get_scene()
        if current != scene_name:
            self.client.call(requests.SetCurrentProgramScene(sceneName=scene_name))

    def get_scene(self) -> str | None:
        """
        Returns the current scene name, or `None` if there is no connection.
        """
        if self.client is not None:
            return self.client.call(requests.GetCurrentProgramScene()).getCurrentProgramSceneName()
        else:
            return None

    def _load_hotkeys(self) -> None:
        """
        Load from the profile JSON the applicable hotkey names and key binds.

        This populates the `hotkeys` dictionary.
        """
        with open(self.profile, 'r') as profile_file:
            profile_data = json.load(profile_file)
        scene_switcher_data = profile_data["modules"].get("advanced-scene-switcher", None)
        if scene_switcher_data is None:
            return None

        # Each macro should have at most one scene condition and one hotkey
        # condition to be considered.
        for macro in scene_switcher_data["macros"]:
            name = ""
            keybind = None
            scene = None

            for condition in macro.get("conditions", []):
                if condition["id"] == "hotkey" and condition["keyBind"]:
                    keybind = condition["keyBind"][0]
                    name = condition["desc"]
                    break

            for condition in macro.get("conditions", []):
                if condition["id"] == "scene":
                    scene = condition["sceneSelection"]["name"]

            if keybind is not None:
                self.hotkeys[name] = Hotkey(keybind, scene)

    def trigger_hotkey(self, hotkey: str) -> None:
        """
        Trigger a hotkey in the OBS client by name.

        :params hotkey: The hotkey to trigger
        """
        keybind = self.hotkeys[hotkey].keybind
        key_id = keybind["key"]
        key_modifiers = dict(
            control=keybind.get("control", False),
            shift=keybind.get("shift", False),
            alt=keybind.get("alt", False),
            command=keybind.get("command", False),
        )
        self.client.call(requests.TriggerHotkeyByKeySequence(keyId=key_id, keyModifiers=key_modifiers))

    def get_stinger_group_name(self) -> str:
        """
        Returns the group name of the stinger-containing group in the current
        scene. This is not guaranteed to be an existing group, just what the
        group would be called, were one to exist.
        """
        return f"{self.get_scene()}.{STINGER_GROUP_SUFFIX}".upper()

    def get_stingers(self) -> list[str]:
        """
        Returns a list of all stinger names associated with the current scene,
        or an empty list if there are none.
        """
        group_name = self.get_stinger_group_name()
        result = self.client.call(requests.GetGroupSceneItemList(sceneName=group_name))
        if result.status:
            items = result.getSceneItems()
        else:
            items = []
        return [item["sourceName"] for item in items]

    def get_hotkeys(self) -> list[str]:
        """
        Returns a list of all hotkey names associated with the current scene,
        or an empty list if there are none.
        """
        scene_hotkeys = []
        scene = self.get_scene()
        for name, attributes in self.hotkeys.items():
            if attributes.scene == scene:
                scene_hotkeys.append(name)
        return scene_hotkeys

    def trigger_stinger(self, stinger_name) -> None:
        """
        Trigger a particular stinger by restarting the media input with which
        it is associated.

        :params stinger_name: The name of the stinger to trigger
        """
        self.client.call(requests.TriggerMediaInputAction(inputName=stinger_name, mediaAction=MEDIA_INPUT_ACTION_RESTART))
