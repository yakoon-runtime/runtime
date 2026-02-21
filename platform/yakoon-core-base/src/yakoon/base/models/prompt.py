from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PromptResult:

    _values: dict[str, Any]  # var -> value
    _aliases: dict[str, str]  # key -> var
    _order: list[str]  # vars in definition order

    def get(self, k: str, default: Any = None) -> Any:
        if k in self._values:
            return self._values[k]
        v = self._aliases.get(k)
        if v is not None:
            return self._values.get(v, default)
        return default

    def first(self) -> Any:
        if not self._order:
            raise LookupError("PromptResult is empty")
        return self._values[self._order[0]]

    def last(self) -> Any:
        if not self._order:
            raise LookupError("PromptResult is empty")
        return self._values[self._order[-1]]

    def list(self) -> list[Any]:
        return [self._values[k] for k in self._order if k in self._values]

    def dict(self) -> dict[str, Any]:
        return dict(self._values)

    def __getitem__(self, k: str) -> Any:
        sentinel = object()
        v = self.get(k, sentinel)
        if v is sentinel:
            raise KeyError(k)
        return v
