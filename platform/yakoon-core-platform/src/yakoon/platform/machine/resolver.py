from __future__ import annotations

from typing import Protocol

from yakoon.base.errors import ErrorState
from yakoon.base.nodes import Node, NodePath, NodeScope
from yakoon.platform.capabilities.permission import Permission
from yakoon.platform.runtime import (
    NodeNotFound,
    PermissionDenied,
    Session,
)


class InvocationResolver:

    SUGGESTION_LIMIT = 1

    def __init__(
        self,
        on_authorize: OnAuthorize,
        on_suggest: OnSuggest,
        root: Node,
    ):

        self._root = root

        self.on_authorize = on_authorize
        self.on_suggest = on_suggest

        self._global_nodes: dict[str, Node] = {}
        self._root_nodes: dict[str, Node] = {}

        self._build()

    # ---------------------------------------------------------------------
    # Build
    # ---------------------------------------------------------------------

    def _build(self):

        def collect(node: Node):

            # GLOBAL
            if node.scope == NodeScope.GLOBAL:

                if node.key in self._global_nodes:
                    raise ValueError(f"GLOBAL conflict: {node.key}")

                self._global_nodes[node.key] = node

            # ROOT
            if node.scope == NodeScope.ROOT:

                if node.key in self._root_nodes:
                    raise ValueError(f"ROOT conflict: {node.key}")

                self._root_nodes[node.key] = node

        self._root.walk(collect)

    def globals(self) -> set[str]:
        return set(self._global_nodes.keys())

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def resolve(
        self,
        parent: NodePath | None,
        key: str,
        tokens: list[str] | None,
        session: Session,
    ) -> Node:

        choices: list[str] = []

        key = key.strip()

        if not key:
            raise NodeNotFound(
                ErrorState.by_type(
                    key=NodeNotFound,
                    command=key,
                )
            )

        # ---------------------------------
        # Resolve parent runtime space
        # ---------------------------------

        _parent = self._root

        if parent:

            resolved = self._root.find(parent)

            if not resolved:
                raise NodeNotFound(
                    ErrorState.by_type(
                        key=NodeNotFound,
                        command=str(parent),
                    )
                )

            _parent = resolved

        # ---------------------------------
        # Local runtime scope
        # ---------------------------------

        for node in _parent.find_resolvable():

            if node.scope in (
                NodeScope.NODE,
                NodeScope.ROOT,
            ):
                choices.append(node.key)

            if node.key == key and node.scope in (
                NodeScope.NODE,
                NodeScope.ROOT,
            ):
                self._ensure_invocation(
                    session,
                    node,
                    tokens,
                )

                return node

        # ---------------------------------
        # ROOT scope
        # ---------------------------------

        if _parent == self._root:

            choices.extend([n for n in self._root_nodes.keys()])

            node = self._root_nodes.get(key)

            if node:

                self._ensure_invocation(
                    session,
                    node,
                    tokens,
                )

                return node

        # ---------------------------------
        # GLOBAL scope
        # ---------------------------------

        choices.extend([n for n in self._global_nodes.keys()])

        node = self._global_nodes.get(key)

        if node:

            self._ensure_invocation(
                session,
                node,
                tokens,
            )

            return node

        # ---------------------------------
        # Suggestions
        # ---------------------------------

        suggestions = self.on_suggest(
            value=key,
            choices=choices,
            limit=self.SUGGESTION_LIMIT,
        )

        raise NodeNotFound(
            ErrorState.by_type(
                key=NodeNotFound,
                command=key,
                suggestions=suggestions,
            )
        )

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    def _ensure_invocation(
        self,
        session: Session,
        node: Node,
        tokens: list[str] | None,
    ):

        if node.anonymous:
            return

        action = tokens[0] if tokens else None

        parent_key = node.parent.key if node.parent else ""

        fq = Permission.fq_key(
            parent_key,
            node.key,
            action,
        )  # type: ignore

        if not self.on_authorize(
            session=session,
            perm_key=fq,
        ):
            raise PermissionDenied(ErrorState.by_type(key=PermissionDenied))


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
