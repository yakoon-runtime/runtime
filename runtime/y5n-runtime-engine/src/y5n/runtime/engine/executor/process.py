from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

from y5n.runtime.api.flow.dsl import Outcome

from .base import Executor, ExecutorKind, Phase, RunResult

if TYPE_CHECKING:
    from y5n.runtime.api.nodes.node import Node
    from y5n.runtime.api.nodes.space import NodeSpace


def _empty() -> RunResult:
    async def _noop():
        yield Outcome()

    return _noop()


def _emit_text(text: str):
    from y5n.runtime.api.document import to_text
    from y5n.runtime.api.flow.primitives import EmitView

    return EmitView(to_text(text))


class ProcessExecutor(Executor):

    kind = ExecutorKind.PROCESS

    def run(
        self,
        node: Node,
        phase: Phase,
        space: NodeSpace,
    ) -> RunResult:
        fs_path = node.fs_path
        if fs_path is None:
            return _empty()
        app_file = fs_path / "_yak" / phase.value / "app"
        if not app_file.is_file() or not os.access(str(app_file), os.X_OK):
            return _empty()

        ws_root = space.session.get_data("fs:root") if space.session else ""
        raw_path = space.session.cwd if space.session else ""
        if raw_path and raw_path != "/":
            root_path = Path(ws_root) if ws_root else Path()
            cwd = root_path / raw_path.lstrip("/")
            if not cwd.exists():
                cwd = Path(raw_path).resolve()
        else:
            cwd = Path(ws_root) if ws_root else Path.home()
        cwd = str(cwd.resolve())

        args = [str(app_file)]
        if space.request:
            for a in space.request.args():
                args.append(a)

        env = {
            "YAK_WORKSPACE": str(ws_root) if ws_root else "",
            "YAK_NODE": str(node.path),
            "YAK_CWD": cwd,
        }

        async def _stream():
            try:
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    env={**os.environ, **env},
                    cwd=cwd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except FileNotFoundError:
                return

            if proc.stdout:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    yield Outcome(effects=[_emit_text(line.decode().rstrip())])

            await proc.wait()
            if proc.returncode != 0:
                stderr_text = ""
                if proc.stderr:
                    stderr_text = (await proc.stderr.read()).decode().strip()
                if stderr_text:
                    yield Outcome(effects=[_emit_text(f"error: {stderr_text}")])

        return _stream()
