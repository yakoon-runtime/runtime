from __future__ import annotations

from yakoon.base.runtime import Container

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

    def publish(self, port, capability):
        """Publishes a capability into the parent runtime scope.

        Published capabilities become visible to the direct
        parent runtime space.

        Args:
            port:
                The capability port.

            capability:
                The bound capability implementation.
        """
        self._publish_to.bind(port, capability)

    def provide(self, port, capability):
        """Provides a capability inside the local runtime scope.

        Provided capabilities remain local to the current
        runtime hierarchy and are inherited by child nodes.

        Args:
            port:
                The capability port.

            capability:
                The bound capability implementation.
        """
        self._local.bind(port, capability)

    def get(self, port):
        """Resolves a capability from the local hierarchy.

        Resolution follows hierarchical scope lookup:

            current node
            -> parent node
            -> root node

        Args:
            port:
                The capability port.

        Returns:
            The resolved capability implementation.
        """
        return self._local.get(port)

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
