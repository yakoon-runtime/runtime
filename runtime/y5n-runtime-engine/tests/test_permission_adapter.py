"""permissions port — end-to-end over the Runtime Bus.

A command asks `permissions.check(path, "read")`; the adapter resolves
the path to a node and delegates to the checker with the caller session.
Runtime nodes without a grant are denied; non-tree paths (filesystem
mounts) are allowed.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import PermBits, Permission
from y5n.runtime.engine.capabilities.permission import PermissionChecker
from y5n.runtime.engine.capabilities.permission.models.set import PermissionSet
from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData
from y5n.runtime.engine.wire.adapter.permission import PermissionAdapter


def _write(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(tmp_path) -> Tree:
    _write(
        tmp_path / "opt" / "crm" / "contact" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Contact",
                "resolvable: true",
                "navigable: false",
            ]
        ),
    )
    _write(
        tmp_path / "opt" / "crm" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: CRM",
                "resolvable: false",
                "navigable: true",
            ]
        ),
    )
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=tmp_path, executors=registry)
    tree.build()
    return tree


class _FakeManager:
    def __init__(self, session: Session):
        self._sessions = {session.key: _Runner(session)}


class _Runner:
    def __init__(self, session: Session):
        self.session = session


@pytest.mark.asyncio
async def test_check_denies_runtime_node_without_grant(tmp_path):
    tree = _build_tree(tmp_path)
    session = Session(
        key=Key.from_parts("test", "session", "perm", "1"),
        data=SessionData(),
    )
    session.set_permissions(PermissionSet())

    adapter = PermissionAdapter(_FakeManager(session), tree, PermissionChecker())
    call = type("Call", (), {"caller_session_key": str(session.key)})()

    assert await adapter.check(call, path="/opt/crm", operation="read") is False


@pytest.mark.asyncio
async def test_check_allows_with_grant(tmp_path):
    tree = _build_tree(tmp_path)
    session = Session(
        key=Key.from_parts("test", "session", "perm", "2"),
        data=SessionData(),
    )
    permset = PermissionSet()
    permset.add(Permission(path="/opt", bits=PermBits.from_str("rwx")))
    session.set_permissions(permset)

    adapter = PermissionAdapter(_FakeManager(session), tree, PermissionChecker())
    call = type("Call", (), {"caller_session_key": str(session.key)})()

    assert await adapter.check(call, path="/opt/crm", operation="read") is True


@pytest.mark.asyncio
async def test_check_allows_non_tree_path(tmp_path):
    tree = _build_tree(tmp_path)
    session = Session(
        key=Key.from_parts("test", "session", "perm", "3"),
        data=SessionData(),
    )
    session.set_permissions(PermissionSet())

    adapter = PermissionAdapter(_FakeManager(session), tree, PermissionChecker())
    call = type("Call", (), {"caller_session_key": str(session.key)})()

    # ~/home is not a runtime node -> allowed (filesystem mount)
    assert await adapter.check(call, path="/home/stefan", operation="read") is True
