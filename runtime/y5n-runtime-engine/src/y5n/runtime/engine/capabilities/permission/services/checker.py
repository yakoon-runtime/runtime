from __future__ import annotations

from typing import TYPE_CHECKING

from y5n.runtime.api.permissions import Operation

if TYPE_CHECKING:
    from y5n.runtime.engine.nodes import Node
    from y5n.runtime.engine.runtime import Session


class PermissionChecker:
    """Asks whether a session may perform an operation on a node.

    The operation API is the future: ``check(session, node, operation)`` —
    the node maps the operation onto the required bit via
    ``node.required_bit(operation)``. The legacy ``can_execute(session,
    perm_key)`` string API remains for the resolver until it is migrated.
    """

    # ----------------------------------
    # OPERATION API (new)
    # ----------------------------------

    def check(self, session: Session, node: Node, operation: Operation) -> bool:
        if not session.permissions:
            return False
        bit = node.required_bit(operation)
        return session.permissions.check(str(node.path), bit)

    def can_read(self, session: Session, node: Node) -> bool:
        return self.check(session, node, Operation.READ)

    def can_write(self, session: Session, node: Node) -> bool:
        return self.check(session, node, Operation.WRITE)

    def can_execute(self, session: Session, node: Node) -> bool:
        return self.check(session, node, Operation.EXECUTE)

    # ----------------------------------
    # LEGACY API (string perm_key)
    # ----------------------------------

    def can_execute_key(self, session: Session, perm_key: str) -> bool:
        if not session.permissions:
            return False
        return session.permissions.check(perm_key, "x")
