from __future__ import annotations

import importlib.util
import inspect
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

from y5n.base.flow.dsl import Outcome
from y5n.base.nodes.space import NodeSpace

from .base import (
    DiagnosticExecutor,
    Executor,
    ExecutorKind,
    HealthResult,
    Phase,
    RunResult,
)

if TYPE_CHECKING:
    from y5n.base.nodes.node import Node


def _empty() -> RunResult:
    async def _noop():
        yield Outcome()

    return _noop()


class PythonExecutor(Executor, DiagnosticExecutor):

    kind = ExecutorKind.PYTHON

    def __init__(self):
        self._loaded_modules: dict[Path, types.ModuleType] = {}
        self._root_ports = None

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
        tree_path = str(node.path)
        mod = self._load_module(app_file, tree_path=tree_path, phase=phase.value)
        if mod is not None and hasattr(mod, "run"):
            return mod.run(space)
        return _empty()

    async def health(self, node: Node) -> HealthResult:
        fs_path = node.fs_path
        if fs_path is None:
            return HealthResult.green()
        health_file = fs_path / "_yak" / "health" / "app.py"
        if not health_file.is_file():
            return HealthResult.green()
        tree_path = str(node.path)
        mod = self._load_health_module(health_file, tree_path=tree_path)
        if mod is None or not hasattr(mod, "run"):
            return HealthResult.green()

        assert node
        space = NodeSpace(
            path=node.path,
            request=None,  # type: ignore
            session=None,  # type: ignore
            ports=node.ports,
            ports_from=lambda: node.ports,  # type: ignore
        )
        result = mod.run(space)
        if inspect.iscoroutine(result):
            return await result
        return result

    def _load_health_module(
        self, path: Path, *, tree_path: str
    ) -> types.ModuleType | None:
        segments = [s for s in tree_path.strip("/").split("/") if s]
        entry_name = path.stem

        full_name = "yak.bundle." + ".".join(segments + ["health", entry_name])
        cap_pkg = "yak.bundle." + ".".join(segments + ["health"])

        seen = ""
        for part in full_name.split("."):
            seen = f"{seen}.{part}" if seen else part
            if seen not in sys.modules:
                pkg = types.ModuleType(seen)
                pkg.__package__ = seen
                sys.modules[seen] = pkg

        sys.modules[cap_pkg].__path__ = [str(path.parent)]

        spec = importlib.util.spec_from_file_location(full_name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        return mod

    def _load_module(
        self, path: Path, *, tree_path: str, phase: str
    ) -> types.ModuleType | None:
        loaded = self._loaded_modules.get(path)
        if loaded is not None:
            return loaded

        segments = [s for s in tree_path.strip("/").split("/") if s]
        entry_name = path.stem

        full_name = "yak.bundle." + ".".join(segments + [phase, entry_name])
        cap_pkg = "yak.bundle." + ".".join(segments + [phase])

        import sys

        seen = ""
        for part in full_name.split("."):
            seen = f"{seen}.{part}" if seen else part
            if seen not in sys.modules:
                pkg = types.ModuleType(seen)
                pkg.__package__ = seen
                sys.modules[seen] = pkg

        sys.modules[cap_pkg].__path__ = [str(path.parent)]

        spec = importlib.util.spec_from_file_location(full_name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        self._loaded_modules[path] = mod
        return mod
