from enum import StrEnum


class DialogCancelled(Exception):
    """User cancelled the dialog."""

    pass


class DialogState(StrEnum):
    IDLE = "idle"
    WAITING_WIZARD = "waiting_wizard"
    WAITING_FORM = "waiting_form"
