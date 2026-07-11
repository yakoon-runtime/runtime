from __future__ import annotations

from typing import Protocol

from y5n.base.nodes import Node, NodePath, UsageError
from y5n.runtime.capabilities.permission import Permission
from y5n.runtime.runtime import (
    NodeNotExecutable,
    NodeNotFound,
    PermissionDenied,
    Session,
)


class InvocationResolver:
    """Resolve command strings to Node targets.

    Traverses the node tree with scope-aware resolution, permission checks,
    and argument matching against registered invocations.
    """

    SUGGESTION_LIMIT = 1
    USAGE_TOKEN = "?"

    def __init__(
        self,
        on_authorize: OnAuthorize,
        on_suggest: OnSuggest,
        root: Node,
        on_get_node: OnGetNode,
    ):

        self._root = root

        self.on_authorize = on_authorize
        self.on_suggest = on_suggest
        self.on_get_node = on_get_node

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def resolve(
        self,
        parent: NodePath | None,
        key: str,
        tokens: list[str] | None,
        session: Session,
        strict: bool = True,
    ) -> tuple[Node, list[str]]:

        tokens = tokens or []

        key = key.strip()

        if not key:
            raise NodeNotFound(command=key)

        # ---------------------------------
        # '?' shows usage instead of executing
        # ---------------------------------

        show_usage = tokens and tokens[-1] == self.USAGE_TOKEN
        if show_usage:
            tokens = tokens[:-1]

        # ---------------------------------
        # Resolve parent runtime space
        # ---------------------------------

        current = self._root

        if parent:

            resolved = self._root.find(parent, absolute=True)

            if not resolved:
                raise NodeNotFound(command=str(parent))

            current = resolved

        # ---------------------------------
        # Path-style resolution (ident/users/list)
        # ---------------------------------

        if "/" in key:
            node = self._resolve_path(
                current=current,
                key=key,
            )
            if node:
                if show_usage:
                    self._raise_usage(node)
                self._ensure_invocation(
                    session,
                    node,
                    tokens,
                    strict=strict,
                )
                return node, tokens

        # ---------------------------------
        # Resolve current node
        # ---------------------------------

        node = self._resolve_node(
            parent=current,
            key=key,
        )

        if not node:
            self._raise_not_found(
                parent=current,
                key=key,
            )

        assert node

        # ---------------------------------
        # Continue contextual traversal
        # ---------------------------------

        if node.contextual and tokens:

            if not node.consumes(tokens):

                return self.resolve(
                    parent=node.path,
                    key=tokens[0],
                    tokens=tokens[1:],
                    session=session,
                )

        # ---------------------------------
        # Show usage for resolved node
        # ---------------------------------

        if show_usage:
            self._raise_usage(node)

        # ---------------------------------
        # Reject non-executable final target
        # ---------------------------------

        if not node.resolvable:
            raise NodeNotExecutable(command=key)

        # ---------------------------------
        # Validate invocation
        # ---------------------------------

        self._ensure_invocation(
            session,
            node,
            tokens,
            strict=strict,
        )

        return node, tokens

    def _raise_not_found(
        self,
        *,
        parent: Node,
        key: str,
    ) -> None:

        suggestions = self.on_suggest(
            value=key,
            choices=[],
            limit=self.SUGGESTION_LIMIT,
        )

        raise NodeNotFound(
            command=key,
            suggestions=suggestions,
        )

    # ---------------------------------------------------------------------
    # Path resolution
    # ---------------------------------------------------------------------

    def _resolve_path(
        self,
        *,
        current: Node,
        key: str,
    ) -> Node | None:
        """Resolve a path-style key like 'ident/users/list'.

        Walks the node tree segment by segment. The last segment is
        resolved via _resolve_node (respects scope + resolvable flag).
        Intermediate segments are resolved by direct child key lookup
        (with fallback to tree index).
        """
        segments = key.split("/")

        # Absolute path starts from root
        walk = self._root if key.startswith("/") else current

        for seg in segments[:-1]:
            if not seg:
                continue
            child = self.on_get_node(walk, seg)
            if child is None:
                return None
            walk = child

        return self._resolve_node(parent=walk, key=segments[-1])

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    def _resolve_node(
        self,
        *,
        parent: Node,
        key: str,
    ) -> Node | None:

        return self.on_get_node(parent, key)

    def _raise_usage(
        self,
        node: Node,
    ) -> None:
        usages = [inv.usage_data(node.key) for inv in (node.invocations or [])]
        if not usages:
            for child in node.children.values():
                for inv in child.invocations or []:
                    usages.append(inv.usage_data(child.key))
        raise UsageError(usages=usages, command=node.key)

    def _ensure_invocation(
        self,
        session: Session,
        node: Node,
        tokens: list[str] | None,
        strict: bool = True,
    ):
        node.validate(tokens, strict=strict)

        if node.anonymous:
            return

        action = tokens[0] if tokens else None

        parent_key = node.parent.key if node.parent else ""

        fq = Permission.fq_key(
            parent_key,
            node.key,
            action,
        )

        if not self.on_authorize(
            session=session,
            perm_key=fq,
        ):
            raise PermissionDenied()


# -------------------------------------------------------------------------
# Ports
# -------------------------------------------------------------------------


class OnAuthorize(Protocol):

    def __call__(
        self,
        *,
        session,
        perm_key: str,
    ) -> bool: ...


class OnSuggest(Protocol):

    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...


class OnGetNode(Protocol):
    def __call__(self, parent: Node, key: str) -> Node | None: ...
