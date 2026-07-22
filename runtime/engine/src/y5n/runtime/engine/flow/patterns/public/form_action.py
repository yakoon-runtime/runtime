from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class FormAction:
    """A navigation action on a form cursor.

    Describes *what* should happen, not *how* — the same action
    can originate from keyboard, mouse, agent, or API.

        FormAction("next")
        FormAction("previous")
        FormAction("focus", target="username")
    """

    action: Literal["next", "previous", "focus", "submit"]
    target: str | None = None

    # --------------------------------------------------------
    # Wire serialization
    # --------------------------------------------------------

    def to_wire(self) -> dict[str, Any]:
        return {
            "__type__": "FormAction",
            "action": self.action,
            "target": self.target,
        }

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> FormAction:
        return cls(action=data["action"], target=data.get("target"))
