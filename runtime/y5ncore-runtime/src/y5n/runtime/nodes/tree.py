from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from y5n.base.nodes import Node
from y5n.base.nodes.ports import NodePorts


@dataclass
class BuildState:
    """Accumulated inherited context during tree assembly.

    Carried top-down through the node hierarchy. Each level may
    contribute additional entries that are inherited by all children.
    """

    search_paths: list[str] = field(default_factory=list)
    """Search path prefixes inherited from parent levels."""


@dataclass
class Capability:
    """Loaded capability with its module and resource paths."""

    module: object | None = None
    """The loaded Python module, or None if load failed."""

    resources: dict[str, dict[str, Path]] = field(default_factory=dict)
    """Resource file paths resolved from yak.yml, keyed by type then variant."""


class Tree:
    """Compiled index of .yak/ directories.

    Scans a filesystem root for .yak/ directories at build time and
    constructs a Node tree with fully assembled Ports and search paths.
    """

    def __init__(self, root_ports: NodePorts, root_path: str | Path):
        self._root_ports = root_ports
        self._root_path = Path(root_path).resolve()
        self._nodes: dict[str, Node] = {}
        self._root: Node | None = None

    # ------------------------------------------------------------------
    # Build pipeline
    # ------------------------------------------------------------------

    def build(self) -> None:
        dirs = self._scan()
        nodes = self._create_nodes(dirs)
        self._link_nodes(nodes)
        self._assemble()

    # ------------------------------------------------------------------
    # Phase 1 – Scan
    # ------------------------------------------------------------------

    def _scan(self) -> list[Path]:
        return sorted(
            p.parent.parent
            for p in self._root_path.rglob(".yak/yak.yml")
            if p.parent.parent != self._root_path
        )

    # ------------------------------------------------------------------
    # Phase 2 – Create
    # ------------------------------------------------------------------

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
        )
        cap = self._load_capability(dir_path / ".yak" / "run")
        if cap and cap.module and hasattr(cap.module, "run"):
            node.run = cap.module.run  # type: ignore
        if cap:
            node.resources = cap.resources
        return node

    def _load_capability(self, cap_dir: Path) -> Capability | None:
        meta = _read_yaml(cap_dir / "yak.yml")
        if not meta:
            return None
        executor = meta.get("executor", "python")
        entry = meta.get("entry", f"{executor}.py")
        entry_file = cap_dir / entry
        mod = (
            _load_module(
                f"_cap_{cap_dir.parent.parent.name}_{cap_dir.name}", entry_file
            )
            if entry_file.is_file()
            else None
        )

        resources: dict[str, dict[str, Path]] = {}
        for res_type in ("projection", "man"):
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

        return Capability(module=mod, resources=resources)

    # ------------------------------------------------------------------
    # Phase 3 – Link
    # ------------------------------------------------------------------

    def _link_nodes(self, created: dict[str, Node]) -> None:
        sorted_rels = sorted(created.keys(), key=lambda r: len(Path(r).parts))

        root_meta = _read_yaml(self._root_path / ".yak" / "yak.yml")
        self._root = Node(
            key="/",
            name=root_meta.get("title", "root"),
            resolvable=False,
            navigable=True,
            ports=self._root_ports.fork(),
        )
        self._nodes["/"] = self._root

        for rel_str in sorted_rels:
            node = created[rel_str]
            parent_rel = str(Path(rel_str).parent)
            parent_key = f"/{parent_rel}" if parent_rel != "." else "/"
            parent = self._nodes.get(parent_key) or self._root
            parent.add(node)
            self._nodes[f"/{rel_str}"] = node

    # ------------------------------------------------------------------
    # Phase 4 – Assemble
    # ------------------------------------------------------------------

    def _assemble(self) -> None:
        assert self._root
        self._assemble_node(self._root, self._root_path, BuildState())

    def _assemble_node(
        self, node: Node, dir_path: Path | None, state: BuildState
    ) -> None:
        current = BuildState(search_paths=list(state.search_paths))

        if dir_path:
            self._merge_search_paths(node, dir_path, current)
            self._run_setup(node, dir_path)

        node.search_paths = current.search_paths

        for child_node in node.children.values():
            child_dir = self._fs_path_from_node(child_node)
            self._assemble_node(child_node, child_dir, current)

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

    def _run_setup(self, node: Node, dir_path: Path) -> None:
        cap = self._load_capability(dir_path / ".yak" / "setup")
        if cap and cap.module and hasattr(cap.module, "configure"):
            cap.module.configure(node.ports)  # type: ignore

    def _fs_path_from_node(self, node: Node) -> Path | None:
        for key, n in self._nodes.items():
            if n is node:
                if key == "/":
                    return None
                return self._root_path / key.lstrip("/")
        return None

    def _tree_path(self, dir_path: Path) -> str:
        if dir_path == self._root_path:
            return "/"
        return "/" + str(dir_path.relative_to(self._root_path))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def root(self) -> Node | None:
        return self._root

    def find(self, path: str) -> Node | None:
        return self._nodes.get(path)

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

        for node in self._nodes.values():
            if node.key == key:
                return node
        return None

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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _read_yaml(path: Path) -> dict[str, Any]:
    if path.is_file():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
