# yakoon/kivy/host/output_adapter.py
from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable


def ensure_async(fn: Callable[[str], object]) -> Callable[[str], Awaitable[None]]:
    if inspect.iscoroutinefunction(fn):
        return fn  # type: ignore[misc]

    async def _wrapped(text: str) -> None:
        fn(text)

    return _wrapped


class OutputAdapter:

    def __init__(self, emit_fn, emit_err_fn=None):
        self.emit = ensure_async(emit_fn)
        self.emit_err = ensure_async(emit_err_fn or emit_fn)
