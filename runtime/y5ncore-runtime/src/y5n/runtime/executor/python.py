from __future__ import annotations

import io
import runpy
import sys
from typing import TYPE_CHECKING

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text

from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.base.nodes.node import Node
    from y5n.base.nodes.space import NodeSpace


def _empty() -> RunResult:
    async def _noop():
        yield Outcome()

    return _noop()


class PythonExecutor(Executor):

    kind = ExecutorKind.PYTHON

    def run(
        self,
        node: Node,
        phase: Phase,
        space: NodeSpace,
    ) -> RunResult:
        fs_path = node.fs_path
        if fs_path is None:
            return _empty()
        app_file = fs_path / "_yak" / phase.value / "app.py"
        if not app_file.is_file():
            return _empty()

        old_argv = sys.argv
        old_main = sys.modules.pop("__main__", None)
        sys.argv = [str(app_file)]
        if space.request:
            sys.argv.extend(space.request.args())

        buf = io.StringIO()
        old_out = sys.stdout
        sys.stdout = buf
        try:
            runpy.run_path(str(app_file), run_name="__main__")
        finally:
            sys.stdout = old_out
            sys.argv = old_argv
            if old_main is not None:
                sys.modules["__main__"] = old_main
            else:
                sys.modules.pop("__main__", None)

        text = buf.getvalue()
        if text.strip():
            async def _stream():
                for line in text.splitlines():
                    yield Outcome(effects=[EmitView(to_text(line))])
            return _stream()
        return _empty()
