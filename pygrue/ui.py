from typing import Iterable

from asciimatics.exceptions import ResizeScreenError
from asciimatics.scene import Scene
from asciimatics.screen import Screen

from .exploration_view import ExplorationView
from .obs import OBSClient
from .pc import PC
from .vn_view import VNView


class UI:
    """
    The main app UI. Upon constructing this class, it will immediately
    block and begin running.
    """
    __slots__ = {
        "_client": "The client used to connect to OBS",
    }

    def __init__(self, obs_client: OBSClient) -> None:
        """
        :params pcs: The PCs that will be associated with this UI
        :params obs_client: The client used to connect to OBS
        """
        self._client = obs_client
        self.run()

    def wrap(self, last_scene: Scene | None) -> None:
        """
        Wrap and run the UI; called by `run`.

        :params last_scene: The last active scene if recovering from an error, otherwise `None`
        """
        Screen.wrapper(self._play, catch_interrupt=True, arguments=[last_scene])

    def run(self) -> None:
        """
        Run the UI.
        """
        last_scene = None
        while True:
            try:
                self.wrap(last_scene)
            except ResizeScreenError as e:
                last_scene = e.scene
            else:
                break


class GrueUI(UI):
    __slots__ = {
        "_pcs": "An iterable of the `PC`s associated with this UI",
    }

    def __init__(self, pcs: Iterable[PC], obs_client: OBSClient) -> None:
        """
        :params pcs: The PCs that will be associated with this UI
        :params obs_client: The client used to connect to OBS
        """
        self._pcs = pcs
        super().__init__(obs_client)

    def _play(self, screen: Screen, scene: Scene) -> None:
        """
        Callback to invoke when the wrapper decides to play.

        :params screen: The `Screen` to play
        :params scene: The starting `Scene`
        """
        views = [ExplorationView(screen, self._pcs, self._client)]
        screen.play([Scene(views, -1, name="Main")],
                    stop_on_resize=True,
                    start_scene=scene,
                    allow_int=True)


class VNUI(UI):
    def _play(self, screen: Screen, scene: Scene) -> None:
        """
        Callback to invoke when the wrapper decides to play.

        :params screen: The `Screen` to play
        :params scene: The starting `Scene`
        """
        views = [VNView(screen, self._client)]
        screen.play([Scene(views, -1, name="Main")],
                    stop_on_resize=True,
                    start_scene=scene,
                    allow_int=True)
