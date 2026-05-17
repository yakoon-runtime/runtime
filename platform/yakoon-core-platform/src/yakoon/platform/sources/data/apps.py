from collections.abc import Iterable, Sequence
from typing import Any

from yakoon.base.nodes.node import Node
from yakoon.base.sources import DataRequest, DataResult, DataSource


class NodeSource(DataSource):
    """Query interface for the runtime node graph.

    NodeSource provides structured runtime introspection over
    the composed semantic runtime world.

    The source exposes filtered views onto the internal node
    graph without leaking actual runtime objects. Results are
    always returned as serializable data rows.

    Query model:
        Exactly one selector must be provided.

    Supported selectors:
        --all
            Returns all known runtime nodes.

        --listed
            Returns nodes visible in runtime discovery.

        --activatable
            Returns nodes that may become active runtime spaces.

        --shell
            Returns the shell runtime node.

        --by-key <key>
            Resolves a node by its unique runtime key.

        --by-name <name>
            Resolves a node by its semantic display name.
    """

    def __init__(self, nodes: Iterable[Node]):

        self._shell = None
        self._by_key: dict[str, Node] = {}
        self._by_name: dict[str, Node] = {}

        self._nodes = nodes
        self._resolvers = {
            "all": self._resolve_all,
            "listed": self._resolve_listed,
            "activatable": self._resolve_activatable,
            "shell": self._resolve_shell,
            "by-key": self._resolve_by_key,
            "by-name": self._resolve_by_name,
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

    # -----------------------
    # --- Selector Resolution
    # -----------------------

    def _select(self, request: DataRequest) -> str | DataResult:

        matches = [k for k in self._resolvers if request.has_option(k)]
        if not matches:
            return DataResult.invalid(reason="no selector")

        if len(matches) > 1:
            return DataResult.invalid(reason="multiple selectors")

        return matches[0]

    # ------------------------
    # Resolver Implementations
    # ------------------------

    def _resolve_by_key(self, request: DataRequest) -> DataResult:
        node_key = request.option("by-key")

        node = self._get(node_key)
        if not node:
            return DataResult.not_found(id=node_key)

        return DataResult.ok(rows=[self._to_row(node)])

    def _resolve_by_name(self, request: DataRequest) -> DataResult:
        node_name = request.option("by-name")

        node = self._get_by_name(node_name)
        if not node:
            return DataResult.not_found(name=node_name)

        return DataResult.ok(rows=[self._to_row(node)])

    def _resolve_all(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(n) for n in self._all()])

    def _resolve_listed(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(n) for n in self._all() if n.listed])

    def _resolve_activatable(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(n) for n in self._all() if n.navigable])

    def _resolve_shell(self, request: DataRequest) -> DataResult:
        return DataResult.ok(rows=[self._to_row(self._shell)])

    # ----------------
    # Internal Helpers
    # ----------------

    def _build(self):

        by_key: dict[str, Node] = {}
        by_name: dict[str, Node] = {}

        def collect(node: Node):

            if node.key in by_key:
                raise ValueError(f"Duplicate node key: {node.key}")

            if node.is_shell:
                if self._shell is not None:
                    raise ValueError(
                        f"Duplicate shell node: " f"{self._shell.key} / {node.key}"
                    )
                self._shell = node

            by_key[node.key] = node
            if node.name:
                by_name[node.name] = node

        for root in self._nodes:
            root.walk(collect)

        self._by_key = by_key
        self._by_name = by_name

    def _ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_key.keys()))

    def _all(self) -> Sequence[Node]:
        return tuple(self._by_key[cid] for cid in self._ids())

    def _get(self, node_key: str) -> Node | None:
        return self._by_key.get(node_key)

    def _get_by_name(self, node_name: str) -> Node | None:
        return self._by_name.get(node_name)

    def _to_row(self, node: Node) -> dict[str, Any]:
        return {
            "key": node.key,
            "name": node.name,
            "listed": node.listed,
            "activatable": node.navigable,
            "is_shell": node.is_shell,
        }
