from __future__ import annotations

from typing import Any, TypeVar, overload

from y5n.runtime.api.ports import Port
from y5n.runtime.api.runtime import Container

T = TypeVar("T")

# ----------------------------------
# NODE PORTS
# ----------------------------------


class NodePorts:
    """Hierarchical capability scope for a runtime node.

    A NodePorts instance defines the capability visibility
    of a semantic runtime space.

    Capabilities are separated into two directions:

    - local:
        Private capabilities visible inside the current
        runtime hierarchy through hierarchical lookup.

    - publish:
        Export target for capabilities exposed to the
        direct parent runtime space.

    Child nodes inherit the local hierarchy while publishing
    upward into the current node scope.
    """

    def __init__(
        self,
        publish_to: Container,
        local: Container,
    ):
        """Creates a new capability scope.

        Args:
            publish_to:
                Parent capability target used for upward exports.

            local:
                Local hierarchical capability scope.
        """
        self._publish_to = publish_to
        self._local = local

    # ----------------------------------
    # PUBLIC API
    # ----------------------------------

    def publish(self, port: object, capability: object) -> None:
        """Publishes a capability into the parent runtime scope.

        Published capabilities become visible to the direct
        parent runtime space.

        Args:
            port:     The capability port (Port object or class).
            capability:  The bound capability implementation.
        """
        self._publish_to.bind(self._key(port), capability)

    def promote(self, port: object, capability: object) -> None:
        """Promotes a capability to the root scope.

        The capability is visible from any node in the tree,
        regardless of branch.  Intended for cross-branch services
        like authentication that need global reach.

        Args:
            port:     The capability port (Port object or class).
            capability:  The bound capability implementation.
        """
        key = self._key(port)
        walk = self._publish_to
        while walk._parent is not None:
            walk = walk._parent
        walk.bind(key, capability)

    def provide(self, port: object, capability: object) -> None:
        """Provides a capability inside the local runtime scope.

        Provided capabilities remain local to the current
        runtime hierarchy and are inherited by child nodes.

        For Port objects the registry key is the port name (a string);
        the protocol class is additionally registered as a fallback key
        for backwards compatibility.

        Args:
            port:     The capability port (Port object or class).
            capability:  The bound capability implementation.
        """
        key = self._key(port)
        self._local.bind(key, capability)
        if isinstance(port, Port) and port.protocol:
            self._local.bind(port.protocol, capability)

    @overload
    def get(self, port: Port[T]) -> T: ...

    @overload
    def get(self, port: type[T]) -> T: ...

    def get(self, port: Port[T] | type[T]) -> Any:
        """Resolves a capability from the local hierarchy.

        Resolution follows hierarchical scope lookup:

            current node
            -> parent node
            -> root node

        Args:
            port:  The capability port (Port object or class).

        Returns:
            The resolved capability implementation.
        """
        return self._local.get(self._key(port))

    def has(self, port: object) -> bool:
        """Returns True if the capability *port* is available in the hierarchy."""
        return self._local.has(port=self._key(port))

    @staticmethod
    def _key(port) -> object:
        if isinstance(port, Port):
            return port.name
        return port

    # ----------------------------------
    # FORK
    # ----------------------------------

    def fork(self) -> NodePorts:
        """Creates a child capability scope.

        Child scopes inherit the local hierarchy while
        publishing upward into the current node scope.

        Returns:
            A forked capability scope.
        """

        return NodePorts(
            publish_to=self._local,
            local=self._local.fork(),
        )

    # ----------------------------------
    # ATTACH
    # ----------------------------------

    def mount(self, parent: NodePorts) -> None:
        """Mountes the local hierarchy to a parent runtime scope.

        The existing local scope chain remains intact while
        extending hierarchical lookup into the parent runtime.

        Args:
            parent:
                Parent runtime scope.
        """

        # Extend hierarchical lookup.
        self._local.mount(parent._local)

        # Redirect upward exports into parent scope.
        self._publish_to = parent._local
