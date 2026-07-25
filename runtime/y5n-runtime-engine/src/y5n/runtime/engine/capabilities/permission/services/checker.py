from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from y5n.runtime.engine.runtime import Session

from ..models import PermBit


class PermissionChecker:

    def can_read(self, session: Session, perm_key: str) -> bool:
        if not session.permissions:
            return False
        return session.permissions.check(perm_key, PermBit.READ)

    def can_write(self, session: Session, perm_key: str) -> bool:
        if not session.permissions:
            return False
        return session.permissions.check(perm_key, PermBit.WRITE)

    def can_execute(self, session: Session, perm_key: str) -> bool:
        if not session.permissions:
            return False
        return session.permissions.check(perm_key, PermBit.EXECUTE)
