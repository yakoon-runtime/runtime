from __future__ import annotations

from dataclasses import dataclass

from .bit import PermBits


@dataclass(frozen=True)
class Permission:
    """
    A grant of operations on a runtime path.

    path: full node path, e.g. "/crm/contact/edit"
    bits: PermBits, e.g. rwx
    deny: if True, removes bits instead of adding them
    """

    path: str
    bits: PermBits
    deny: bool = False

    @staticmethod
    def fq_key(path: str, action: str | None) -> str:
        """
        Returns the fully qualified permission key for a runtime path.
        """
        if action and action != "*":
            return f"{path}.{action}"
        return path
