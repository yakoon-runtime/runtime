from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Protocol

import yaml
from y5n.base.nodes import Node, NodePath, NodeScope, UsageError
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
        bundles_path: str | Path | None = None,
    ):

        self._root = root

        self.on_authorize = on_authorize
        self.on_suggest = on_suggest

        self._global_nodes: dict[str, Node] = {}
        self._root_nodes: dict[str, Node] = {}

        self._bundles_path = self._resolve_bundles_path(bundles_path)
        self._bundle_cache: dict[str, Node] = {}

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
        # Non-resolvable nodes (containers, namespaces)
        # Found by direct key lookup for proper error messaging
        # ---------------------------------

        child = parent.children.get(key)
        if child is not None and not child.resolvable:
            return child

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
        Intermediate segments are resolved by direct child key lookup.
        """
        segments = key.split("/")

        # Absolute path starts from root
        walk = self._root if key.startswith("/") else current

        for seg in segments[:-1]:
            if not seg:
                continue
            child = walk.children.get(seg)
            if child is None:
                child = self._global_nodes.get(seg) or self._root_nodes.get(seg)
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

        # ---------------------------------
        # Bundle check (experiment/fs-namespace)
        # Bundles in YAKOON_PATH take priority over semantic tree
        # ---------------------------------

        bundle_node = self._resolve_bundle(key)
        if bundle_node:
            return bundle_node

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
        # Non-resolvable nodes (containers, namespaces)
        # Found by direct key lookup for proper error messaging
        # ---------------------------------

        child = parent.children.get(key)
        if child is not None and not child.resolvable:
            return child

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

    # ---------------------------------------------------------------------
    # Bundle path resolution
    # ---------------------------------------------------------------------

    @staticmethod
    def _resolve_bundles_path(override: str | Path | None) -> Path:
        if override:
            return Path(override).resolve()
        raise RuntimeError(
            "No bundles_path configured. Set root_path in yakoon-runtime.yml "
            "or pass bundles_path to InvocationResolver."
        )

    # ---------------------------------------------------------------------
    # Bundle resolution
    # ---------------------------------------------------------------------

    def _resolve_bundle(self, key: str) -> Node | None:
        bundle_dir = self._bundles_path / f"{key}.bndl"
        if not bundle_dir.is_dir():
            return None

        cached = self._bundle_cache.get(key)
        if cached:
            return cached

        meta_file = bundle_dir / "bundle.yaml"
        if not meta_file.exists():
            return None

        with open(meta_file) as f:
            meta = yaml.safe_load(f) or {}

        executor = meta.get("executor", "python")
        run_file = bundle_dir / "run" / f"{executor}.py"
        if not run_file.exists():
            return None

        spec = importlib.util.spec_from_file_location(f"_bundle_{key}", run_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        node = Node(
            key=key,
            run=mod.run,
            resolvable=meta.get("resolvable", True),
            navigable=meta.get("navigable", False),
            anonymous=True,
            scope=NodeScope.GLOBAL,
        )
        self._bundle_cache[key] = node
        return node

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
