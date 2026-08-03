from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING

from y5n.runtime.api.flow.dsl import Pulse
from y5n.runtime.api.nodes.space import NodeSpace

from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.runtime.api.nodes.node import Node


def _parse_entry(entry: str) -> tuple[str, str]:
    if ":" in entry:
        scheme, _, rest = entry.partition(":")
        if scheme == "pack":
            return (scheme, rest)
    raise ValueError(f"invalid entry '{entry}' — expected 'pack:<module>:<func>'")


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

    def _handle_module_entry(self, value: str, space: NodeSpace) -> RunResult | None:
        if ":" not in value:
            return None
        mod_name, _, func_name = value.rpartition(":")
        if not mod_name or not func_name:
            return None
        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
        import importlib

        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            return None
        func = getattr(mod, func_name, None)
        if func is None:
            return None
        try:
            result = func(space)
        except TypeError:
            result = func()
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

        _, value = _parse_entry(entry)
        return self._handle_module_entry(value, space)
