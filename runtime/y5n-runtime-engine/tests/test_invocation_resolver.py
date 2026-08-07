"""InvocationResolver unit tests.

Covers the command-string resolution logic against a real node tree:
  - path resolution (ident/users/list, /absolute)
  - session-context resolution from cwd
  - '?' usage handling
  - contextual child traversal
  - non-executable rejection
  - permission checks and anonymous bypass
  - suggestions on not-found
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import Operation
from y5n.runtime.api.runtime.invocation import CommandSignature, Invocation, Param
from y5n.runtime.engine.machine.resolver import InvocationResolver
from y5n.runtime.engine.nodes import Node, UsageError
from y5n.runtime.engine.runtime.error import (
    NodeNotExecutable,
    NodeNotFound,
    PermissionDenied,
)
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


def _session(cwd: str | None = None) -> Session:
    session = Session(
        key=Key.from_parts("test", "session", "resolver", "1"),
        data=SessionData(),
    )
    if cwd:
        session.set_cwd(cwd)
    return session


def _build_tree() -> Node:
    root = Node(key="root")

    system = Node(
        key="system",
        signatures=[CommandSignature(action="version", default=True)],
    )
    root.add(system)

    ident = Node(key="ident", contextual=True)
    root.add(ident)
    users = Node(
        key="users",
        contextual=True,
        signatures=[CommandSignature(action="list", default=True)],
    )
    ident.add(users)
    users.add(
        Node(key="admin", signatures=[CommandSignature(action="show", default=True)])
    )

    app = Node(key="app")
    root.add(app)
    app.add(
        Node(
            key="hello",
            anonymous=True,
            signatures=[CommandSignature(action="greet", default=True)],
        )
    )

    internal = Node(key="hidden", resolvable=False)
    root.add(internal)

    return root


def _make_resolver(
    root: Node, *, authorized: bool = True
) -> tuple[InvocationResolver, list[str]]:
    permissions: list[str] = []

    def on_get_node(parent: Node, key: str) -> Node | None:
        return parent.get(key)

    def on_suggest(
        *, value: str, choices: list[str], limit: int = 3, cutoff: float = 0.5
    ) -> list[str]:
        return [f"suggest:{value}"]

    def on_authorize(*, session: Session, node: Node, operation: Operation) -> bool:
        permissions.append(f"{str(node.path)}:{operation.value}")
        return authorized

    resolver = InvocationResolver(
        root=root,
        on_authorize=on_authorize,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
    )
    return resolver, permissions


# ----------------------------------------
# BASIC RESOLUTION
# ----------------------------------------


def test_resolves_simple_command_from_root():
    root = _build_tree()
    resolver, _ = _make_resolver(root)

    node, tokens = resolver.resolve("system", None, _session())

    assert node is root.get("system")
    assert tokens == []


def test_empty_key_raises_not_found():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(NodeNotFound) as exc:
        resolver.resolve("  ", None, _session())

    assert exc.value.command == ""


def test_unknown_command_raises_not_found_with_suggestions():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(NodeNotFound) as exc:
        resolver.resolve("nope", None, _session())

    assert exc.value.suggestions == ["suggest:nope"]


def test_non_resolvable_node_is_rejected():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(NodeNotExecutable) as exc:
        resolver.resolve("hidden", None, _session())

    assert exc.value.command == "hidden"


# ----------------------------------------
# PATH RESOLUTION
# ----------------------------------------


def test_relative_path_resolution():
    root = _build_tree()
    resolver, _ = _make_resolver(root)

    node, tokens = resolver.resolve("ident/users", ["list"], _session())

    ident = root.get("ident")
    assert ident is not None
    assert node is ident.get("users")
    assert tokens == ["list"]


def test_absolute_path_resolution():
    resolver, _ = _make_resolver(_build_tree())

    node, tokens = resolver.resolve("/ident/users", ["list"], _session())

    assert node.key == "users"
    assert tokens == ["list"]


def test_path_intermediate_missing_returns_none():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(NodeNotFound) as exc:
        resolver.resolve("ident/nope/users", None, _session())

    assert exc.value.command == "ident/nope/users"


# ----------------------------------------
# SESSION CONTEXT
# ----------------------------------------


def test_resolves_from_session_context():
    root = _build_tree()
    resolver, _ = _make_resolver(root)

    # cwd = /ident/users → "admin" resolves there first
    node, _ = resolver.resolve("admin", None, _session(cwd="/ident/users"))

    ident = root.get("ident")
    assert ident is not None
    users = ident.get("users")
    assert users is not None
    assert node.key == "admin"
    assert node.parent is users


def test_falls_back_to_root_when_not_in_context():
    resolver, _ = _make_resolver(_build_tree())

    # cwd = /ident/users but "system" lives under root
    node, _ = resolver.resolve("system", None, _session(cwd="/ident/users"))

    assert node.key == "system"


def test_root_cwd_resolves_from_root():
    resolver, _ = _make_resolver(_build_tree())

    node, _ = resolver.resolve("system", None, _session(cwd="/"))

    assert node.key == "system"


def test_missing_context_path_falls_back_to_root():
    resolver, _ = _make_resolver(_build_tree())

    # cwd points into a node that does not exist → resolve from root
    node, _ = resolver.resolve("system", None, _session(cwd="/ident/void"))

    assert node.key == "system"


# ----------------------------------------
# USAGE ('?')
# ----------------------------------------


def test_usage_token_raises_usage_for_action():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(UsageError) as exc:
        resolver.resolve("system", ["?"], _session())

    assert exc.value.command == "system"
    assert exc.value.usages[0]["action"] == "version"


def test_usage_token_falls_back_to_children():
    root = _build_tree()
    resolver, _ = _make_resolver(root)
    leaf = Node(key="bare")
    root.add(leaf)
    leaf.add(Node(key="run", signatures=[CommandSignature(action="do")]))

    with pytest.raises(UsageError) as exc:
        resolver.resolve("bare", ["?"], _session())

    assert any(u["action"] == "do" for u in exc.value.usages)


def test_usage_on_path_resolution():
    resolver, _ = _make_resolver(_build_tree())

    with pytest.raises(UsageError) as exc:
        resolver.resolve("ident/users", ["list", "?"], _session())

    assert exc.value.command == "users"


# ----------------------------------------
# CONTEXTUAL TRAVERSAL
# ----------------------------------------


def test_contextual_child_traversal_consumes_token():
    resolver, _ = _make_resolver(_build_tree())

    node, tokens = resolver.resolve("ident", ["users", "list"], _session())

    ident = resolver._root.get("ident")
    assert ident is not None
    assert node is ident.get("users")
    assert tokens == ["list"]


def test_contextual_node_keeps_target_when_no_match():
    resolver, _ = _make_resolver(_build_tree())

    node, tokens = resolver.resolve("ident", ["list"], _session())

    assert node.key == "ident"
    assert tokens == ["list"]


# ----------------------------------------
# PERMISSIONS
# ----------------------------------------


def test_permission_checked_as_execute_operation():
    root = _build_tree()
    resolver, permissions = _make_resolver(root)

    resolver.resolve("system", None, _session())

    assert "/root/system:execute" in permissions


def test_permission_with_action_uses_same_operation():
    root = _build_tree()
    resolver, permissions = _make_resolver(root)

    resolver.resolve("system", ["version"], _session())

    assert "/root/system:execute" in permissions


def test_permission_denied_raises():
    resolver, _ = _make_resolver(_build_tree(), authorized=False)

    with pytest.raises(PermissionDenied):
        resolver.resolve("system", None, _session())


def test_anonymous_node_skips_permission_check():
    root = _build_tree()
    resolver, permissions = _make_resolver(root)

    resolver.resolve("app/hello", None, _session())

    assert permissions == []


def test_signature_bind_produces_invocation_without_action_in_args():
    """CommandSignature.bind() erzeugt eine Invocation ohne Action im Args.

    ADR-12: eine Invocation ist path + args, der Command-Name lebt nur im
    path — er wird nie in args dupliziert.
    """

    sig = CommandSignature(
        action="copy",
        params=[
            Param(key="source", required=True, positional=True),
            Param(key="target", required=True, positional=True),
            Param(key="verbose", positional=False),
        ],
    )

    inv = sig.bind(
        {"source": "a.txt", "target": "b.txt", "verbose": "1"},
        path="/usr/bin/copy",
        lang="de",
    )

    assert inv.path == "/usr/bin/copy"
    assert inv.args == ["a.txt", "b.txt", "--verbose", "1"]
    assert inv.lang == "de"
    assert "copy" not in inv.args


def test_invocation_is_dispatchable_via_parser():
    """Eine gebundene Invocation kann direkt dispatcht werden.

    Der Parser erkennt eine Invocation im Event-Payload und extrahiert
    path + args — der Request-Roundtrip ist weg.
    """

    from y5n.runtime.api.runtime import Event
    from y5n.runtime.api.runtime.invocation import Invocation
    from y5n.runtime.engine.machine.parser import InputParser

    parser = InputParser()
    inv = Invocation(path="/usr/bin/copy", args=["a.txt", "b.txt"])

    cmd, args, pipeline = parser.parse(Event(payload=inv))

    assert cmd == "/usr/bin/copy"
    assert args == ["a.txt", "b.txt"]
    assert pipeline == []
