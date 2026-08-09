"""Store profile collection (ADR-18).

The tree *describes* the installed components; it does not answer domain
questions about them. Collectors walk the nodes and evaluate their declared
needs. ``StoreCollector`` collects the logical store names the installed
packs declare — the names the deployment must provide. What each name means
(backend, instance) is deployment knowledge.
"""

from __future__ import annotations

from y5n.runtime.engine.nodes.tree import Tree


class StoreCollector:
    """Collect the declared store profiles across the installed packs."""

    def __init__(self, tree: Tree) -> None:
        self._tree = tree

    def collect(self) -> list[str]:
        """Return the sorted, de-duplicated logical store names."""
        return sorted(
            {node.store for node in self._tree.iter_nodes() if node.store is not None}
        )
