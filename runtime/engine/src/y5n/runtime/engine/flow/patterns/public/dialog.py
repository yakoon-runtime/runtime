from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class Dialog:
    """Cursor controller for ordered field navigation.

    Dialog manages a cursor over a list of items. It knows nothing
    about data, validation, or rendering — it only tracks position
    and completion.

        dialog = Dialog(fields, focus_key="password")

        while not dialog.completed:
            field = dialog.current
            dialog.next()

        dialog.focus("username")
        dialog.previous()
    """

    def __init__(
        self,
        fields: Sequence[Any],
        *,
        focus_key: str | None = None,
    ):
        self._fields = list(fields)
        self._idx = 0

        if focus_key is not None:
            self.focus(focus_key)

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    @property
    def fields(self) -> list[Any]:
        return self._fields

    @property
    def index(self) -> int:
        return self._idx

    @property
    def count(self) -> int:
        return len(self._fields)

    @property
    def current(self) -> Any | None:
        if self._idx >= len(self._fields):
            return None
        return self._fields[self._idx]

    @property
    def completed(self) -> bool:
        return self._idx >= len(self._fields)

    @property
    def has_previous(self) -> bool:
        return self._idx > 0

    @property
    def has_next(self) -> bool:
        return self._idx < len(self._fields) - 1

    # --------------------------------------------------------
    # Cursor movement
    # --------------------------------------------------------

    def next(self) -> None:
        if self._idx < len(self._fields):
            self._idx += 1

    def previous(self) -> None:
        if self._idx > 0:
            self._idx -= 1

    def move(self, offset: int) -> None:
        target = self._idx + offset
        self._idx = max(0, min(len(self._fields) - 1, target))

    def focus(self, key: str) -> None:
        for i, f in enumerate(self._fields):
            if getattr(f, "key", None) == key:
                self._idx = i
                return
