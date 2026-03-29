from __future__ import annotations

import inspect

from yakoon.base.flow.primitives import Outcome


class FlowCursor:

    def __init__(self):
        self._stack = []

    async def next(self, command, request):

        # initialisieren
        if not self._stack:
            gen = _ensure_step(command.run)(command, request)
            self._stack.append(gen)

        gen = self._stack[-1]
        return await anext(gen)

    def has_stack(self) -> bool:
        return bool(self._stack)

    async def send(self, value):
        gen = self._stack[-1]
        return await gen.asend(value)

    def push(self, gen):
        self._stack.append(gen)

    def pop(self):
        if self._stack:
            self._stack.pop()

    def current(self):
        if not self._stack:
            raise RuntimeError("Cursor stack is empty")
        return self._stack[-1]


def _ensure_step(run_fn):

    def factory(command, request):

        result = run_fn(request)

        # --- async generator ---
        if inspect.isasyncgen(result):
            return result

        # --- coroutine ---
        if inspect.iscoroutine(result):

            async def coro_wrapper():
                await result
                yield Outcome()

            return coro_wrapper()

        # --- None ---
        if result is None:

            async def empty():
                yield Outcome()

            return empty()

        raise TypeError(f"Invalid return type: {type(result)}")

    return factory
