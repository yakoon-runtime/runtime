from typing import Any

from y5n.base.nodes.node import Node
from y5n.base.nodes.path import NodePath
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

        self._resolvers = {
            "by-key": self._resolve_by_key,
            "children": self._resolve_children,
        }

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

    def _resolve_by_key(self, request: DataRequest) -> DataResult:

        raw = request.option("by-key")
        path = NodePath.from_string(raw)

        node = self._root.find(path)

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



    # ---------------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------------

    def _to_row(self, node: Node) -> dict[str, Any]:

        return {
            "key": node.key,
            "name": node.name,
            "listed": node.listed,
            "navigable": node.navigable,
            "resolvable": node.resolvable,
            "kind": str(node.kind),
            "visibility": str(node.visibility),
            "parent": node.parent.key if node.parent else None,
            "path": node.path,
        }
