from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class RenderMount:
    target: Literal["live", "history"]
    op: Literal["set_live", "clear_live", "append_history", "replace_history"]
    vid: str | None
    payload: object
