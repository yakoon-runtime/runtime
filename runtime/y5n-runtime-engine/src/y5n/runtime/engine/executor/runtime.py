from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING

from ..bootstrap import PackReference
from ..flow.util import empty_flow
from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.runtime.engine.nodes.node import Node


class RuntimeExecutor(Executor):

    kind = ExecutorKind.RUNTIME

    def _entry_value(self, node: Node, phase: Phase) -> str | None:
        entry = node.metadata.get("entry", {})
        if not isinstance(entry, dict):
            return None
        return entry.get(phase.value)

    def _handle_module_entry(self, entry: str) -> RunResult:
        try:
            ref = PackReference(entry)
        except ValueError:
            return empty_flow()
        try:
            fn = ref.load()
        except LookupError:
            return empty_flow()
        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
        try:
            result = fn()
        except TypeError:
            result = fn()
        if inspect.iscoroutine(result):
            return result
        if hasattr(result, "__aiter__"):
            return result
        return empty_flow()

    def run(
        self,
        node: Node,
        phase: Phase,
    ) -> RunResult:
        entry = self._entry_value(node, phase)
        if not entry:
            return empty_flow()

        return self._handle_module_entry(entry)
