from __future__ import annotations

from enum import StrEnum


class Interaction(StrEnum):
    CLI = "cli"
    FORM = "form"
    INHERIT = "inherit"
