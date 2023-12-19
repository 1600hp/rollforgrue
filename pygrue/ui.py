import enum
from typing import Iterable

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Divider, Frame, Label, Layout, RadioButtons

from .environment import Lighting
from .pc import Ability, PC, Proficiency


class Palette(enum.Enum):
    BRIGHT = "label"
    DIM = "field"
    DARK = "disabled"


class BarLabel(Label):
    def __init__(self, colour: str, force_update: callable, length: int = 30) -> None:
        self.length = length
        self.target_value = 0
        self._done_sweep = False
        self._force_update_callback = force_update
        self._scan_ascending = True
        self.custom_colour = colour
        super(BarLabel, self).__init__(self._val_to_ascii(0))

    def _val_to_ascii(self, value: int) -> str:
        return "█" * min(self.length, value) + "▒" * (self.length - min(self.length, value))

    def set_target(self, colour: str, value: int) -> None:
        self.custom_colour = colour
        self._scan_ascending = value >= self.target_value
        self.target_value = value
        self._done_sweep = False

    def _sweep_update(self) -> bool:
        target_text = self._val_to_ascii(self.target_value)
        scan_range = list(range(len(target_text)))
        scan_iterator = scan_range if self._scan_ascending else list(reversed(scan_range))
        for i in scan_iterator:
            if self.text[i] != target_text[i] and self.text[i] != "▓":
                self.text = self.text[:i] + "▓" + self.text[i + 1:]
                return False

        for i in scan_iterator:
            if self.text[i] == "▓":
                self.text = self.text[:i] + target_text[i] + self.text[i + 1:]
                return False

    def update(self, *args, **kwargs):
        assert self.custom_colour is not None
        if not self._done_sweep:
            self._force_update_callback()
            self._done_sweep = self._sweep_update()
        else:
            self.text = self._val_to_ascii(self.target_value)

        super(BarLabel, self).update(*args, **kwargs)


class RollBar:
    def __init__(self,
                 pc: PC,
                 ability: Ability,
                 proficiency: Proficiency,
                 force_update: callable) -> None:
        self.pc = pc
        self.ability = ability
        self.proficiency = proficiency
        self.name_widget = Label(pc.name)
        self.value_widget = Label(0)
        self.value = 0
        self.bar_widget = BarLabel("disabled", force_update)

    def populate(self, layout: Layout) -> None:
        layout.add_widget(self.name_widget, 0)
        layout.add_widget(self.value_widget, 1)
        layout.add_widget(self.bar_widget, 2)
        self.refresh("disabled", 0)

    def refresh(self, colour: str, value: int) -> None:
        self.value_widget.text = str(value)
        self.bar_widget.set_target(colour, value)


class VisualView(Frame):
    def __init__(self, screen: Screen, pcs: Iterable[PC]) -> None:
        super(VisualView, self).__init__(screen,
                                         screen.height,
                                         80, # screen.width,
                                         on_load=None,
                                         hover_focus=False,
                                         can_scroll=False,
                                         title="VISUALS")
        self.lighting = Lighting.BRIGHT

        layout = Layout([12, 3, 30, 20], fill_frame=False)
        self.add_layout(layout)
        self._roll_bars: list[RollBar] = []
        layout.add_widget(Divider(), 0)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("PERCEPTION"), 2)
        # Perception
        for pc in pcs:
            roll_bar = RollBar(pc, Ability.WISDOM, Proficiency.PERCEPTION, screen.force_update)
            self._roll_bars.append(roll_bar)
            roll_bar.populate(layout)
        layout.add_widget(Divider(), 0)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("INVESTIGATION"), 2)
        # Investigation
        for pc in pcs:
            roll_bar = RollBar(pc, Ability.INTELLIGENCE, Proficiency.INVESTIGATION, screen.force_update)
            self._roll_bars.append(roll_bar)
            roll_bar.populate(layout)

        # Controls
        layout.add_widget(Button("REFRESH", self._refresh_bars), 3)
        self.lighting_radio = RadioButtons([("BRIGHT", Lighting.BRIGHT),
                                            ("DIM", Lighting.DIM),
                                            ("DARK", Lighting.DARK),],
                                           label="LIGHTING",
                                           on_change=self._refresh_bars)
        layout.add_widget(self.lighting_radio, column=3)
        self.fix()

    def _refresh_bars(self) -> None:
        for bar in self._roll_bars:
            match self.lighting_radio.value:
                case Lighting.BRIGHT:
                    colour = Palette.BRIGHT
                case Lighting.DIM:
                    colour = Palette.BRIGHT if bar.pc.darkvision else Palette.DIM
                case Lighting.DARK:
                    colour = Palette.DIM if bar.pc.darkvision else Palette.DARK
                case _:
                    raise ValueError(self.lighting_radio.value)
            result = bar.pc.sight_based_check(bar.ability, self.lighting_radio.value, bar.proficiency)
            bar.refresh(colour.value, result)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord("q"), ord("Q"), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord("r"), ord("R")]:
                self._refresh_bars()

            self.screen.force_update()

        # Now pass on to lower levels for normal handling of the event.
        return super(VisualView, self).process_event(event)


class UI:
    def __init__(self, pcs: Iterable[PC]) -> None:
        self._pcs = pcs
        self.run()

    def _play(self, screen: Screen, scene: Scene) -> None:
        views = [VisualView(screen, self._pcs)]
        screen.play([Scene(views, -1, name="Main")],
                    stop_on_resize=True,
                    start_scene=scene,
                    allow_int=True)

    def wrap(self, last_scene: Scene):
        Screen.wrapper(self._play, catch_interrupt=True, arguments=[last_scene])

    def run(self) -> None:
        last_scene = None
        while True:
            try:
                self.wrap(last_scene)
            except ResizeScreenError as e:
                last_scene = e.scene
            else:
                break