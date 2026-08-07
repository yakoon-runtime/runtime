from __future__ import annotations

from typing import Protocol

from y5n.runtime.api.permissions import Operation
from y5n.runtime.api.runtime.sessions import SecurityContext
from y5n.runtime.engine.nodes import Node, UsageError
from y5n.runtime.engine.runtime import (
    ElevationRequired,
    NodeNotExecutable,
    NodeNotFound,
    PermissionDenied,
    Session,
)

from .ports import OnSuggest


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
        # Path-style resolution (ident/users/list)
        # ---------------------------------

        if "/" in key:
            node = self._resolve_path(
                current=self._root,
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
        # Resolve from session context (current path)
        # ---------------------------------

        ctx = self._resolve_context(session)
        node = self._resolve_node(parent=ctx, key=key) if ctx else None

        if not node:
            node = self._resolve_node(parent=self._root, key=key)

        if not node:
            self._raise_not_found(
                parent=self._root,
                key=key,
            )

        assert node

        # ---------------------------------
        # Continue contextual traversal
        # ---------------------------------

        if node.contextual and tokens:
            if not node.consumes(tokens):
                child = self.on_get_node(node, tokens[0])
                if child:
                    node = child
                    tokens = tokens[1:]

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

    def _resolve_context(self, session: Session) -> Node | None:
        """Walk from root to the session's current path node."""
        path = session.cwd
        if not path or path == "/":
            return None
        walk = self._root
        for seg in path.strip("/").split("/"):
            child = self.on_get_node(walk, seg)
            if child is None:
                return None
            walk = child
        return walk

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
        usages = [sig.usage_data(node.key) for sig in (node.signatures or [])]
        if not usages:
            for child in node.children.values():
                for sig in child.signatures or []:
                    usages.append(sig.usage_data(child.key))
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

        if not self.on_authorize(
            session=session,
            node=node,
            operation=Operation.EXECUTE,
        ):
            raise PermissionDenied()

        # Elevation: privileged nodes need a security context that is
        # already elevated. Permission was checked above — the account
        # may well hold the grant. The context only answers *how*: a
        # normal session must consciously confirm first; temporary
        # elevates exactly one invocation and falls back to normal.
        if node.privileged:
            context = session.security_context
            if context == SecurityContext.NORMAL:
                raise ElevationRequired(command=node.key)
            if context == SecurityContext.TEMPORARY:
                session.set_security_context(SecurityContext.NORMAL)


# -------------------------------------------------------------------------
# Ports
# -------------------------------------------------------------------------


class OnAuthorize(Protocol):

    def __call__(
        self,
        *,
        session,
        node: Node,
        operation: Operation,
    ) -> bool: ...


class OnGetNode(Protocol):
    def __call__(self, parent: Node, key: str) -> Node | None: ...
