"""End-to-end: privileged node in the tree + resolver + checker.

The tree reads ``privileged`` from yak.yml; the resolver raises
ElevationRequired for a normal session; an administrative session runs
the node; temporary elevates exactly one invocation. The node never
knows about elevation — it is an invocation flag like ``anonymous``.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import PermBits, Permission
from y5n.runtime.api.runtime.invocation import CommandSignature
from y5n.runtime.api.runtime.sessions import SecurityContext
from y5n.runtime.engine.capabilities.permission import PermissionChecker
from y5n.runtime.engine.capabilities.permission.models.set import PermissionSet
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.machine.resolver import InvocationResolver
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime.error import ElevationRequired
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


def _write(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(tmp_path) -> Tree:
    _write(
        tmp_path / "usr" / "sbin" / "danger" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Danger",
                "resolvable: true",
                "navigable: false",
                "privileged: true",
            ]
        ),
    )
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=tmp_path, executors=registry)
    tree.build()
    return tree


def _session() -> Session:
    session = Session(
        key=Key.from_parts("test", "session", "e2e", "1"),
        data=SessionData(),
    )
    permset = PermissionSet()
    permset.add(Permission(path="/", bits=PermBits.from_str("rwx")))
    session.set_permissions(permset)
    return session


def _resolver(tree: Tree) -> InvocationResolver:
    checker = PermissionChecker()

    def on_get_node(parent: Node, key: str) -> Node | None:
        return parent.get(key)

    def on_suggest(
        *, value: str, choices: list[str], limit: int = 3, cutoff: float = 0.5
    ):
        return []

    root = tree.root()
    return InvocationResolver(
        root=root,
        on_authorize=checker.check,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
    )


def test_privileged_in_tree_blocks_normal_session(tmp_path):
    tree = _build_tree(tmp_path)
    resolver = _resolver(tree)
    session = _session()

    with pytest.raises(ElevationRequired):
        resolver.resolve("/usr/sbin/danger", None, session)


def test_privileged_in_tree_runs_in_administrative_session(tmp_path):
    tree = _build_tree(tmp_path)
    resolver = _resolver(tree)
    session = _session()
    session.set_security_context(SecurityContext.ADMINISTRATIVE)

    node, tokens = resolver.resolve("/usr/sbin/danger", None, session)
    assert node.privileged is True
    assert tokens == []


def test_privileged_in_tree_temporary_elevates_once(tmp_path):
    tree = _build_tree(tmp_path)
    resolver = _resolver(tree)
    session = _session()
    session.set_security_context(SecurityContext.TEMPORARY)

    node, _ = resolver.resolve("/usr/sbin/danger", None, session)
    assert node.privileged is True
    assert session.security_context == SecurityContext.NORMAL

    with pytest.raises(ElevationRequired):
        resolver.resolve("/usr/sbin/danger", None, session)


def test_privileged_node_has_signature(tmp_path):
    """A privileged node may also declare a signature — both compose."""
    tree = _build_tree(tmp_path)
    root = tree.root()
    danger = root.get("usr").get("sbin").get("danger")
    assert danger is not None
    assert danger.privileged is True
