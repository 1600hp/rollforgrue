import enum

from asciimatics.widgets import Label, Layout

from .dice import Advantage
from .pc import Ability, PC, Proficiency


class Palette(enum.Enum):
    """
    Visual stylings to UI colour palette names
    """
    BRIGHT = "label"
    DIM = "field"
    DARK = "disabled"
    BAD = "invalid"


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
        "adv_widget": "The `Label` widget displaying the level of advantage applied to this roll",
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
        self.adv_widget = Label("-")
        self.adv_widget.custom_colour = Palette.DIM.value

    def populate(self, layout: Layout) -> None:
        """
        Add the widgets needed to display the bar into the first three columns
        of the given layout, and refresh with a value of 0.

        :params layout: The `Layout` to populate
        """
        layout.add_widget(self.name_widget, 0)
        layout.add_widget(self.value_widget, 1)
        layout.add_widget(self.bar_widget, 2)
        layout.add_widget(self.adv_widget, 3)
        self.refresh(Palette.DARK.value, 0, Advantage.NONE)

    def refresh(self, colour: str, value: int, advantage: Advantage) -> None:
        """
        Refresh the widgets composing the bar display.

        :params colour: The string palette colour to apply to the bar
        :params value: The new value to display
        :params advantage: The level of advantage to display
        """
        self.value_widget.text = str(value)
        self.bar_widget.set_target(colour, value)
        match advantage:
            case Advantage.NONE:
                self.adv_widget.text = "-"
                self.adv_widget.custom_colour = Palette.DIM.value
            case Advantage.ADVANTAGE:
                self.adv_widget.text = "▲"
                self.adv_widget.custom_colour = Palette.BRIGHT.value
            case Advantage.DISADVANTAGE:
                self.adv_widget.text = "▼"
                self.adv_widget.custom_colour = Palette.BAD.value
            case Advantage.FAIL:
                self.adv_widget.text = "X"
                self.adv_widget.custom_colour = Palette.BAD.value
