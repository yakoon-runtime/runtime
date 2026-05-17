from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.errors import ErrorState
from yakoon.base.nodes import Node, NodeScope
from yakoon.platform.capabilities.permission import Permission
from yakoon.platform.runtime import NodeNotFound, PermissionDenied, Session


class InvocationResolver:

    SUGGESTION_LIMIT = 1

    def __init__(
        self,
        on_authorize: OnAuthorize,
        on_suggest: OnSuggest,
        nodes: Sequence[Node],
    ):
        self.nodes = nodes
        self.on_authorize = on_authorize
        self.on_suggest = on_suggest

        self._root_nodes = {n.key: n for n in nodes}
        self._global_nodes: dict[str, Node] = {}
        self._shell_nodes: dict[str, Node] = {}
        self._shell_root = next(n for n in nodes if n.is_shell)

        self._build()

    def _build(self):

        for root in self.nodes:
            self._index_node(root)

    def _index_node(self, node: Node):

        # GLOBAL
        if node.scope == NodeScope.GLOBAL:
            if node.key in self._global_nodes:
                raise ValueError(f"GLOBAL conflict: {node.key}")

            self._global_nodes[node.key] = node

        # ROOT
        if node.scope == NodeScope.ROOT:
            if node.key in self._shell_nodes:
                raise ValueError(f"ROOT conflict: {node.key}")

            self._shell_nodes[node.key] = node

        # RECURSIVE
        for child in node.children.values():
            self._index_node(child)

    def resolve(
        self,
        parent_key: str | None,
        node_key: str,
        tokens: list[str] | None,
        session: Session,
    ) -> Node:

        choices = []

        node_key = node_key.strip()
        if not node_key:
            raise NodeNotFound(
                ErrorState.by_type(
                    key=NodeNotFound,
                    command=node_key,
                )
            )

        parent: Node | None = None
        if parent_key is None:
            parent = self._shell_root
        else:
            parent = self._root_nodes.get(parent_key)

        if not parent:
            raise NodeNotFound(
                ErrorState.by_type(
                    key=NodeNotFound,
                    command=node_key,
                )
            )

        if parent.key == node_key:
            self._ensure_invocation(session, parent, tokens)
            return parent

        # -------------------
        # 2. PARENT SCOPE ---
        # -------------------

        for node in parent.find_navigable():
            if node.scope in (NodeScope.NODE, NodeScope.ROOT):
                choices.append(node.key)

            #!Command in own app & all own commands with SHELL Scope.
            if node.key == node_key and node.scope in (
                NodeScope.NODE,
                NodeScope.ROOT,
            ):
                self._ensure_invocation(session, node, tokens)
                return node

        # -------------------------------------
        # 3. SHELL scope (in case of shell) ---
        # -------------------------------------

        if parent.is_shell:
            choices.extend([n for n in self._shell_nodes.keys()])
            node = self._shell_nodes.get(node_key)
            if node:
                self._ensure_invocation(session, node, tokens)
                return node

        # -------------------
        # 4. GLOBAL scope ---
        # -------------------

        node = self._global_nodes.get(node_key)
        choices.extend([n for n in self._global_nodes.keys()])
        if node:
            self._ensure_invocation(session, node, tokens)
            return node

        # -----------------
        # 5. SUGGESTION ---
        # -----------------

        suggestions = self.on_suggest(
            value=node_key,
            choices=choices,
            limit=self.SUGGESTION_LIMIT,
        )
        raise NodeNotFound(
            ErrorState.by_type(
                key=NodeNotFound,
                command=node_key,
                suggestions=suggestions,
            )
        )

    def globals(self) -> set[str]:
        return set(self._global_nodes.keys())

    # ----------------------------------
    # INTERNALS
    # ----------------------------------

    def _ensure_invocation(
        self, session: Session, node: Node, tokens: list[str] | None
    ):
        # node.ensure_invocation(tokens=tokens)

        if node.anonymous:
            return

        action = tokens[0] if tokens else None
        parent_key = node.parent.key if node.parent else ""
        fq = Permission.fq_key(parent_key, node.key, action)  # type: ignore
        if not self.on_authorize(session=session, perm_key=fq):
            raise PermissionDenied(ErrorState.by_type(key=PermissionDenied))


# ----------------------------------
# PORTS
# ----------------------------------


class OnAuthorize(Protocol):
    def __call__(self, *, session, perm_key: str) -> bool: ...


class OnSuggest(Protocol):
    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...
