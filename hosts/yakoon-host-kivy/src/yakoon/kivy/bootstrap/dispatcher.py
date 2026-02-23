from __future__ import annotations

from collections.abc import Callable

from kivy.clock import Clock


class ContextDispatcher:

    def __init__(self):
        self._handler: Callable[[object], None] | None = None

    def set_handler(self, handler: Callable[[object], None]) -> None:
        self._handler = handler

    def __call__(self, ctx) -> None:
        if self._handler:
            Clock.schedule_once(lambda _dt: self._handler(ctx), 0)
            # self._handler(ctx)
