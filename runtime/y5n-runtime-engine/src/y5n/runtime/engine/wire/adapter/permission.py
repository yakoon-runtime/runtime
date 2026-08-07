"""Adapter: ``permissions`` port for the Runtime Bus.

Lets commands ask whether the caller session may perform a runtime
operation on a path. The path is resolved to a node; the checker maps
the operation onto the required bit via the node's type. Commands stay
ignorant of bits — they ask in operations (READ, WRITE, EXECUTE).

Semantics: only runtime nodes are protected. A path that is not part of
the runtime tree (e.g. a plain filesystem mount like ~/home) is not a
runtime resource and therefore allowed (True). Runtime nodes without a
grant are denied.
"""

from __future__ import annotations

from y5n.runtime.api.naming import Key
from y5n.runtime.api.permissions import Operation
from y5n.runtime.api.runtime.invoke import Call


class PermissionAdapter:
    """SDK-facing ``permissions.check`` Port."""

    def __init__(self, manager, tree, checker) -> None:
        self._manager = manager
        self._tree = tree
        self._checker = checker

    async def check(
        self,
        call: Call,
        *,
        path: str,
        operation: str | Operation,
    ) -> bool:
        session_key = call.caller_session_key
        if not session_key:
            return False

        runner = self._manager._sessions.get(Key.from_str(session_key))
        if runner is None:
            return False

        node = self._tree.find(path)
        if node is None:
            return True

        op = Operation(operation)
        return self._checker.check(runner.session, node, op)
