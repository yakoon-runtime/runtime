from kivy.event import EventDispatcher
from kivy.properties import ListProperty, NumericProperty, StringProperty


class DefaultTheme(EventDispatcher):

    # Colors (rgba)
    bg = ListProperty([0.07, 0.07, 0.08, 1])
    surface = ListProperty([0.11, 0.11, 0.13, 1])
    surface_input = ListProperty([0.13, 0.13, 0.15, 1])

    # bg = [0.15, 0.15, 0.16, 1]
    # surface = [0.20, 0.20, 0.22, 1]

    border = ListProperty([0.20, 0.20, 0.24, 0])  # no border

    text = ListProperty([0.93, 0.93, 0.95, 1])
    muted = ListProperty([0.70, 0.70, 0.75, 1])
    accent = ListProperty([0.30, 0.58, 0.95, 1])

    # states
    info = ListProperty([0.45, 0.75, 0.95, 1])  # kühles Blau/Cyan
    warning = ListProperty([0.95, 0.70, 0.20, 1])  # gelb/orange
    error = ListProperty([0.90, 0.30, 0.30, 1])  # rot
    success = ListProperty([0.30, 0.75, 0.45, 1])  # grün

    # Metrics
    radius = NumericProperty(14)
    pad = NumericProperty(10)
    pad_sm = NumericProperty(6)
    font = StringProperty("Roboto")
    font_mono = StringProperty("RobotoMono")  # falls nicht vorhanden: später fallback
