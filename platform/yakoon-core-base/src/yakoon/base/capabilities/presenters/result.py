from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PresentResult:
    """
    Result of a presented interactive state.

    Stores values by var name and supports alias-based lookup.
    """

    _values: dict[str, Any]  # var -> value
    _aliases: dict[str, str]  # alias -> var
    _order: list[str]  # vars in definition order

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._values:
            return self._values[key]
        var = self._aliases.get(key)
        if var is not None:
            return self._values.get(var, default)
        return default

    def first(self) -> Any:
        if not self._order:
            raise LookupError("PresentResult is empty")
        return self._values[self._order[0]]

    def last(self) -> Any:
        if not self._order:
            raise LookupError("PresentResult is empty")
        return self._values[self._order[-1]]

    def list(self) -> list[Any]:
        return [self._values[k] for k in self._order if k in self._values]

    def dict(self) -> dict[str, Any]:
        return dict(self._values)

    def __getitem__(self, key: str) -> Any:
        sentinel = object()
        value = self.get(key, sentinel)
        if value is sentinel:
            raise KeyError(key)
        return value

    def __bool__(self) -> bool:
        return bool(self._values)
