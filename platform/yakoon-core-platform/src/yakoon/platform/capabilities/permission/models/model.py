from __future__ import annotations

from dataclasses import dataclass

from .bit import PermBits


@dataclass(frozen=True)
class Permission:
    """
    command_key: e.g. "auth:su"
    bits: PermBits, e.g. rwx
    scope1/scope2:
      - scope1 is the "primary" scope (e.g. account)
      - scope2 optional (e.g. group / tenant / controller-context)
    deny: if True, removes bits instead of adding them
    """

    command_key: str
    scope1: PermBits
    scope2: PermBits | None = None
    deny: bool = False

    @property
    def is_scoped(self) -> bool:
        return self.scope2 is not None

    @staticmethod
    def fq_key(app_id: str, command_key: str, action: str | None) -> str:
        """
        Returns fq_key (fully qualified key)
        """
        if action and action != "*":
            return f"{app_id}:{command_key}.{action}"
        return f"{app_id}:{command_key}"
