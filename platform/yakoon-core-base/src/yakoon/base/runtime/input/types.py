from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class InputEvent:

    raw: Any  # str | dict | später mehr

    # ------------------------
    # Interpretation
    # ------------------------

    def is_text(self) -> bool:
        return isinstance(self.raw, str)

    def is_form(self) -> bool:
        return isinstance(self.raw, dict)

    def to_text(self) -> str:
        if isinstance(self.raw, str):
            return self.raw
        return ""

    def to_values(self) -> dict[str, Any]:
        if isinstance(self.raw, dict):
            return self.raw
        return {}

    def get(self, name: str, default: Any = None) -> Any:
        data = self.to_values()
        return data.get(name, default)

    def require(self, name: str) -> Any:
        data = self.to_values()
        if name not in data:
            raise KeyError(f"Missing input field: {name}")
        return data[name]
