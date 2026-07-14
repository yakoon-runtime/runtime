from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from y5n.base.nodes import Invocation, Node, Param
from y5n.base.nodes.ports import NodePorts
from y5n.base.nodes.space import NodeSpace
from y5n.base.ports.models import HealthLevel, HealthResult
from y5n.base.runtime import Container
from y5n.runtime.executor import (
    Executor,
    ExecutorKind,
    ExecutorRegistry,
    Phase,
)

# Resource types that capabilities can declare in yak.yml.
# Each entry becomes a node.resources[type][variant] to Path mapping.
RESOURCE_KEYS = frozenset({"projection", "man"})


@dataclass
class BuildState:
    """Accumulated inherited context during tree assembly.
    Carried top-down through the node hierarchy.
    """

    search_paths: list[str] = field(default_factory=list)


@dataclass
class Capability:
    """Bundle metadata: invocations and resource paths."""

    executor_kind: ExecutorKind = ExecutorKind.PYTHON
    invocations: list[Invocation] = field(default_factory=list)
    resources: dict[str, dict[str, Path]] = field(default_factory=dict)


class Tree:
    """Compiled index of _yak/ directories.

    Scans root_path recursively for _yak/ directories and constructs
    a Node tree.  Symlinks in the filesystem are followed during scan,
    so bundles can be linked into the tree from external locations.
    """

    def __init__(
        self,
        root_path: str | Path,
        executors: ExecutorRegistry,
        root_ports: NodePorts | None = None,
    ):
        self._root_path = Path(root_path).resolve()
        self._root_ports = root_ports or NodePorts(
            Container(allow_override=False),
            Container(allow_override=True),
        )
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
        """
        result: list[Path] = []
        for dirpath, _dirnames, filenames in os.walk(self._root_path, followlinks=True):
            p = Path(dirpath)
            if p.name == "_yak" and "yak.yml" in filenames:
                bundle_dir = p.parent
                if bundle_dir != self._root_path:
                    result.append(bundle_dir)
        return sorted(result)

    def _create_nodes(self, dirs: list[Path]) -> dict[str, Node]:
        nodes: dict[str, Node] = {}
        for dir_path in dirs:
            rel = str(dir_path.relative_to(self._root_path))
            nodes[rel] = self._build_node(dir_path)
        return nodes

    def _build_node(self, dir_path: Path) -> Node:
        meta = _read_yaml(dir_path / "_yak" / "yak.yml")
        node = Node(
            key=dir_path.name,
            name=meta.get("title", dir_path.name),
            resolvable=meta.get("resolvable", True),
            navigable=meta.get("navigable", True),
            contextual=meta.get("contextual", False),
            anonymous=True,
            fs_path=dir_path,
        )
        cap = self._load_capability(dir_path / "_yak" / "run")
        if cap:
            node.invocations = cap.invocations
            node.resources = cap.resources
            node.metadata["executor"] = cap.executor_kind.value
            executor = self._executors.get(cap.executor_kind)
            node.run = _make_handler(executor, node, Phase.RUN)
        return node

    def _load_capability(self, cap_dir: Path) -> Capability | None:
        meta = _read_yaml(cap_dir / "yak.yml")
        if not meta:
            return None
        executor_kind = ExecutorKind(meta.get("executor", "python"))

        invocations: list[Invocation] = []
        inv_data = meta.get("invocation")
        if isinstance(inv_data, dict):
            params: list[Param] = []
            for p in inv_data.get("params", []):
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
            invocations.append(
                Invocation(
                    action=inv_data.get("action"),
                    params=params,
                    min_options=inv_data.get("min_options", 0),
                    default=inv_data.get("default", True),
                )
            )

        resources: dict[str, dict[str, Path]] = {}
        for res_type in RESOURCE_KEYS:
            variants = meta.get(res_type)
            if not isinstance(variants, dict):
                continue
            resolved: dict[str, Path] = {}
            for variant, filename in variants.items():
                fpath = (cap_dir / filename).resolve()
                if fpath.is_file():
                    resolved[variant] = fpath
            if resolved:
                resources[res_type] = resolved

        return Capability(
            executor_kind=executor_kind,
            invocations=invocations,
            resources=resources,
        )

    def _link_nodes(self, created: dict[str, Node]) -> None:
        sorted_rels = sorted(created.keys(), key=lambda r: len(Path(r).parts))

        root_meta = _read_yaml(self._root_path / "_yak" / "yak.yml")
        self._root = Node(
            key="/",
            name=root_meta.get("title", "root"),
            resolvable=False,
            navigable=True,
            ports=self._root_ports.fork(),
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
        path_file = dir_path / "_yak" / "path"
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
            fs_path = node.fs_path or self._root_path
            meta = _read_yaml(fs_path / "_yak" / "setup" / "yak.yml")
            if not meta:
                continue
            app_file = fs_path / "_yak" / "setup" / "app.py"
            if not app_file.is_file():
                continue
            kind = ExecutorKind(meta.get("executor", "python"))
            executor = self._executors.get(kind)
            if executor is None:
                continue
            space = NodeSpace(
                path=node.path,
                request=None,  # type: ignore
                session=None,  # type: ignore
                ports=node.ports,
                ports_from=lambda: node.ports,  # type: ignore  # noqa: B023
            )
            result = executor.run(node, Phase.SETUP, space)
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
          - app.py exists for declared phases
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
            for phase in ("run", "setup"):
                phase_dir = fs_path / "_yak" / phase
                meta = _read_yaml(phase_dir / "yak.yml")
                if not meta:
                    continue
                kind_name = meta.get("executor", "python")
                try:
                    kind = ExecutorKind(kind_name)
                except ValueError:
                    issues.append(f"{phase}: unknown executor '{kind_name}'")
                    continue
                try:
                    self._executors.get(kind)
                except KeyError:
                    issues.append(f"{phase}: executor '{kind_name}' not registered")
                    continue
                app_file = phase_dir / "app.py"
                if not app_file.is_file():
                    issues.append(f"{phase}: app.py not found")

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
    def _run(space):
        return executor.run(node, phase, space)

    return _run
