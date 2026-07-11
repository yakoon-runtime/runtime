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
    constructs a Node tree.  Each Node's ports context is assembled
    top-down (root first, children last) so that every node inherits
    its parent's capabilities at construction time — not at resolution
    time.

    Usage::

        tree = Tree(root_path="bundles/root", root_ports=platform.ports)
        tree.build()

        node = tree.find("/usr/bin/ls")   # → Node with ready Ports
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
        yak_dirs: list[Path] = sorted(
            p.parent.parent for p in self._root_path.rglob(".yak/yak.yml")
        )

        raw: dict[str, Node] = {}

        for dir_path in yak_dirs:
            if dir_path == self._root_path:
                continue
            rel = str(dir_path.relative_to(self._root_path))
            meta = _read_yaml(dir_path / ".yak" / "yak.yml")

            node = Node(
                key=dir_path.name,
                name=meta.get("title", dir_path.name),
                resolvable=meta.get("resolvable", True),
                navigable=meta.get("navigable", True),
                contextual=meta.get("contextual", False),
                anonymous=True,
            )

            # Read run capability
            run_meta = _read_yaml(dir_path / ".yak" / "run" / "yak.yml")
            if run_meta:
                executor = run_meta.get("executor", "python")
                entry = run_meta.get("entry", f"{executor}.py")
                run_file = dir_path / ".yak" / "run" / entry
                if run_file.is_file():
                    mod = _load_module(f"_bundle_{dir_path.name}", run_file)
                    if mod and hasattr(mod, "run"):
                        node.run = mod.run

            raw[rel] = node

        # Sort by depth so parents are created before children
        sorted_rels = sorted(raw.keys(), key=lambda r: len(Path(r).parts))

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
            node = raw[rel_str]
            parent_rel = str(Path(rel_str).parent)
            parent = self._nodes.get(parent_rel) or self._root
            parent.add(node)
            self._nodes[f"/{rel_str}"] = node

        # Assemble context top-down
        self._assemble_context(self._root, self._root_path)

    def _assemble_context(self, node: Node, dir_path: Path | None) -> None:
        if dir_path:
            setup_dir = dir_path / ".yak" / "setup"
            setup_meta = _read_yaml(setup_dir / "yak.yml")
            if setup_meta:
                executor = setup_meta.get("executor", "python")
                entry = setup_meta.get("entry", f"{executor}.py")
                setup_file = setup_dir / entry
                if setup_file.is_file():
                    mod = _load_module(f"_tree_setup_{node.key}", setup_file)
                    if mod and hasattr(mod, "configure"):
                        mod.configure(node.ports)

        for child_key, child_node in node.children.items():
            child_path = (dir_path / child_key) if dir_path else None
            self._assemble_context(child_node, child_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def root(self) -> Node | None:
        return self._root

    def find(self, path: str) -> Node | None:
        node = self._nodes.get(path)
        if node:
            return node
        # Fallback: global commands (ls, cd) found by key
        key = path.rsplit("/", 1)[-1]
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
        self._assemble_context(node, dir_path)


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
