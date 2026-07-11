from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from y5n.base.nodes import Invocation, Node, Param
from y5n.base.nodes.ports import NodePorts

# Resource types that capabilities can declare in yak.yml.
# Each entry becomes a node.resources[type][variant] → Path mapping.
RESOURCE_KEYS = frozenset({"projection", "man"})


@dataclass
class Mount:
    """A single tree mount point.

    Maps a namespace prefix in the logical tree to a physical
    filesystem path.  The runtime composes its node tree by
    iterating all mounts and building a unified namespace.
    """

    namespace: str
    """Logical namespace under which this mount appears (e.g. "/", "/luma")."""

    path: Path
    """Filesystem path to scan for .yak/ directories."""

    def __post_init__(self):
        self.path = Path(self.path).resolve()
        if not self.namespace.startswith("/"):
            self.namespace = "/" + self.namespace


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
    """Loaded capability with its module, invocations and resource paths."""

    module: object | None = None
    """The loaded Python module, or None if load failed."""

    invocations: list[Invocation] = field(default_factory=list)
    """Parsed invocation definitions from yak.yml."""

    resources: dict[str, dict[str, Path]] = field(default_factory=dict)
    """Resource file paths resolved from yak.yml, keyed by type then variant."""


class Tree:
    """Compiled index of .yak/ directories.

    Scans a filesystem root for .yak/ directories at build time and
    constructs a Node tree with fully assembled Ports and search paths.
    """

    def __init__(self, root_ports: NodePorts, mounts: list[Mount]):
        self._root_ports = root_ports
        self._mounts = mounts
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

    def _scan(self) -> list[tuple[str, Path]]:
        result: list[tuple[str, Path]] = []
        for mount in self._mounts:
            for p in mount.path.rglob(".yak/yak.yml"):
                bundle_dir = p.parent.parent
                if bundle_dir == mount.path:
                    continue
                rel = bundle_dir.relative_to(mount.path)
                if mount.namespace == "/":
                    tree_path = "/" + str(rel)
                else:
                    tree_path = mount.namespace + "/" + str(rel)
                result.append((tree_path, bundle_dir))
        return sorted(result, key=lambda x: x[0])

    # ------------------------------------------------------------------
    # Phase 2 – Create
    # ------------------------------------------------------------------

    def _create_nodes(self, entries: list[tuple[str, Path]]) -> dict[str, Node]:
        nodes: dict[str, Node] = {}
        for tree_path, dir_path in entries:
            nodes[tree_path] = self._build_node(dir_path)
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
        if cap:
            if cap.module and hasattr(cap.module, "run"):
                node.run = cap.module.run  # type: ignore
            node.invocations = cap.invocations
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

        # Parse invocation
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
                    default=inv_data.get("default", True),
                )
            )

        # Parse resources
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

        return Capability(module=mod, invocations=invocations, resources=resources)

    # ------------------------------------------------------------------
    # Phase 3 – Link
    # ------------------------------------------------------------------

    def _link_nodes(self, created: dict[str, Node]) -> None:
        sorted_paths = sorted(created.keys(), key=lambda r: len(Path(r).parts))

        # Read root meta from the "/" namespace mount
        root_meta: dict[str, Any] = {}
        for m in self._mounts:
            if m.namespace == "/":
                root_meta = _read_yaml(m.path / ".yak" / "yak.yml")
                break

        self._root = Node(
            key="/",
            name=root_meta.get("title", "root"),
            resolvable=False,
            navigable=True,
            ports=self._root_ports.fork(),
        )
        self._nodes["/"] = self._root

        for tree_path in sorted_paths:
            node = created[tree_path]
            parent_path = str(Path(tree_path).parent)
            parent = self._nodes.get(parent_path) or self._root
            parent.mount(node)
            self._nodes[tree_path] = node

    # ------------------------------------------------------------------
    # Phase 4 – Assemble
    # ------------------------------------------------------------------

    def _assemble(self) -> None:
        assert self._root
        self._assemble_node(self._root, BuildState())

    def _assemble_node(self, node: Node, state: BuildState) -> None:
        current = BuildState(search_paths=list(state.search_paths))

        fs_path = self._fs_path_from_node(node)
        if fs_path:
            self._merge_search_paths(node, fs_path, current)
            self._run_setup(node, fs_path)

        node.search_paths = current.search_paths

        for child_node in node.children.values():
            self._assemble_node(child_node, current)

    def _merge_search_paths(
        self, node: Node, dir_path: Path, state: BuildState
    ) -> None:
        path_file = dir_path / ".yak" / "path"
        if not path_file.is_file():
            return
        node_path = self._tree_path_from_node(node)
        if node_path is None:
            return
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

    def _resolve_fs_path(self, tree_path: str) -> Path | None:
        """Map a logical tree path to the physical filesystem path
        using the longest matching mount namespace."""
        best: tuple[int, Path] | None = None
        for mount in self._mounts:
            ns = mount.namespace
            if ns == "/":
                remainder = tree_path.lstrip("/") if tree_path != "/" else ""
                score = 0
            elif tree_path == ns:
                remainder = ""
                score = len(ns)
            elif tree_path.startswith(ns + "/"):
                remainder = tree_path[len(ns) + 1 :]
                score = len(ns)
            else:
                continue
            fs_path = mount.path / remainder if remainder else mount.path
            if best is None or score > best[0]:
                best = (score, fs_path)
        return best[1] if best else None

    def _fs_path_from_node(self, node: Node) -> Path | None:
        for tree_path, n in self._nodes.items():
            if n is node:
                return self._resolve_fs_path(tree_path)
        return None

    def _tree_path_from_node(self, node: Node) -> str | None:
        for tree_path, n in self._nodes.items():
            if n is node:
                return tree_path
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        self._assemble_node(node, BuildState(search_paths=node.search_paths))


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
