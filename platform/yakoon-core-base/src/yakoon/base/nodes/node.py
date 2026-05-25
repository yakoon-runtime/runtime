from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from yakoon.base.runtime import Container

from .handler import RunHandler
from .invocation import Invocation, InvocationValidator
from .path import NodePath
from .ports import NodePorts
from .types import NodeKind, NodeScope, NodeVisibility

# ----------------------------------
# NODE
# ----------------------------------

T = TypeVar("T", bound="Node")


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
            Container(allow_override=False),
            Container(allow_override=True),
        )
    )

    # ----------------------------------
    # INVOCATIONS
    # ----------------------------------

    invocations: list[Invocation] = field(default_factory=list)
    validator: InvocationValidator = field(default_factory=InvocationValidator)

    def validate(self, tokens: list[str] | None) -> Invocation | None:
        return self.validator.validate(node=self, tokens=tokens)

    def consumes(self, tokens: list[str] | None) -> bool:
        if not self.invocations:
            return False

        tokens = tokens or []
        if not tokens:
            return False

        action = tokens[0]

        for invocation in self.invocations:
            if invocation.action == action:
                return True

        return False

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
    contextual: bool = False

    # ----------------------------------
    # ATTACH TO RUNTIME
    # ----------------------------------

    def mount(self, node: T) -> T:
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
        return node

    # ----------------------------------
    # ROOT
    # ----------------------------------

    @property
    def path(self) -> NodePath:
        """Returns the node path inside the runtime hierarchy."""

        parts: list[str] = []

        node: Node | None = self
        while node is not None:
            parts.append(node.key)
            node = node.parent

        parts.reverse()
        return NodePath(tuple(parts))

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

    def add(self, child: T) -> T:
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
        return child

    def get(self, key: str) -> Node | None:
        """Returns a direct child node by key."""

        return self.children.get(key)

    def ports_from(
        self,
        path: NodePath,
        *,
        absolute: bool = False,
    ) -> NodePorts | None:
        """Resolves the capability scope of another runtime space.

        This method traverses the runtime hierarchy and returns the
        published capability scope of the target runtime node.

        Unlike direct node access, this method exposes only semantic
        runtime capabilities and does not leak mutable runtime topology.

        The returned NodePorts object may provide:

        - projection capabilities
        - runtime services
        - infrastructure adapters
        - plugin-local semantic capabilities
        - platform-provided services

        Args:
            path:
                Runtime path to resolve.

            absolute:
                If True, resolution starts from the runtime root.

        Returns:
            The target runtime capability scope or None if the
            runtime space cannot be resolved.
        """

        node = self.find(path, absolute=absolute)
        if node is None:
            return None

        return node.ports

    # ----------------------------------
    # HAS
    # ----------------------------------

    def has_run(self) -> bool:
        """Returns True if the node provides a run capability."""

        return self.on_run is not None

    def has_setup(self) -> bool:
        """Returns True if the node provides a setup capability."""

        return self.on_setup is not None

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

        parts = path.parts
        if absolute and path.first == current.key:
            parts = parts[1:]

        for part in parts:

            if part == ".":
                continue

            if part == "..":
                if current.parent:
                    current = current.parent
                continue

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
