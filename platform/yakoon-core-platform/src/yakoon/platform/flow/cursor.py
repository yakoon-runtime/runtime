from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Literal

from yakoon.base.flow.primitives import Outcome

if TYPE_CHECKING:
    from yakoon.base.nodes import Node, NodeSpace

HandlerName = Literal[
    "run",
    "setup",
]


class FlowCursor:

    def __init__(self, handler_name: HandlerName):
        self.handler_name = handler_name
        self._stack = []

    async def next(
        self,
        node: Node,
        ctx: NodeSpace,
    ):
        if not self._stack:
            handler = getattr(node, self.handler_name)
            gen = _ensure_step(handler)(ctx)
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

    def factory(ctx):

        result = run_fn(ctx)

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
