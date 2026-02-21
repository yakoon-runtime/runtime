from __future__ import annotations

from collections.abc import Callable


class ContextDispatcher:

    def __init__(self):
        self._handler: Callable[[object], None] | None = None

    def set_handler(self, handler: Callable[[object], None]) -> None:
        self._handler = handler

    def __call__(self, ctx) -> None:
        if self._handler:
            self._handler(ctx)
