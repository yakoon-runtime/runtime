"""Elevation gate tests: privileged nodes need an elevated security context.

Permission answers "may I?" — a privileged node requires a conscious
confirmation on top. The session security context (normal/temporary/
administrative) answers *how* the session works:

- normal         → ElevationRequired
- temporary      → allowed once, then falls back to normal
- administrative → allowed
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import Operation
from y5n.runtime.api.runtime.invocation import CommandSignature
from y5n.runtime.api.runtime.sessions import SecurityContext
from y5n.runtime.engine.machine.resolver import InvocationResolver
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.runtime.error import ElevationRequired
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


def _session(context: str = "normal") -> Session:
    session = Session(
        key=Key.from_parts("test", "session", "elevation", "1"),
        data=SessionData(),
    )
    session.set_security_context(context)
    return session


def _resolver(*, authorized: bool = True) -> InvocationResolver:
    def on_get_node(parent: Node, key: str) -> Node | None:
        return parent.get(key)

    def on_suggest(
        *, value: str, choices: list[str], limit: int = 3, cutoff: float = 0.5
    ) -> list[str]:
        return []

    def on_authorize(*, session: Session, node: Node, operation: Operation) -> bool:
        return authorized

    root = Node(key="root")
    root.add(
        Node(
            key="danger",
            privileged=True,
            navigable=False,
            signatures=[CommandSignature(action="run", default=True)],
        )
    )

    return InvocationResolver(
        root=root,
        on_authorize=on_authorize,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
    )


def test_normal_session_requires_elevation():
    resolver = _resolver()

    with pytest.raises(ElevationRequired) as exc:
        resolver.resolve("danger", None, _session(SecurityContext.NORMAL))

    assert exc.value.command == "danger"


def test_administrative_session_allows_privileged():
    resolver = _resolver()

    node, tokens = resolver.resolve(
        "danger", None, _session(SecurityContext.ADMINISTRATIVE)
    )

    assert node.key == "danger"
    assert tokens == []


def test_temporary_allows_exactly_one_invocation():
    resolver = _resolver()
    session = _session(SecurityContext.TEMPORARY)

    node, _ = resolver.resolve("danger", None, session)
    assert node.key == "danger"
    # temporary is consumed: the session fell back to normal
    assert session.security_context == SecurityContext.NORMAL

    with pytest.raises(ElevationRequired):
        resolver.resolve("danger", None, session)


def test_privileged_requires_permission_too():
    """Permission is still checked first — elevation grants no rights."""
    resolver = _resolver(authorized=False)

    with pytest.raises(Exception):
        resolver.resolve("danger", None, _session(SecurityContext.ADMINISTRATIVE))


def test_normal_node_ignores_elevation_gate():
    resolver = _resolver()
    root = resolver._root  # type: ignore[attr-defined]
    root.add(
        Node(
            key="safe",
            navigable=False,
            signatures=[CommandSignature(action="run", default=True)],
        )
    )

    node, _ = resolver.resolve("safe", None, _session(SecurityContext.NORMAL))
    assert node.key == "safe"


def test_logout_resets_security_context():
    session = _session(SecurityContext.ADMINISTRATIVE)
    session.logout()
    assert session.security_context == SecurityContext.NORMAL
