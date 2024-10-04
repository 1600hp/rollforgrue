from asciimatics.event import Event, KeyboardEvent
from asciimatics.exceptions import StopApplication
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Divider, Frame, Label, Layout, RadioButtons, TextBox, VerticalDivider

from .obs import OBSClient
from .ui_utils import RollBar


class VNView(Frame):
    """
    A view for displaying controls and feedback related to exploration.
    """
    __slots__ = {
        "_stinger_buttons": "All `Button` objects associated with stingers",
        "_stinger_button_labels": "All `TextBox` objects associated with stinger buttons",
        "obs_client": "The OBS WebSocket client associated with this view",
    }

    MAX_STINGERS = 10
    MAX_HOTKEYS = 10

    def __init__(self, screen: Screen, obs_client: OBSClient) -> None:
        """
        :params screen: The `Screen` which will display this view
        :params obs_client: The client used to connect to OBS
        """
        super(VNView, self).__init__(screen,
                                         screen.height,
                                         90, # screen.width,
                                         on_load=None,
                                         hover_focus=False,
                                         can_scroll=False,
                                         title="CONTROL PANEL")
        layout = Layout([12, 3, 25, 2, 3, 20], fill_frame=False)
        self.add_layout(layout)
        self._roll_bars: list[RollBar] = []
        self._hotkey_buttons: list[Button] = []
        self._stinger_buttons: list[Button] = []
        self._stinger_button_labels: list[TextBox] = []
        self.obs_client = obs_client

        # End of rollbar pane
        for col in range(6):
            layout.add_widget(Divider(), col)

        # Vertical divider
        layout.add_widget(VerticalDivider(), 4)

        # Vertical divider
        layout.add_widget(VerticalDivider(), 1)

        # Transitions
        layout.add_widget(Label("HOTKEYS"), 2)
        for _ in range(VNView.MAX_HOTKEYS):
            next_button = Button("[NONE]", on_click=lambda: None)
            self._hotkey_buttons.append(next_button)
            layout.add_widget(next_button, 2)
        if self.obs_client.client is not None:
            self.rebind_hotkeys()
        else:
            layout.add_widget(Label("<NO OBS>"), 2)

        # Stingers
        layout.add_widget(Label("STINGERS"), 0)
        for _ in range(VNView.MAX_STINGERS):
            next_text = TextBox(1, as_string=True)
            next_text.disabled = True
            next_text.custom_colour = "label"
            next_text.value = "[NONE]"
            next_button = Button("play", on_click=lambda: None)
            self._stinger_buttons.append(next_button)
            self._stinger_button_labels.append(next_text)
            layout.add_widget(next_text, 0)
            layout.add_widget(next_button, 0)
        if self.obs_client.client is not None:
            self.rebind_stingers()

        # Controls
        # Scene switcher
        if self.obs_client.scenes is not None:
            self.scene_radio = RadioButtons([(scene, scene) for scene in self.obs_client.scenes],
                                            label="OBS SCENE",
                                            on_change=lambda: self.change_scene(self.scene_radio.value))
            layout.add_widget(self.scene_radio, 5)
            self.scene_radio.value = self.obs_client.get_scene()
        else:
            layout.add_widget(Label("<NO OBS CONNECTION>"), 5)

        # Finalize
        self.fix()

    def change_scene(self, scene: str) -> None:
        """
        Update the current scene to the given name, making the appropriate
        WebSocket callback and rebinding scene-linked UI elements.

        :params scene: The scene name to transition into
        """
        self.obs_client.set_scene(scene)
        self.rebind_stingers()
        self.rebind_hotkeys()

    def rebind_hotkeys(self) -> None:
        hotkeys = self.obs_client.get_hotkeys()
        for i in range(self.MAX_HOTKEYS):
            if i < len(hotkeys):
                self._hotkey_buttons[i]._on_click = lambda h=hotkeys[i]: self.obs_client.trigger_hotkey(h)
                self._hotkey_buttons[i].disabled = False
                self._hotkey_buttons[i].text = hotkeys[i]
            else:
                self._hotkey_buttons[i]._on_click = lambda: None
                self._hotkey_buttons[i].disabled = True
                self._hotkey_buttons[i].text = "[NONE]"

    def rebind_stingers(self) -> None:
        """
        Relabel all stinger buttons and bind them to the appropriate callback.
        """
        stingers = self.obs_client.get_stingers()
        for i in range(self.MAX_STINGERS):
            if i < len(stingers):
                self._stinger_buttons[i]._on_click = lambda s=stingers[i]: self.obs_client.trigger_stinger(s)
                self._stinger_buttons[i].disabled = False
                self._stinger_button_labels[i].value = stingers[i]
            else:
                self._stinger_buttons[i]._on_click = lambda: None
                self._stinger_buttons[i].disabled = True
                self._stinger_button_labels[i].value = "[NONE]"

    def process_event(self, event: Event) -> None:
        """
        Process keyboard and mouse events.

        :params event: The event to process
        """
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord("q"), ord("Q"), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord("r"), ord("R")]:
                self._refresh_bars()

            self.screen.force_update()
            # Consume other key events
            return

        # Now pass on to lower levels for normal handling of the event.
        return super(VNView, self).process_event(event)
