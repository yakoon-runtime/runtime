from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml
from y5n.base.nodes import Node
from y5n.base.nodes.ports import NodePorts


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
    # Build
    # ------------------------------------------------------------------

    def build(self) -> None:
        yak_dirs = sorted(
            p.parent.parent for p in self._root_path.rglob(".yak/yak.yml")
        )

        pending: dict[str, Node] = {}

        for dir_path in yak_dirs:
            if dir_path == self._root_path:
                continue
            rel = str(dir_path.relative_to(self._root_path))
            pending[rel] = self._build_node(dir_path)

        # Sort by depth so parents are created before children
        sorted_rels = sorted(pending.keys(), key=lambda r: len(Path(r).parts))

        # Build root node
        root_meta = _read_yaml(self._root_path / ".yak" / "yak.yml")
        self._root = Node(
            key="/",
            name=root_meta.get("title", "root"),
            resolvable=False,
            navigable=True,
            ports=self._root_ports.fork(),
        )
        self._nodes["/"] = self._root

        # Attach children to parents
        for rel_str in sorted_rels:
            node = pending[rel_str]
            parent_rel = str(Path(rel_str).parent)
            parent_key = f"/{parent_rel}" if parent_rel != "." else "/"
            parent = self._nodes.get(parent_key) or self._root
            parent.add(node)
            self._nodes[f"/{rel_str}"] = node

        # Assemble context top-down
        self._assemble_recursive(self._root, self._root_path)

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
        mod = self._load_capability(dir_path / ".yak" / "run")
        if mod and hasattr(mod, "run"):
            node.run = mod.run
        return node

    def _load_capability(self, cap_dir: Path) -> object | None:
        meta = _read_yaml(cap_dir / "yak.yml")
        if not meta:
            return None
        executor = meta.get("executor", "python")
        entry = meta.get("entry", f"{executor}.py")
        entry_file = cap_dir / entry
        if not entry_file.is_file():
            return None
        return _load_module(f"_cap_{cap_dir.parent.parent.name}_{cap_dir.name}", entry_file)

    def _assemble_recursive(
        self,
        node: Node,
        dir_path: Path | None,
        inherited: list[str] | None = None,
    ) -> None:
        if inherited is None:
            inherited = []

        paths = list(inherited)

        if dir_path:
            self._merge_search_paths(node, dir_path, paths)
            self._run_setup(node, dir_path)

        node.search_paths = paths

        for child_key, child_node in node.children.items():
            child_path = (dir_path / child_key) if dir_path else None
            self._assemble_recursive(child_node, child_path, paths)

    def _merge_search_paths(self, node: Node, dir_path: Path, paths: list[str]) -> None:
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
            paths.insert(0, tree_path)

    def _run_setup(self, node: Node, dir_path: Path) -> None:
        mod = self._load_capability(dir_path / ".yak" / "setup")
        if mod and hasattr(mod, "configure"):
            mod.configure(node.ports)

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

    def resolve(self, parent_path: str, key: str) -> Node | None:
        full = f"/{key}" if parent_path == "/" else f"{parent_path}/{key}"

        node = self._nodes.get(full)
        if node:
            return node

        parent = self._nodes.get(parent_path)
        if parent is not None:
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
        self._assemble_recursive(node, dir_path)


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
