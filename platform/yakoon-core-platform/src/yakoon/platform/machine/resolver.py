from __future__ import annotations

from typing import Protocol

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
    ) -> tuple[Node, list[str]]:

        tokens = tokens or []

        key = key.strip()

        if not key:
            raise NodeNotFound(command=key)

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
        # Validate invocation
        # ---------------------------------

        self._ensure_invocation(
            session,
            node,
            tokens,
        )

        return node, tokens

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    def _resolve_node(
        self,
        *,
        parent: Node,
        key: str,
    ) -> Node | None:

        # ---------------------------------
        # Local runtime scope
        # ---------------------------------

        for node in parent.find_resolvable():

            if node.scope not in (
                NodeScope.NODE,
                NodeScope.ROOT,
            ):
                continue

            if node.key == key:
                return node

        # ---------------------------------
        # ROOT scope
        # ---------------------------------

        if parent == self._root:

            node = self._root_nodes.get(key)

            if node:
                return node

        # ---------------------------------
        # GLOBAL scope
        # ---------------------------------

        return self._global_nodes.get(key)

    def _raise_not_found(
        self,
        *,
        parent: Node,
        key: str,
    ) -> None:

        choices: list[str] = []

        # ---------------------------------
        # Local runtime scope
        # ---------------------------------

        for node in parent.find_resolvable():

            if node.scope in (
                NodeScope.NODE,
                NodeScope.ROOT,
            ):
                choices.append(node.key)

        # ---------------------------------
        # ROOT scope
        # ---------------------------------

        if parent == self._root:
            choices.extend(self._root_nodes.keys())

        # ---------------------------------
        # GLOBAL scope
        # ---------------------------------

        choices.extend(self._global_nodes.keys())

        suggestions = self.on_suggest(
            value=key,
            choices=choices,
            limit=self.SUGGESTION_LIMIT,
        )

        raise NodeNotFound(
            command=key,
            suggestions=suggestions,
        )

    def _ensure_invocation(
        self,
        session: Session,
        node: Node,
        tokens: list[str] | None,
    ):
        node.validate(tokens)

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
