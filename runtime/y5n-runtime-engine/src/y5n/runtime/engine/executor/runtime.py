from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING

from y5n.runtime.api.flow.dsl import Pulse
from y5n.runtime.api.nodes.space import NodeSpace

from ..bootstrap import PackReference
from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.runtime.api.nodes.node import Node


def _empty() -> RunResult:
    async def _noop():
        yield Pulse()

    return _noop()


class RuntimeExecutor(Executor):

    kind = ExecutorKind.RUNTIME

    def _entry_value(self, node: Node, phase: Phase) -> str | None:
        entry = node.metadata.get("entry", {})
        if not isinstance(entry, dict):
            return None
        return entry.get(phase.value)

    def _handle_module_entry(self, entry: str, space: NodeSpace) -> RunResult | None:
        try:
            ref = PackReference(entry)
        except ValueError:
            return None
        try:
            fn = ref.load()
        except LookupError:
            return None
        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
        try:
            result = fn(space)
        except TypeError:
            result = fn()
        if inspect.iscoroutine(result):
            return result
        if hasattr(result, "__aiter__"):
            return result
        return None

    def run(
        self,
        node: Node,
        phase: Phase,
        space: NodeSpace,
    ) -> RunResult:
        entry = self._entry_value(node, phase)
        if not entry:
            return _empty()

        return self._handle_module_entry(entry, space)
