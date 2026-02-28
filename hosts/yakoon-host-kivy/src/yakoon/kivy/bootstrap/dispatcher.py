from __future__ import annotations

from collections.abc import Callable

from kivy.clock import Clock
from yakoon.kivy.runtime.context.view_context import ViewContext


class ContextDispatcher:

    _handler: Callable[[ViewContext], None] | None

    def __init__(self):
        self._handler = None

    def set_handler(self, handler: Callable[[ViewContext], None]) -> None:
        self._handler = handler

    def __call__(self, ctx) -> None:
        # to get a context to write from runtime
        if self._handler:
            Clock.schedule_once(lambda _dt: self._handler(ctx), 0)
