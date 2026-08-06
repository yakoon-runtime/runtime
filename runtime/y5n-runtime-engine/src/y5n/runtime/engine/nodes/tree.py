from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from y5n.runtime.api.ports.models import HealthLevel, HealthResult
from y5n.runtime.api.runtime.invocation import CommandSignature, Param
from y5n.runtime.engine.bootstrap import PackReference
from y5n.runtime.engine.executor import (
    Executor,
    ExecutorKind,
    ExecutorRegistry,
    Phase,
)
from y5n.runtime.engine.flow.util import empty_flow
from y5n.runtime.engine.nodes import Node

# Resource types that capabilities can declare in yak.yml.
# Each entry becomes a node.resources[type][variant] to reference string
# mapping (ADR-10); resolution is lazy and host-owned.
RESOURCE_KEYS = frozenset({"document", "man"})


@dataclass
class BuildState:
    """Accumulated inherited context during tree assembly.
    Carried top-down through the node hierarchy.
    """

    search_paths: list[str] = field(default_factory=list)


@dataclass
class Capability:
    """Bundle metadata: executor, host, entry, and resource paths."""

    executor_kind: ExecutorKind = ExecutorKind.RUNTIME
    host: str | None = None
    entry: dict[str, str] = field(default_factory=dict)
    resources: dict[str, dict[str, Path]] = field(default_factory=dict)


class Tree:
    """Compiled index of .yak/ directories.

    Scans root_path recursively for .yak/ directories and constructs
    a Node tree.  Symlinks in the filesystem are followed during scan,
    so bundles can be linked into the tree from external locations.
    """

    def __init__(
        self,
        root_path: str | Path,
        executors: ExecutorRegistry,
    ):
        self._root_path = Path(root_path).resolve()
        self._executors = executors
        self._nodes: dict[str, Node] = {}
        self._root: Node | None = None

    def build(self) -> None:
        dirs = self._scan()
        nodes = self._create_nodes(dirs)
        self._link_nodes(nodes)
        self._assemble()

    def _scan(self) -> list[Path]:
        """Return list of bundle directories under root_path.

        Uses os.walk with followlinks=True so that symlinked
        product bundles (crm, luma, …) are discovered.

        Prunes symlinks that point to directories without any .yak/
        markers to avoid walking large system trees (/home, /etc, …).
        """
        result: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(self._root_path, followlinks=True):
            p = Path(dirpath)
            if p.name == ".yak" and "yak.yml" in filenames:
                bundle_dir = p.parent
                if bundle_dir != self._root_path:
                    result.append(bundle_dir)
            _prune_bare_symlinks(dirnames, p)
        return sorted(result)

    def _create_nodes(self, dirs: list[Path]) -> dict[str, Node]:
        nodes: dict[str, Node] = {}
        for dir_path in dirs:
            rel = str(dir_path.relative_to(self._root_path))
            nodes[rel] = self._build_node(dir_path)
        return nodes

    def _build_node(self, dir_path: Path) -> Node:
        meta = _read_yaml(dir_path / ".yak" / "yak.yml")
        node = Node(
            key=dir_path.name,
            name=meta.get("title", dir_path.name),
            resolvable=meta.get("resolvable", True),
            navigable=meta.get("navigable", True),
            contextual=meta.get("contextual", False),
            anonymous=True,
            fs_path=dir_path,
        )
        node.metadata["version"] = meta.get("version")

        # Backward compat: if .yak/yak.yml has no host/executor/entry,
        # fall back to .yak/run/yak.yml (old structure).
        run_meta = _read_yaml(dir_path / ".yak" / "run" / "yak.yml")
        if (
            run_meta
            and "host" not in meta
            and "executor" not in meta
            and "entry" not in meta
        ):
            meta = {**meta, **run_meta}

        # Parse host / executor / entry from the same yak.yml
        executor_kind = ExecutorKind(meta.get("executor", "runtime"))
        host = meta.get("host")
        if host:
            executor_kind = ExecutorKind.RUNTIME

        node.metadata["executor"] = executor_kind.value
        if host:
            node.metadata["host"] = host

        entry = meta.get("entry")
        if isinstance(entry, dict):
            node.metadata["entry"] = entry

        # Signatures
        signatures: list[CommandSignature] = []
        sig_data = meta.get("invocation")
        if isinstance(sig_data, dict):
            params: list[Param] = []
            for p in sig_data.get("params", []):
                if isinstance(p, dict):
                    key = p.get("key", "")
                    if key:
                        params.append(
                            Param(
                                key=key,
                                required=p.get("required", False),
                                positional=p.get("positional", False),
                                default=p.get("default"),
                            )
                        )
            signatures.append(
                CommandSignature(
                    action=sig_data.get("action"),
                    params=params,
                    min_options=sig_data.get("min_options", 0),
                    default=sig_data.get("default", True),
                )
            )
        node.signatures = signatures

        resources: dict[str, Any] = {}
        res_section = meta.get("resources")
        if isinstance(res_section, dict) and isinstance(res_section.get("ref"), str):
            resources = res_section
        else:
            # Legacy: top-level document/man sections (per-capability refs).
            legacy: dict[str, Any] = {}
            for res_type in RESOURCE_KEYS:
                variants = meta.get(res_type)
                if isinstance(variants, dict):
                    legacy[res_type] = variants
            resources = legacy
        node.resources = resources

        # Run handler
        if host:
            node.run = _make_dispatch_handler(self, node.key, host)
        else:
            executor = self._executors.get(executor_kind)
            node.run = _make_handler(executor, node, Phase.RUN)

        # Resolve handler — a host declares how it interprets content
        # expressions (ADR-10). Built lazily; no module import at build time.
        resolve_meta = meta.get("resolve")
        if isinstance(resolve_meta, dict):
            resolve_expr = resolve_meta.get("default") or resolve_meta.get("run")
            if isinstance(resolve_expr, str):
                node.resolve = _make_resolve_handler(resolve_expr)

        return node

    def _link_nodes(self, created: dict[str, Node]) -> None:
        sorted_rels = sorted(created.keys(), key=lambda r: len(Path(r).parts))

        root_meta = _read_yaml(self._root_path / ".yak" / "yak.yml")
        self._root = Node(
            key="/",
            name=root_meta.get("title", "root"),
            resolvable=False,
            navigable=True,
            fs_path=self._root_path,
        )
        self._nodes["/"] = self._root

        intermediates: set[str] = set()
        for rel_str in sorted_rels:
            tree_path = f"/{rel_str}"
            parent_path = str(Path(tree_path).parent)
            while parent_path != "/":
                if parent_path not in intermediates and parent_path not in self._nodes:
                    intermediates.add(parent_path)
                parent_path = str(Path(parent_path).parent)

        for ipath in sorted(intermediates, key=lambda p: len(Path(p).parts)):
            key = Path(ipath).name
            implicit = Node(
                key=key,
                name=key,
                resolvable=False,
                navigable=True,
                fs_path=self._root_path / ipath.lstrip("/"),
            )
            self._nodes[ipath] = implicit
            parent_path = str(Path(ipath).parent)
            parent = self._nodes.get(parent_path) or self._root
            parent.mount(implicit)

        for rel_str in sorted_rels:
            node = created[rel_str]
            tree_path = f"/{rel_str}"
            parent_path = str(Path(tree_path).parent)
            parent = self._nodes.get(parent_path) or self._root

            # An implicit intermediate node may already exist for this path
            # (created while linking deeper bundles). Adopt its children so a
            # bundle that is also a mount point keeps its subtree reachable.
            existing = self._nodes.get(tree_path)
            if existing is not None and existing is not node:
                for key, child in existing.children.items():
                    child.parent = node
                    node.children[key] = child

            parent.mount(node)
            self._nodes[tree_path] = node

    def _assemble(self) -> None:
        assert self._root
        self._assemble_node(self._root, self._root_path, BuildState())

    def _assemble_node(
        self, node: Node, dir_path: Path | None, state: BuildState
    ) -> None:
        current = BuildState(search_paths=list(state.search_paths))

        if dir_path:
            self._merge_search_paths(node, dir_path, current)

        node.search_paths = current.search_paths

        for child_node in node.children.values():
            self._assemble_node(child_node, child_node.fs_path, current)

    def _merge_search_paths(
        self, node: Node, dir_path: Path, state: BuildState
    ) -> None:
        path_file = dir_path / ".yak" / "path"
        if not path_file.is_file():
            return
        node_path = self._tree_path(dir_path)
        for line in path_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sub = line[2:] if line.startswith("./") else line
            tree_path = f"/{sub}" if node_path == "/" else f"{node_path}/{sub}"
            state.search_paths.insert(0, tree_path)

    async def setup(self) -> None:
        for node in self._nodes.values():
            entry = node.metadata.get("entry", {})
            setup_path = entry.get("setup")
            if not setup_path:
                continue

            kind = ExecutorKind(node.metadata.get("executor", "runtime"))
            executor = self._executors.get(kind)
            if executor is None:
                continue

            result = executor.run(node, Phase.SETUP)
            if result is not None:
                if hasattr(result, "__await__"):
                    await result  # type: ignore
                else:
                    async for _ in result:  # type: ignore
                        pass

    def _tree_path(self, dir_path: Path) -> str:
        """Map a filesystem path under root_path to its tree path."""
        if dir_path == self._root_path:
            return "/"
        # Use relative_to — works through symlinks because rglob returns
        # paths under root_path even when following symlinks.
        return "/" + str(dir_path.relative_to(self._root_path))

    def root(self) -> Node | None:
        return self._root

    def find(self, path: str) -> Node | None:
        return self._nodes.get(path)

    def find_by_key(self, key: str) -> Node | None:
        for node in self._nodes.values():
            if node.key == key:
                return node
        return None

    def resolve(self, parent: Node, key: str) -> Node | None:
        ppath = str(parent.path)
        full = f"/{key}" if ppath == "/" else f"{ppath}/{key}"

        node = self._nodes.get(full)
        if node:
            return node

        for sp in parent.search_paths:
            node = self._nodes.get(f"{sp}/{key}")
            if node:
                return node

        return None

    def validate(self) -> HealthResult:
        """Structural validation — 0 module imports.

        Checks every node for:
          - yak.yml readable
          - Executor registered
          - entry file exists for declared phases
        """
        root_result = HealthResult.green()
        root_result.message = "Tree validation"

        for path_key, node in sorted(self._nodes.items()):
            fs_path = node.fs_path
            if fs_path is None:
                child = HealthResult.red("No fs_path set")
                child.message = f"{path_key}: no filesystem path"
                root_result.children.append(child)
                continue

            issues: list[str] = []
            meta = _read_yaml(fs_path / ".yak" / "yak.yml")
            entry = meta.get("entry", {}) if meta else {}

            for phase in ("run", "setup"):
                entry_path = entry.get(phase)
                if not entry_path:
                    continue
                if not isinstance(entry_path, str):
                    continue
                if entry_path.startswith("pack:") or entry_path.startswith("file:"):
                    continue
                issues.append(
                    f"{phase}: invalid entry '{entry_path}'"
                    f" — expected 'pack:...' or 'file:...'"
                )

            executor_value = (
                meta.get("host") or meta.get("executor", "") if meta else ""
            )
            if executor_value and not meta.get("host"):
                try:
                    kind = ExecutorKind(executor_value)
                    self._executors.get(kind)
                except (ValueError, KeyError):
                    issues.append(f"unknown executor '{executor_value}'")

            if issues:
                child = HealthResult.yellow("; ".join(issues))
            else:
                child = HealthResult.green()
            child.message = path_key
            root_result.children.append(child)

        if any(
            c.level == HealthLevel.YELLOW or c.level == HealthLevel.RED
            for c in root_result.children
        ):
            root_result.level = HealthLevel.YELLOW
        return root_result

    def refresh(self) -> None:
        self._nodes.clear()
        self._root = None
        self.build()

    def reload(self, path: str) -> None:
        node = self._nodes.get(path)
        if node is None:
            return
        rel = path.lstrip("/")
        dir_path = self._root_path / rel if rel else self._root_path
        self._assemble_node(node, dir_path, BuildState(search_paths=node.search_paths))


def _read_yaml(path: Path) -> dict[str, Any]:
    if path.is_file():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _make_handler(executor: Executor, node: Node, phase: Phase):
    def _run():
        return executor.run(node, phase)

    return _run


def _make_dispatch_handler(tree: Tree, node_key: str, host_path: str):
    """Build a dispatch handler that routes a node to its declared executor.

    A node declares ``host:`` in yak.yml — the runtime's dispatch rule is
    "this node is executed by that node". The handler finds the declared
    node in the tree and runs it. It holds no host knowledge: the target is
    an ordinary node (ADR-12); it reads the invocation from the context.
    """

    def _run():
        host_node = tree.find(host_path)
        if host_node is None or not host_node.has_run():
            return empty_flow()
        host_run = host_node.run
        if host_run is None:
            return empty_flow()
        return host_run()

    return _run


def _make_resolve_handler(resolve_expr: str):
    """Build a node's resolve handler from a ``pack:<module>:<func>`` expression.

    This is bootstrap linking, not interpretation (ADR-10): the runtime loads
    the host's declared resolve function so the host can interpret later
    references. The function is loaded lazily on first call — no module import
    at build time.
    """
    ref = PackReference(resolve_expr)

    async def _resolve(*, node, capability, parameters=None):
        fn = ref.load()
        result = fn(node=node, capability=capability, parameters=parameters or {})
        if inspect.isawaitable(result):
            return await result
        return result

    return _resolve


def _prune_bare_symlinks(dirnames: list[str], parent: Path) -> None:
    """Remove symlinks from os.walk dirnames if target has no .yak/ marker.

    This prevents os.walk with followlinks=True from descending into
    large external trees (like /home via a user mount) that contain
    no Yakoon commands.
    """
    for name in list(dirnames):
        child = parent / name
        if child.is_symlink():
            target = child.resolve()
            if not _has_yak_marker(target):
                dirnames.remove(name)


def _has_yak_marker(path: Path) -> bool:
    """Check if path or any direct child contains a .yak/yak.yml."""
    if (path / ".yak" / "yak.yml").is_file():
        return True
    try:
        for entry in path.iterdir():
            if entry.is_dir() and (entry / ".yak" / "yak.yml").is_file():
                return True
    except PermissionError:
        pass
    return False
