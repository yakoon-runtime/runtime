from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from y5n.runtime.api.permissions import Operation
from y5n.runtime.api.runtime.input import Interaction
from y5n.runtime.api.runtime.invocation import CommandSignature

from .handler import ResolveHandler, RunHandler
from .invocation import CommandSignatureValidator
from .path import NodePath
from .types import NodeKind, NodeVisibility

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
    """

    key: str
    """Unique identifier used for CLI resolution and node lookup."""

    name: str | None = None
    """Human-readable display name. Falls back to *key* when not set."""

    fs_path: Path | None = None
    """Filesystem path to the bundle directory (set by Tree on assembly)."""

    # ----------------------------------
    # EXECUTION METADATA
    # ----------------------------------

    kind: NodeKind = NodeKind.USER
    """Runtime-level classification (USER, SYSTEM, …)."""

    visibility: NodeVisibility = NodeVisibility.NORMAL
    """Controls whether the node appears in listings."""

    # ----------------------------------
    # SIGNATURES
    # ----------------------------------

    signatures: list[CommandSignature] = field(default_factory=list)
    """Declared CLI signatures.  Matched against user input during resolution."""

    validator: CommandSignatureValidator = field(
        default_factory=CommandSignatureValidator
    )
    """Strategy object that matches tokens against *signatures*."""

    def validate(
        self,
        tokens: list[str] | None,
        strict: bool = True,
    ) -> CommandSignature | None:
        return self.validator.validate(node=self, tokens=tokens, strict=strict)

    def consumes(self, tokens: list[str] | None) -> bool:
        if not self.resolvable or not self.signatures:
            return False

        tokens = tokens or []
        if not tokens:
            return False

        action = tokens[0]

        # Options (--key) are always consumed by the invocation system,
        # not by child nodes.
        if action.startswith("--"):
            return True

        for signature in self.signatures:
            if signature.action == action:
                return True

        return False

    # ----------------------------------
    # PERMISSIONS
    # ----------------------------------

    anonymous: bool = False
    """Skip permission checks when True.  Used for public/utility nodes."""

    def required_bit(self, operation: Operation) -> str:
        """Map a runtime operation onto the required permission bit.

        The node type decides the mapping — the engine knows only
        operations, never bits directly:
          - Container (navigable): READ -> r, WRITE -> w
          - Leaf / Command:        READ -> r, EXECUTE -> x
        """
        if operation is Operation.WRITE:
            return "w"
        if operation is Operation.READ:
            return "r"
        if operation is Operation.EXECUTE:
            return "x" if not self.navigable else "r"
        raise ValueError(f"Unknown operation: {operation}")

    # ----------------------------------
    # RUN HANDLER
    # ----------------------------------

    run: RunHandler | None = None
    """Async generator invoked when the node is executed as a command."""

    setup: RunHandler | None = None
    """Async generator called once during node initialisation."""

    resolve: ResolveHandler | None = None
    """Content interpretation of the node's host. Built by the tree from the
    host's ``resolve:`` declaration (ADR-10). The runtime dispatches a node's
    capability resolution to its host node's handler."""

    # ----------------------------------
    # TREE STRUCTURE
    # ----------------------------------

    parent: Node | None = None
    """Parent node in the runtime tree.  Set by add() or mount()."""

    children: dict[str, Node] = field(default_factory=dict)
    """Direct child nodes, keyed by their *key* attribute."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Arbitrary key-value storage for space-specific data."""

    search_paths: list[str] = field(default_factory=list)
    """Pre-computed search paths for command resolution.  Assembled by
    Tree.build() from .yak/path files, inherited and merged top-down."""

    resources: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Raw resource references assembled by Tree.build().  Keyed by resource
    type (projection, man, …) then variant (default, de, compact, …).
    Values are a reference expression string (``file:...``, ``resource:...``)
    or a ``{ref, parameters}`` mapping; resolved lazily by the host
    (ADR-10)."""

    # ----------------------------------
    # RENDERING HINTS
    # ----------------------------------

    listed: bool = True
    """Show this node in ls / overview listings when True."""

    navigable: bool = True
    """Allow cd / enter into this node when True."""

    resolvable: bool = True
    """Consider this node during command resolution when True."""

    contextual: bool = False
    """Walk into child nodes during resolution when the current
    node does not match the next token."""

    # ----------------------------------
    # INTERACTION MODE
    # ----------------------------------

    interaction: Interaction = Interaction.CLI
    """Default input mode for this node.
    Overridden by --cli / --form / --inherit at runtime.
    CLI     → always command line (default).
    FORM    → always interactive form.
    INHERIT → inherit from session setting.
    """

    # ----------------------------------
    # ATTACH TO RUNTIME
    # ----------------------------------

    def mount(self, node: T) -> T:
        """Mount an existing runtime subtree.

        Unlike add(), mount() preserves the existing capability
        hierarchy of the mounted subtree.

        The mounted subtree keeps its internal local scopes while
        extending hierarchical lookup into the current runtime node.

        Published capabilities remain directed only to the direct
        parent runtime space.

        Args:
            node:
                Existing runtime subtree root.

        Raises:
            ValueError:
                If *node* is the same instance — cannot self-mount.
                If *node* already belongs to another parent.
                If *node* is an ancestor — would create a cycle.
        """

        if node is self:
            raise ValueError("Cannot mount a node onto itself.")

        if node.parent is not None:
            raise ValueError(
                f"Node '{node.key}' is already mounted under '{node.parent.key}'."
            )

        # Prevent cycles: walk up from self, ensure node is not an ancestor
        current = self
        while current is not None:
            if current is node:
                raise ValueError("Cannot mount an ancestor into its own subtree.")
            current = current.parent

        node.parent = self

        self.children[node.key] = node
        return node

    # ----------------------------------
    # PATH
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

        Use add() for new leaf nodes.  Use mount() for existing
        subtrees that already carry a hierarchy.

        Args:
            child:
                The child runtime node.

        Raises:
            ValueError:
                If *child* already has children — use mount() instead.
                If *child* already belongs to another parent.
        """

        if child.children:
            raise ValueError(
                f"Node '{child.key}' already has children. Use mount() "
                f"for existing subtrees, not add()."
            )

        if child.parent is not None:
            raise ValueError(
                f"Node '{child.key}' already belongs to "
                f"'{child.parent.key}'. Detach it first."
            )

        child.parent = self

        self.children[child.key] = child
        return child

    def get(self, key: str) -> Node | None:
        """Returns a direct child node by key."""

        return self.children.get(key)

    # ----------------------------------
    # HAS
    # ----------------------------------

    def has_run(self) -> bool:
        """Returns True if the node provides a run capability."""

        return self.run is not None

    def has_setup(self) -> bool:
        """Returns True if the node provides a setup capability."""

        return self.setup is not None

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
        if path.first == current.key:
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
