from typing import Iterable

from asciimatics.event import Event, KeyboardEvent
from asciimatics.exceptions import StopApplication
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Divider, Frame, Label, Layout, RadioButtons, TextBox, VerticalDivider

from .dice import Advantage
from .environment import Lighting, Sense
from .obs import OBSClient
from .pc import Ability, PC, Proficiency
from .ui_utils import Palette, RollBar


class ExplorationView(Frame):
    """
    A view for displaying controls and feedback related to exploration.
    """
    __slots__ = {
        "_roll_bars": "All `RollBar` objects associated with this view",
        "_stinger_buttons": "All `Button` objects associated with stingers",
        "_stinger_button_labels": "All `TextBox` objects associated with stinger buttons",
        "lighting_radio": "A radio button controlling the relevant lighting conditions",
        "obs_client": "The OBS WebSocket client associated with this view",
        "sense_radio": "A radio button controlling the relevant sense",
    }

    MAX_STINGERS = 10
    MAX_HOTKEYS = 10

    def __init__(self, screen: Screen, pcs: Iterable[PC], obs_client: OBSClient) -> None:
        """
        :params screen: The `Screen` which will display this view
        :params pcs: All `PC`s associated with this view
        :params obs_client: The client used to connect to OBS
        """
        super(ExplorationView, self).__init__(screen,
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

        # Vertical divider
        layout.add_widget(VerticalDivider(), 4)

        def add_rollbar_section(label: str, ability: Ability, proficiency: Proficiency):
            layout.add_widget(Divider(), 0)
            layout.add_widget(Divider(), 1)
            layout.add_widget(Label(label), 2)
            layout.add_widget(Divider(), 3)
            for pc in pcs:
                roll_bar = RollBar(pc, ability, proficiency, screen.force_update)
                self._roll_bars.append(roll_bar)
                roll_bar.populate(layout)

        add_rollbar_section("PERCEPTION", Ability.WISDOM, Proficiency.PERCEPTION)
        add_rollbar_section("INVESTIGATION", Ability.INTELLIGENCE, Proficiency.INVESTIGATION)
        add_rollbar_section("INSIGHT", Ability.WISDOM, Proficiency.INSIGHT)
        add_rollbar_section("STEALTH", Ability.DEXTERITY, Proficiency.STEALTH)
        add_rollbar_section("SURVIVAL", Ability.WISDOM, Proficiency.PERCEPTION)

        # End of rollbar pane
        for col in range(4):
            layout.add_widget(Divider(), col)

        # Vertical divider
        layout.add_widget(VerticalDivider(), 1)

        # Transitions
        layout.add_widget(Label("HOTKEYS"), 2)
        for _ in range(ExplorationView.MAX_HOTKEYS):
            next_button = Button("[NONE]", on_click=lambda: None)
            self._hotkey_buttons.append(next_button)
            layout.add_widget(next_button, 2)
        if self.obs_client.client is not None:
            self.rebind_hotkeys()
        else:
            layout.add_widget(Label("<NO OBS>"), 2)

        # Stingers
        layout.add_widget(Label("STINGERS"), 0)
        for _ in range(ExplorationView.MAX_STINGERS):
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
        layout.add_widget(Divider(), 5)
        layout.add_widget(Button("REFRESH", self._refresh_bars), 5)

        layout.add_widget(Divider(), 5)
        self.sense_radio = RadioButtons([("SIGHT", Sense.SIGHT),
                                         ("HEARING", Sense.HEARING),
                                         ("SMELL", Sense.SMELL),],
                                        label="SENSE",
                                        on_change=self._refresh_bars)
        layout.add_widget(self.sense_radio, column=5)

        layout.add_widget(Divider(), 5)
        self.lighting_radio = RadioButtons([("BRIGHT", Lighting.BRIGHT),
                                            ("DIM", Lighting.DIM),
                                            ("DARK", Lighting.DARK),],
                                           label="LIGHTING",
                                           on_change=self._refresh_bars)
        layout.add_widget(self.lighting_radio, column=5)
        layout.add_widget(Divider(), 5)

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

    def _refresh_bars(self) -> None:
        """
        For each bar, reroll and refresh using the relevant environmental
        conditions. Call whenever those conditions change, or a reroll is
        requested.
        """
        for bar in self._roll_bars:
            inherent_advantage = bar.pc.proficiency_advantages[bar.proficiency]

            if self.sense_radio.value is Sense.SIGHT and bar.proficiency.sight_affected():
                lighting_advantage = bar.pc.with_lighting(self.lighting_radio.value)
                match lighting_advantage:
                    case Advantage.DISADVANTAGE:
                        colour = Palette.DIM
                    case Advantage.FAIL:
                        colour = Palette.DARK
                    case _:
                        colour = Palette.BRIGHT

                total_advantage_level = lighting_advantage + inherent_advantage
                result = bar.pc.sight_based_check(bar.ability, self.lighting_radio.value, bar.proficiency)
            else:
                colour = Palette.BRIGHT
                total_advantage_level = inherent_advantage
                result = bar.pc.check(bar.ability, bar.proficiency, Advantage.NONE)

            bar.refresh(colour.value, result, total_advantage_level)

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
        return super(ExplorationView, self).process_event(event)
