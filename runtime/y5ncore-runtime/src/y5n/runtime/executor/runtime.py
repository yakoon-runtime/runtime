from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

from y5n.runtime.engine.flow.dsl import Outcome
from y5n.runtime.engine.nodes.space import NodeSpace

from .base import (
    DiagnosticExecutor,
    Executor,
    ExecutorKind,
    HealthResult,
    Phase,
    RunResult,
)

if TYPE_CHECKING:
    from y5n.runtime.engine.nodes.node import Node


def _parse_entry(entry: str) -> tuple[str, str]:
    if ":" in entry:
        scheme, _, rest = entry.partition(":")
        if scheme in ("pack", "file"):
            return (scheme, rest)
    raise ValueError(
        f"invalid entry '{entry}' — expected 'pack:<module>:<func>' or 'file:<path>'"
    )


def _empty() -> RunResult:
    async def _noop():
        yield Outcome()

    return _noop()


class RuntimeExecutor(Executor, DiagnosticExecutor):

    kind = ExecutorKind.RUNTIME

    def __init__(self):
        self._loaded_modules: dict[Path, types.ModuleType] = {}
        self._root_ports = None

    def _entry_value(self, node: Node, phase: Phase) -> str | None:
        entry = node.metadata.get("entry", {})
        if not isinstance(entry, dict):
            return None
        return entry.get(phase.value)

    def _handle_module_entry(
        self, value: str, space: NodeSpace
    ) -> RunResult | None:
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

    def _entry_file(
        self, node: Node, phase: Phase, file_path: str | None = None
    ) -> Path | None:
        fs_path = node.fs_path
        if fs_path is None:
            return None

        if file_path:
            candidate = fs_path / file_path
            if candidate.is_file():
                return candidate
            return None
        entry_path = self._entry_value(node, phase)
        if entry_path:
            candidate = fs_path / entry_path
            if candidate.is_file():
                return candidate
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

        scheme, value = _parse_entry(entry)

        if scheme == "pack":
            return self._handle_module_entry(value, space)

        if scheme == "file":
            app_file = self._entry_file(node, phase, value)
            if app_file is None:
                return _empty()
            os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
            tree_path = str(node.path)
            mod = self._load_module(
                app_file, tree_path=tree_path, phase=phase.value
            )
            if mod is not None:
                if hasattr(mod, "run"):
                    return mod.run(space)
                if hasattr(mod, "main"):
                    return mod.main()
            return _empty()

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

        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")

        segments = [s for s in tree_path.strip("/").split("/") if s]
        entry_name = path.stem

        full_name = "yak.bundle." + ".".join(segments + [phase, entry_name])
        cap_pkg = "yak.bundle." + ".".join(segments + [phase])

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
