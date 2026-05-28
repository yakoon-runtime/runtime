from typing import Any

from y5n.base.nodes.node import Node
from y5n.base.nodes.path import NodePath
from y5n.base.nodes.types import NodeScope
from y5n.base.sources import DataRequest, DataResult, DataSource


class NodeSource(DataSource):
    """Query interface for the runtime node graph.

    NodeSource provides structured runtime introspection over
    the composed semantic runtime world.

    The source exposes filtered views onto the internal runtime
    topology without leaking actual runtime objects. Results are
    always returned as serializable data rows.

    Query model:
        Exactly one selector must be provided.

    Supported selectors:

        --shell
            Returns the shell runtime node.

        --globals
            Returns globally visible runtime nodes.

        --roots
            Returns visible runtime nodes with root scope.

        --by-key <key-path>
            Resolves a runtime node by canonical runtime path.

        --children [<key-path>]
            Returns direct runtime child nodes.

            If omitted, children of the platform root
            are returned.

        --scope [<key-path>]
            Visibility resolution follows runtime scope semantics:

            - direct child nodes are always visible
            - GLOBAL nodes are visible everywhere
            - ROOT nodes are visible only from the runtime root

    """

    def __init__(self, root: Node):

        self._root = root
        self._shell: Node | None = None
        self._globals: dict[str, Node] = {}
        self._roots: dict[str, Node] = {}

        self._resolvers = {
            "shell": self._resolve_shell,
            "globals": self._resolve_globals,
            "roots": self._resolve_roots,
            "by-key": self._resolve_by_key,
            "children": self._resolve_children,
            "scope": self._resolve_scope,
        }

        self._build()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def read(self, request: DataRequest) -> DataResult:

        if not request.args():
            return DataResult.invalid(reason="empty query")

        key = self._select(request)
        if isinstance(key, DataResult):
            return key

        handler = self._resolvers[key]
        return handler(request)

    # ---------------------------------------------------------------------
    # Selector Resolution
    # ---------------------------------------------------------------------

    def _select(self, request: DataRequest) -> str | DataResult:

        matches = [k for k in self._resolvers if request.has_option(k)]

        if not matches:
            return DataResult.invalid(reason="no selector")

        if len(matches) > 1:
            return DataResult.invalid(reason="multiple selectors")

        return matches[0]

    # ---------------------------------------------------------------------
    # Resolver Implementations
    # ---------------------------------------------------------------------

    def _resolve_shell(self, request: DataRequest) -> DataResult:

        assert self._shell
        return DataResult.ok(rows=[self._to_row(self._shell)])

    def _resolve_globals(self, request: DataRequest) -> DataResult:

        return DataResult.ok(rows=[self._to_row(n) for n in self._globals.values()])

    def _resolve_roots(self, request: DataRequest) -> DataResult:

        return DataResult.ok(rows=[self._to_row(n) for n in self._roots.values()])

    def _resolve_by_key(self, request: DataRequest) -> DataResult:

        raw = request.option("by-key")
        path = NodePath.from_string(raw)

        # ---------------------------------
        # Direct tree resolution
        # ---------------------------------

        node = self._root.find(path)

        # ---------------------------------
        # Global nodes
        # ---------------------------------

        if not node:
            node = self._globals.get(path.last or "")

        # ---------------------------------
        # Root-visible nodes
        # ---------------------------------

        if not node and path.parent == NodePath.root():
            node = self._roots.get(path.last or "")

        # ---------------------------------
        # Not found
        # ---------------------------------

        if not node:
            return DataResult.not_found(id=str(path))

        return DataResult.ok(rows=[self._to_row(node)])

    def _resolve_children(self, request: DataRequest) -> DataResult:

        raw = request.option("children")

        # Root children.
        if not raw:
            return DataResult.ok(
                rows=[self._to_row(child) for child in self._root.children.values()]
            )

        path = NodePath.from_string(raw)

        node = self._root.find(path)
        if not node:
            return DataResult.not_found(id=str(path))

        return DataResult.ok(
            rows=[self._to_row(child) for child in node.children.values()]
        )

    def _resolve_scope(self, request: DataRequest) -> DataResult:
        """Returns runtime nodes visible from a runtime space.

        Visibility resolution follows runtime scope semantics:

        - direct child nodes are always visible
        - GLOBAL nodes are visible everywhere
        - ROOT nodes are visible only from the runtime root

        Duplicate runtime nodes are automatically removed.

        Query:
            --scope [<key-path>]

        If no key-path is provided, the platform root
        is used.
        """

        raw = request.option("scope")

        # Default to runtime root.
        node = self._root

        if raw:

            path = NodePath.from_string(raw)

            resolved = self._root.find(path)
            if not resolved:
                return DataResult.not_found(id=str(path))

            node = resolved

        visible: dict[str, Node] = {}

        # ---------------------------------
        # Direct child nodes
        # ---------------------------------

        for child in node.children.values():

            if child.listed:  # resolvable:
                visible[str(child)] = child

        # ---------------------------------
        # Global nodes
        # ---------------------------------

        for global_node in self._globals.values():

            visible[str(global_node)] = global_node

        # ---------------------------------
        # Root-visible nodes
        # ---------------------------------

        if node == self._root:

            for root_node in self._roots.values():

                visible[str(root_node)] = root_node

        return DataResult.ok(rows=[self._to_row(n) for n in visible.values()])

    # ---------------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------------

    def _build(self):

        globals_: dict[str, Node] = {}
        roots_: dict[str, Node] = {}

        def collect(node: Node):

            if node.is_shell:
                if self._shell is not None:
                    raise ValueError("Duplicate shell node")
                self._shell = node

            if node.scope == NodeScope.GLOBAL:
                if node.key in globals_:
                    raise ValueError(f"GLOBAL conflict: {node.key}")
                globals_[node.key] = node

            if node.scope == NodeScope.ROOT:
                if node.key in roots_:
                    raise ValueError(f"ROOT conflict: {node.key}")
                roots_[node.key] = node

        self._root.walk(collect)

        self._globals = globals_
        self._roots = roots_

    def _to_row(self, node: Node) -> dict[str, Any]:

        return {
            "key": node.key,
            "name": node.name,
            "listed": node.listed,
            "navigable": node.navigable,
            "resolvable": node.resolvable,
            "is_shell": node.is_shell,
            "kind": str(node.kind),
            "scope": str(node.scope),
            "visibility": str(node.visibility),
            "parent": node.parent.key if node.parent else None,
            "path": node.path,
        }
