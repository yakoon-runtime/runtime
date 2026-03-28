from __future__ import annotations

import inspect

from yakoon.base.flow.primitives import Outcome


class FlowCursor:

    def __init__(self):
        self.iterator = None

    async def next(self, command, request):

        if self.iterator is None:
            self.iterator = _ensure_step(command.run)(command, request)

        return await anext(self.iterator)

    async def send(self, value):
        return await self.iterator.asend(value)  # type: ignore


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
