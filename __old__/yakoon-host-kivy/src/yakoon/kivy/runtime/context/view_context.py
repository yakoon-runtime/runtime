from collections.abc import Callable
from dataclasses import dataclass

from y5n.kivy.models.envelope import Envelope


@dataclass
class ViewContext:
    session: object
    envelope: Envelope
    ui_state_provider: Callable  # returns UIState
