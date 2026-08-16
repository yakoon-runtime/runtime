from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Literal

from y5n.runtime.api.flow.primitives import Pulse
from y5n.runtime.engine.nodes.handler import RunHandler

if TYPE_CHECKING:
    from y5n.runtime.engine.nodes import Node

HandlerName = Literal["run",]


class FlowCursor:
    """Manages the async generator stack for flow execution.

    Supports push (enter sub-flow) and pop (return to parent),
    driving the generator with next() and send().
    """

    def __init__(self, handler_name: HandlerName):
        self.handler_name = handler_name
        self._stack = []

    async def next(
        self,
        node: Node,
    ) -> Pulse | AsyncGenerator | None:
        if not self._stack:
            if self.handler_name != "run":
                raise ValueError(f"Invalid handler: {self.handler_name}")
            handler = node.run
            if handler is None:
                raise RuntimeError(f"Node {node} has no {self.handler_name} handler")
            gen = _ensure_step(handler)()
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


def _ensure_step(run_fn: RunHandler):

    def factory():

        result = run_fn()

        # --- async generator ---
        if inspect.isasyncgen(result):
            return result

        # --- coroutine ---
        if inspect.iscoroutine(result):

            async def coro_wrapper():
                await result
                yield Pulse()

            return coro_wrapper()

        # --- None ---
        if result is None:

            async def empty():
                yield Pulse()

            return empty()

        raise TypeError(f"Invalid return type: {type(result)}")

    return factory
