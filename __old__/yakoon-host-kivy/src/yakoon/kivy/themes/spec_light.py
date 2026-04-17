from kivy.event import EventDispatcher
from kivy.properties import ListProperty, NumericProperty, StringProperty


class DefaultTheme(EventDispatcher):

    # Colors (rgba)
    bg = ListProperty([0.88, 0.88, 0.88, 1])
    surface = ListProperty([0.95, 0.95, 0.95, 1])
    surface_input = ListProperty([0.97, 0.97, 0.97, 1])

    border = ListProperty([0.80, 0.80, 0.80, 0])  # no border

    text = ListProperty([0.10, 0.10, 0.10, 1])
    muted = ListProperty([0.40, 0.40, 0.40, 1])
    accent = ListProperty([0, 0, 0, 1])
    # accent = ListProperty([0.30, 0.58, 0.95, 1])

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
