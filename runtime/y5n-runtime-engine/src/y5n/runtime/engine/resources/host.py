"""Host dispatch for content resolution (ADR-10).

The runtime coordinates: it finds a node's host node and delegates the
capability resolution to the host's ``resolve`` handler. The runtime never
knows which host it is — it only follows the node's ``host:`` path.
"""

from __future__ import annotations

from typing import Any


def find_host(tree, node):
    """Return the host node of ``node``, or ``None``."""
    host_path = node.metadata.get("host") if node is not None else None
    if not host_path:
        return None
    return tree.find(host_path)


async def resolve_via_host(
    tree,
    node,
    capability: str,
    parameters: dict[str, Any] | None = None,
):
    """Resolve a node's capability through its host node's resolve handler."""
    host = find_host(tree, node)
    if host is None or host.resolve is None:
        raise LookupError(f"node '{node.key}' has no host with a resolve capability")
    return await host.resolve(
        node=node,
        capability=capability,
        parameters=parameters or {},
    )
