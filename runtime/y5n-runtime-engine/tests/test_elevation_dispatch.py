"""Dispatch-level elevation: the resolver gates privileged nodes.

A ``privileged`` node in a normal session is refused with
ElevationRequired; the engine routes it to the err node (ADR: an error
creates a new invocation). An administrative session runs it directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import PermBits, Permission
from y5n.runtime.api.runtime import Event
from y5n.runtime.api.runtime.sessions import SecurityContext
from y5n.runtime.engine.capabilities.permission.models.set import PermissionSet
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.machine.engine import CommandEngine
from y5n.runtime.engine.machine.resolver import InvocationResolver
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime.invocation import error_payload
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _danger_handler():
    def gen():
        return None

    return gen()


def _err_handler():
    def gen():
        return None

    return gen()


def _make_system(root: Path):
    _write(
        root / "usr" / "sbin" / "danger" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Danger",
                "resolvable: true",
                "navigable: false",
                "privileged: true",
            ]
        ),
    )
    _write(
        root / "usr" / "bin" / "err" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Err",
                "anonymous: true",
            ]
        ),
    )


def _session(context: str = "normal") -> Session:
    session = Session(
        key=Key.from_parts("test", "session", "dispatch", "1"),
        data=SessionData(),
    )
    permset = PermissionSet()
    permset.add(Permission(path="/", bits=PermBits.from_str("rwx")))
    session.set_permissions(permset)
    session.set_security_context(context)
    return session


def _engine(tree: Tree) -> CommandEngine:
    root = tree.root()
    checker = None

    from y5n.runtime.engine.capabilities.permission import PermissionChecker

    checker = PermissionChecker()

    def on_get_node(parent: Node, key: str) -> Node | None:
        return parent.get(key)

    def on_suggest(*, value: str, choices: list[str], limit: int = 3, cutoff: float = 0.5):
        return []

    resolver = InvocationResolver(
        root=root,
        on_authorize=checker.check,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
    )

    def on_parse_input(*, event):
        return event.payload, [], []

    async def on_intercept(*, node, tokens, session, context):
        return node, tokens

    async def on_apply_effects(*args, **kwargs):
        return None

    return CommandEngine(
        on_resolve_node=resolver.resolve,
        on_parse_input=on_parse_input,
        on_intercept=on_intercept,
        on_apply_effects=on_apply_effects,
    )


@pytest.mark.asyncio
async def test_normal_session_refuses_privileged_node(tmp_path):
    _make_system(tmp_path)
    tree = _build_tree(tmp_path)
    engine = _engine(tree)
    session = _session(SecurityContext.NORMAL)

    event = Event(payload="/usr/sbin/danger")
    flow = await engine.dispatch(session=session, event=event)

    # ElevationRequired was raised -> routed to the error node.
    assert flow is not None
    assert flow.node.key == "err"
    assert flow.invocation["error"]["type"] == "ElevationRequired"


@pytest.mark.asyncio
async def test_administrative_session_runs_privileged_node(tmp_path):
    _make_system(tmp_path)
    tree = _build_tree(tmp_path)
    engine = _engine(tree)
    session = _session(SecurityContext.ADMINISTRATIVE)

    event = Event(payload="/usr/sbin/danger")
    flow = await engine.dispatch(session=session, event=event)

    assert flow is not None
    assert flow.node.key == "danger"
    assert flow.invocation["session"]["security_context"] == "administrative"


@pytest.mark.asyncio
async def test_temporary_session_elevates_once_then_falls_back(tmp_path):
    _make_system(tmp_path)
    tree = _build_tree(tmp_path)
    engine = _engine(tree)
    session = _session(SecurityContext.TEMPORARY)

    event = Event(payload="/usr/sbin/danger")
    flow = await engine.dispatch(session=session, event=event)

    assert flow is not None
    assert flow.node.key == "danger"
    # temporary consumed -> back to normal
    assert session.security_context == SecurityContext.NORMAL

    flow = await engine.dispatch(session=session, event=event)
    assert flow.node.key == "err"
