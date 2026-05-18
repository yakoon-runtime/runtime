from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from yakoon.base.runtime.container import Container

from .context import RuntimeContext
from .path import NodePath
from .ports import NodePorts
from .resource import ResourceHandler
from .types import NodeKind, NodeScope, NodeVisibility

RunHandler = Callable[[RuntimeContext], Any]

# ----------------------------------
# NODE
# ----------------------------------


@dataclass(slots=True)
class Node:
    """Semantic runtime node.

    A node represents an executable runtime space inside the
    hierarchical platform runtime.

    Nodes may:

    - execute runtime capabilities
    - expose semantic structure
    - define local capability scopes
    - provide child runtime spaces
    - participate in hierarchical resolution

    Each node owns a local capability scope through NodePorts.
    Child nodes automatically inherit a forked capability scope.
    """

    key: str
    name: str | None = None

    # ----------------------------------
    # EXECUTION METADATA
    # ----------------------------------

    kind: NodeKind = NodeKind.USER
    scope: NodeScope = NodeScope.NODE
    visibility: NodeVisibility = NodeVisibility.NORMAL

    ports: NodePorts = field(
        default_factory=lambda: NodePorts(
            Container(),
            Container(),
        )
    )

    # ----------------------------------
    # PERMISSIONS
    # ----------------------------------

    anonymous: bool = False

    # ----------------------------------
    # RUN HANDLER
    # ----------------------------------

    on_run: RunHandler | None = None
    on_setup: RunHandler | None = None

    # ----------------------------------
    # CONTEXT HANDLER
    # ----------------------------------

    on_resource: ResourceHandler | None = None

    # ----------------------------------
    # FIELDS
    # ----------------------------------

    parent: Node | None = None
    children: dict[str, Node] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ----------------------------------
    # PROPERTIES
    # ----------------------------------

    is_shell: bool = False
    listed: bool = True
    navigable: bool = True
    resolvable: bool = True

    # ----------------------------------
    # ATTACH TO RUNTIME
    # ----------------------------------

    def mount(self, node: Node) -> None:
        """Mountes an existing runtime subtree.

        Unlike add(), attach() preserves the existing capability
        hierarchy of the attached subtree.

        The attached subtree keeps its internal local scopes while
        extending hierarchical lookup into the current runtime node.

        Published capabilities remain directed only to the direct
        parent runtime space.

        Args:
            node:
                Existing runtime subtree root.
        """

        node.parent = self

        # Mount existing runtime scope into current hierarchy.
        node.ports.mount(self.ports)

        self.children[node.key] = node

    # ----------------------------------
    # ROOT
    # ----------------------------------

    @property
    def root(self) -> Node:
        """Returns the top-most runtime node.

        The root node represents the sovereign runtime space of the
        current hierarchy.

        Mounted runtime subtrees inherit hierarchical access into this
        root space while preserving their own local runtime semantics.

        The root node is typically used for:

        - platform-level resource resolution
        - sovereign runtime capabilities
        - global fallback resources
        - platform-owned error projections
        - runtime-wide infrastructure access

        Returns:
            The top-most runtime node in the hierarchy.
        """

        node = self

        while node.parent is not None:
            node = node.parent

        return node

    # ----------------------------------
    # CHILDREN
    # ----------------------------------

    def add(self, child: Node) -> None:
        """Adds a child runtime node.

        Child nodes inherit a forked capability scope from the
        current node, creating a hierarchical runtime visibility
        chain.

        Args:
            child:
                The child runtime node.
        """

        child.parent = self

        # Inherit hierarchical capability scope.
        if self.ports:
            child.ports = self.ports.fork()

        self.children[child.key] = child

    def get(self, key: str) -> Node | None:
        """Returns a direct child node by key."""

        return self.children.get(key)

    def get_resource(self, key: Any, **kwargs: Any) -> Any:
        """Resolves a semantic runtime resource."""

        if self.on_resource:
            resource = self.on_resource(key, **kwargs)
            if resource is not None:
                return resource

        if self.parent:
            return self.parent.get_resource(key, **kwargs)

        return None

    # ----------------------------------
    # HAS
    # ----------------------------------

    def has_run(self) -> bool:
        """Returns True if the node provides a run capability."""

        return self.on_run is not None

    def has_setup(self) -> bool:
        """Returns True if the node provides a setup capability."""

        return self.on_setup is not None

    def has_resource(self) -> bool:
        """Returns True if the node provides a resource capability."""

        return self.on_resource is not None

    # ----------------------------------
    # HIERARCHY
    # ----------------------------------

    def walk(self, on_walk: Callable[[Node], None]):
        """Traverses the runtime hierarchy recursively."""

        on_walk(self)

        for child in self.children.values():
            child.walk(on_walk)

    def find(
        self,
        path: NodePath,
        *,
        absolute: bool = False,
    ) -> Node | None:
        """Resolves a runtime node by path.

        Path resolution traverses the runtime hierarchy using
        local child namespaces.

        Relative resolution starts from the current node.

        Absolute resolution starts from the runtime root.

        Args:
            path:
                Runtime path to resolve.

            absolute:
                If True, resolution starts from the runtime root.

        Returns:
            Resolved runtime node or None if the path
            cannot be resolved.
        """

        current = self.root if absolute else self

        for part in path.parts:

            child = current.children.get(part)
            if child is None:
                return None

            current = child

        return current

    def find_navigable(self) -> Sequence[Node]:
        """Returns navigable runtime spaces visible from this node.

        Visibility follows semantic runtime traversal rules:

        - direct navigable child nodes are visible
        - non-navigable child spaces are traversed transparently
        - navigable child spaces stop recursive traversal

        Returns:
            Visible navigable runtime spaces.
        """

        result: list[Node] = []

        def collect(node: Node):

            for child in node.children.values():

                # Navigable spaces become visible and stop traversal.
                if child.navigable:
                    result.append(child)
                    continue

                # Transparent structure spaces are traversed recursively.
                collect(child)

        collect(self)
        return tuple(result)

    def find_resolvable(self) -> Sequence[Node]:
        """Returns runtime nodes addressable from this runtime space.

        Resolver visibility follows semantic runtime traversal rules:

        - resolvable child nodes become directly addressable
        - non-navigable child spaces are traversed transparently
        - navigable child spaces stop recursive traversal
        - non-resolvable nodes may still contribute structure

        This method describes runtime command visibility, not
        navigational visibility.

        Returns:
            Addressable runtime nodes visible from this runtime space.
        """

        result: list[Node] = []

        def collect(node: Node):

            for child in node.children.values():

                # Addressable runtime endpoint.
                if child.resolvable:
                    result.append(child)

                # Navigable spaces stop recursive traversal.
                if child.navigable:
                    continue

                # Transparent structure spaces are traversed recursively.
                collect(child)

        collect(self)

        return tuple(result)
