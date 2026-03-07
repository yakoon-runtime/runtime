from enum import StrEnum


class DialogState(StrEnum):
    IDLE = "idle"
    WAITING_WIZARD = "waiting_wizard"
    WAITING_FORM = "waiting_form"
