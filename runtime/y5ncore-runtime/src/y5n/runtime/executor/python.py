from __future__ import annotations

import importlib.util
import io
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path
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


def _build_session_dict(ses) -> dict | None:
    if ses is None:
        return None
    return {
        "key": str(ses.key) if hasattr(ses, "key") else None,
        "lang": ses.lang if hasattr(ses, "lang") else None,
    }


class PythonExecutor(Executor):

    kind = ExecutorKind.PYTHON

    def __init__(self):
        self._loaded_modules: dict[Path, types.ModuleType] = {}

    def _entry_file(self, node: Node, phase: Phase) -> Path | None:
        fs_path = node.fs_path
        if fs_path is None:
            return None

        entry = node.metadata.get("entry", {})
        entry_path = entry.get(phase.value) if isinstance(entry, dict) else None
        if entry_path:
            candidate = fs_path / entry_path
            if candidate.is_file():
                return candidate
        # Fallback for commands that haven't migrated their structure
        fallback = fs_path / "_yak" / phase.value / "app.py"
        if fallback.is_file():
            return fallback
        return None

    def run(
        self,
        node: Node,
        phase: Phase,
        space: NodeSpace,
    ) -> RunResult:
        app_file = self._entry_file(node, phase)
        if app_file is None:
            return _empty()

        req = space.request
        ses = space.session

        async def _stream():
            _set_context(
                CommandContext(
                    path=str(node.path) if node.path else None,
                    command=(str(node.path).rsplit("/", 1)[-1] if node.path else None),
                    tokens=list(req.args()) if req else None,
                    session=_build_session_dict(ses),
                )
            )

            mod = self._load_module(app_file)
            if mod is None or not hasattr(mod, "main"):
                return

            old_argv = sys.argv
            sys.argv = [str(app_file)]
            if req:
                sys.argv.extend(req.args())

            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    mod.main()
            finally:
                sys.argv = old_argv

            output = buf.getvalue()
            if output:
                for line in output.splitlines():
                    yield Outcome(effects=[EmitView(to_text(line), mode="append")])

            yield Outcome()

        return _stream()

    def _load_module(self, path: Path) -> types.ModuleType | None:
        loaded = self._loaded_modules.get(path)
        if loaded is not None:
            return loaded

        full_name = (
            "yak.bundle.batch." + path.parent.parent.parent.name + "." + path.stem
        )

        spec = importlib.util.spec_from_file_location(full_name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        self._loaded_modules[path] = mod
        return mod
