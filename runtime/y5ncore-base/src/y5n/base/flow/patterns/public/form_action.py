from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FormAction:
    """A navigation action on a form cursor.

    Describes *what* should happen, not *how* — the same action
    can originate from keyboard, mouse, agent, or API.

        FormAction("next")
        FormAction("previous")
        FormAction("focus", target="username")
        FormAction("submit")
        FormAction("cancel")
    """

    action: Literal["next", "previous", "focus", "submit", "cancel"]
    target: str | None = None
