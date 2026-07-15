from __future__ import annotations

import asyncio
import concurrent.futures
import io
import queue
import runpy
import sys
from typing import TYPE_CHECKING

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text
from y5n.base.runtime.context import CommandContext, _set_context

from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.base.nodes.node import Node
    from y5n.base.nodes.space import NodeSpace


def _empty() -> RunResult:
    async def _noop():
        yield Outcome()

    return _noop()


class _StreamCapture(io.TextIOBase):
    """Thread-safe stdout capture. Pushes lines into a queue.Queue."""

    def __init__(self, q: queue.Queue[str]):
        self._q = q
        self._buffer = ""

    def write(self, text: str) -> int:
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._q.put(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self._q.put(self._buffer)
            self._buffer = ""


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

        async def _stream():
            nonlocal old_argv, old_main
            q: queue.Queue[str] = queue.Queue()
            old_out = sys.stdout
            sys.stdout = _StreamCapture(q)
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:

                    def _run():
                        req = space.request
                        ses = space.session
                        _set_context(
                            CommandContext(
                                path=str(node.path) if node.path else None,
                                request=(
                                    {
                                        "args": list(req.args()) if req else [],
                                        "raw": (
                                            req.raw
                                            if req and hasattr(req, "raw")
                                            else None
                                        ),
                                    }
                                    if req
                                    else None
                                ),
                                session=(
                                    {
                                        "key": (
                                            str(ses.key)
                                            if ses and hasattr(ses, "key")
                                            else None
                                        ),
                                        "lang": (
                                            ses.lang
                                            if ses and hasattr(ses, "lang")
                                            else None
                                        ),
                                    }
                                    if ses
                                    else None
                                ),
                                ports={
                                    "hello": {
                                        "greet": lambda name="World": f"Hello, {name}!",
                                    },
                                },
                            )
                        )
                        runpy.run_path(str(app_file), run_name="__main__")

                    fut = pool.submit(_run)

                    while True:
                        while True:
                            try:
                                line = q.get_nowait()
                                yield Outcome(
                                    effects=[EmitView(to_text(line), mode="append")]
                                )
                            except queue.Empty:
                                break

                        if fut.done():
                            break

                        yield Outcome()
                        await asyncio.sleep(0.02)
            finally:
                sys.stdout = old_out
                sys.argv = old_argv
                if old_main is not None:
                    sys.modules["__main__"] = old_main
                else:
                    sys.modules.pop("__main__", None)

        return _stream()
