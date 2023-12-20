import enum
from typing import Iterable

from asciimatics.event import Event, KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Divider, Frame, Label, Layout, RadioButtons

from .dice import Advantage
from .environment import Lighting, Sense
from .pc import Ability, PC, Proficiency


class Palette(enum.Enum):
    """
    Visual stylings to UI colour palette names
    """
    BRIGHT = "label"
    DIM = "field"
    DARK = "disabled"


class BarLabel(Label):
    """
    A label subclass that displays a bar representing a roll.
    Set the rolled value using `set_target` and the bar will
    gradually update to hit the target.
    """

    __slots__ = {
        "_custom_colour": "The color string to use to display the widget",
        "_done_sweep": "Whether the sweep update has completed (if true, the displayed value is target_value)",
        "_force_update_callback": "The callable that will be invoked when the bar requires more updates",
        "_scan_ascending": "Whether the current scan update is moving up or down the bar",
        "length": "The maximum length of the bar",
        "target_value": "The value that the bar is approaching",
    }

    def __init__(self, colour: str, force_update: callable, length: int = 30) -> None:
        """
        :params colour: The colour string to use to render the bar
        :params force_update: A callback to call when the bar label needs to request a visual update
        :params length: The maximum length of the bar
        """
        self.length = length
        self.target_value = 0
        self._done_sweep = False
        self._force_update_callback = force_update
        self._scan_ascending = True
        self.custom_colour = colour
        super(BarLabel, self).__init__(self._val_to_ascii(0))

    def _val_to_ascii(self, value: int) -> str:
        """
        Transform an integer value to an ASCII bar of the corresponding length.

        :params value: The length of the bar
        """
        return "█" * min(self.length, value) + "▒" * (self.length - min(self.length, value))

    def set_target(self, colour: str, value: int) -> None:
        """
        Set the target value for the bar display. This will begin a sequence
        of updates that will eventually lead to the bar displaying the target.

        :params colour: The colour string to use to render the bar
        :params value: The length of the bar
        """
        self.custom_colour = colour
        self._scan_ascending = value >= self.target_value
        self.target_value = value
        self._done_sweep = False

    def _sweep_update(self) -> bool:
        """
        Perform a single frame's update on the bar, moving one character
        closer to the target display. Call once per `update()`.
        """
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

    def update(self, *args, **kwargs) -> None:
        """
        Update the widget. In addition to the usual updates, perform a single
        character update on the bar, and force an additional screen refresh if
        we have not finished rendering the full bar.
        """
        assert self.custom_colour is not None
        if not self._done_sweep:
            self._force_update_callback()
            self._done_sweep = self._sweep_update()
        else:
            self.text = self._val_to_ascii(self.target_value)

        super(BarLabel, self).update(*args, **kwargs)


class RollBar:
    """
    A combined visual to display a `BarLabel`. In addition to the label itself,
    this renders the name and numeric value rollsed.
    """

    __slots__ = {
        "ability": "The ability to which this bar is linked",
        "bar_widget": "The `BarLabel` widget representing the bar itself",
        "force_update": "The callable that will be invoked when this bar requires an update",
        "name_widget": "The `Label` widget that names this bar",
        "pc": "The `PC` to which this bar is linked",
        "proficiency": "The proficiency to which this bar is linked",
        "value": "The bar's numerical value",
        "value_widget": "The `Label` widget displaying the bar's numerical value",
    }

    def __init__(self,
                 pc: PC,
                 ability: Ability,
                 proficiency: Proficiency,
                 force_update: callable) -> None:
        """
        :params pc: The `PC` to which this bar is linked
        :params ability: The ability to which this bar is linked
        :params proficiency: The proficiency to which this bar is linked
        :params force_update: The callable that will be invoked when this bar requires an update
        """
        self.pc = pc
        self.ability = ability
        self.proficiency = proficiency
        self.name_widget = Label(pc.name)
        self.value_widget = Label(0)
        self.value = 0
        self.bar_widget = BarLabel("disabled", force_update)

    def populate(self, layout: Layout) -> None:
        """
        Add the widgets needed to display the bar into the first three columns
        of the given layout, and refresh with a value of 0.

        :params layout: The `Layout` to populate
        """
        layout.add_widget(self.name_widget, 0)
        layout.add_widget(self.value_widget, 1)
        layout.add_widget(self.bar_widget, 2)
        self.refresh(Palette.DARK.value, 0)

    def refresh(self, colour: str, value: int) -> None:
        """
        Refresh the widgets composing the bar display.

        :params colour: The string palette colour to apply to the bar
        :params value: The new value to display
        """
        self.value_widget.text = str(value)
        self.bar_widget.set_target(colour, value)


class ExplorationView(Frame):
    """
    A view for displaying controls and feedback related to exploration.
    """
    __slots__ = {
        "_roll_bars": "All `RollBar` objects associated with this view",
        "sense_radio": "A radio button controlling the relevant sense",
        "lighting_radio": "A radio button controlling the relevant lighting conditions",
    }

    def __init__(self, screen: Screen, pcs: Iterable[PC]) -> None:
        """
        :params screen: The `Screen` which will display this view
        :params pcs: All `PC`s associated with this view
        """
        super(ExplorationView, self).__init__(screen,
                                         screen.height,
                                         80, # screen.width,
                                         on_load=None,
                                         hover_focus=False,
                                         can_scroll=False,
                                         title="SENSES")
        layout = Layout([12, 3, 30, 20], fill_frame=False)
        self.add_layout(layout)
        self._roll_bars: list[RollBar] = []

        # Perception
        layout.add_widget(Divider(), 0)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("PERCEPTION"), 2)
        for pc in pcs:
            roll_bar = RollBar(pc, Ability.WISDOM, Proficiency.PERCEPTION, screen.force_update)
            self._roll_bars.append(roll_bar)
            roll_bar.populate(layout)

        # Investigation
        layout.add_widget(Divider(), 0)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("INVESTIGATION"), 2)
        for pc in pcs:
            roll_bar = RollBar(pc, Ability.INTELLIGENCE, Proficiency.INVESTIGATION, screen.force_update)
            self._roll_bars.append(roll_bar)
            roll_bar.populate(layout)

        # Controls
        layout.add_widget(Button("REFRESH", self._refresh_bars), 3)
        self.sense_radio = RadioButtons([("SIGHT", Sense.SIGHT),
                                         ("HEARING", Sense.HEARING),
                                         ("SMELL", Sense.SMELL),],
                                        label="SENSE",
                                        on_change=self._refresh_bars)
        layout.add_widget(self.sense_radio, column=3)
        self.lighting_radio = RadioButtons([("BRIGHT", Lighting.BRIGHT),
                                            ("DIM", Lighting.DIM),
                                            ("DARK", Lighting.DARK),],
                                           label="LIGHTING",
                                           on_change=self._refresh_bars)
        layout.add_widget(self.lighting_radio, column=3)

        # Finalize
        self.fix()

    def _refresh_bars(self) -> None:
        """
        For each bar, reroll and refresh using the relevant environmental
        conditions. Call whenever those conditions change, or a reroll is
        requested.
        """
        for bar in self._roll_bars:
            if self.sense_radio.value is Sense.SIGHT:
                match bar.pc.with_lighting(self.lighting_radio.value):
                    case Advantage.DISADVANTAGE:
                        colour = Palette.DIM
                    case Advantage.FAIL:
                        colour = Palette.DARK
                    case _:
                        colour = Palette.BRIGHT
                result = bar.pc.sight_based_check(bar.ability, self.lighting_radio.value, bar.proficiency)
            else:
                colour = Palette.BRIGHT
                result = bar.pc.check(bar.ability, bar.proficiency, Advantage.NONE)

            bar.refresh(colour.value, result)

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

        # Now pass on to lower levels for normal handling of the event.
        return super(ExplorationView, self).process_event(event)


class UI:
    """
    The main app UI. Upon constructing this class, it will immediately
    block and begin running.
    """

    __slots__ = {
        "_pcs": "An iterable of the `PC`s associated with this UI"
    }

    def __init__(self, pcs: Iterable[PC]) -> None:
        """
        :params pcs: The PCs that will be associated with this UI
        """
        self._pcs = pcs
        self.run()

    def _play(self, screen: Screen, scene: Scene) -> None:
        """
        Callback to invoke when the wrapper decides to play.

        :params screen: The `Screen` to play
        :params scene: The starting `Scene`
        """
        views = [ExplorationView(screen, self._pcs)]
        screen.play([Scene(views, -1, name="Main")],
                    stop_on_resize=True,
                    start_scene=scene,
                    allow_int=True)

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
