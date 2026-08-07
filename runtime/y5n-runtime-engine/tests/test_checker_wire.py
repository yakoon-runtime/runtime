"""Wire regression: the resolver's OnAuthorize port and the checker agree.

The resolver calls on_authorize(session, node, operation); the checker's
check(session, node, operation) must satisfy that port signature. A
mismatch (e.g. binding can_execute(session, node)) throws TypeError at
dispatch time and surfaces as an Internal Error.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import Operation, PermBits, Permission
from y5n.runtime.engine.capabilities.permission import PermissionChecker
from y5n.runtime.engine.capabilities.permission.models.set import PermissionSet
from y5n.runtime.engine.machine.resolver import InvocationResolver
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


def _session(permset: PermissionSet) -> Session:
    session = Session(
        key=Key.from_parts("test", "session", "wire", "1"),
        data=SessionData(),
    )
    session.set_permissions(permset)
    return session


def _make_resolver(checker: PermissionChecker) -> InvocationResolver:
    def on_get_node(parent: Node, key: str) -> Node | None:
        return parent.get(key)

    def on_suggest(
        *, value: str, choices: list[str], limit: int = 3, cutoff: float = 0.5
    ) -> list[str]:
        return []

    root = Node(key="root")
    ls_node = Node(key="ls", navigable=False)
    root.add(ls_node)

    return InvocationResolver(
        root=root,
        on_authorize=checker.check,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
    )


def test_checker_check_satisfies_resolver_port():
    """on_has_permission=perm_checker.check must work end to end."""
    permset = PermissionSet()
    permset.add(Permission(path="/root", bits=PermBits.from_str("rwx")))
    session = _session(permset)
    checker = PermissionChecker()

    resolver = _make_resolver(checker)

    node, tokens = resolver.resolve("ls", None, session)
    assert node.key == "ls"
    assert tokens == []


def test_checker_denies_without_grant():
    session = _session(PermissionSet())
    checker = PermissionChecker()
    ls_node = Node(key="ls", navigable=False)

    assert not checker.can_execute(session, ls_node)
    assert not checker.check(session, ls_node, Operation.EXECUTE)


def test_checker_allows_with_grant():
    permset = PermissionSet()
    permset.add(Permission(path="/root", bits=PermBits.from_str("rwx")))
    session = _session(permset)
    checker = PermissionChecker()
    ls_node = Node(key="ls", navigable=False, parent=Node(key="root"))

    assert checker.can_execute(session, ls_node)
    assert checker.check(session, ls_node, Operation.EXECUTE)
