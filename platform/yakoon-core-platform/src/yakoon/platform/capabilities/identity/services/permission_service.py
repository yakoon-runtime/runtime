from __future__ import annotations

from collections.abc import Iterable

from yakoon.base.capabilities.identity import (
    Account,
    PermBit,
    PermBits,
    Permission,
    PermissionSet,
)
from yakoon.platform.runtime.sessions import Session


class DefaultPermissionService:

    _roles: dict[str, list[str]]
    _directs: list[str]

    def __init__(self):

        self._roles: dict[str, list[str]] = {}
        self._directs = [
            "auth:su|rx",
            "auth:whoami|rx",
            "jobs:jobs|rx",
            "shell:welcome|rx",
            "shell:version|rx",
            "shell:man|rx",
            "shell:exit|rx",
            "shell:quit|rx",
            "shell:su|rx",
            "crm-customer:customer-create|rx",
            "crm-customer:wf:crm.customer.store|rx",
            "crm-customer:wf:crm.customer.validate|rx",
            "workflow:wf.run|rx",
            "workflow:wf.input|rx",
            "workflow:wf.next|rx",
            "workflow:wf.cancel|rx",
            "shell:use|rx",
            "discovery:lookup|rx",
            # demo
            "demo:demo.delay|rx",
            "demo:demo.projector|rx",
            "demo:demo.focus.simple|rx",
            "demo:demo.validate|rx",
            "demo:demo.subflow|rx",
            "demo:demo.send.simple|rx",
            "demo:demo.receive.simple|rx",
        ]

    def register_role(self, name: str, specs: list[str]) -> None:
        if name in self._roles:
            raise ValueError(f"Role already registered: {name}")
        self._roles[name] = specs

    def set_bootstrap_permissions(self, session: Session):
        session.set_permissions(self.compile_permissions([], self._directs))

    def apply_account_permissions(self, session: Session, account: Account):
        bootstrap = self.compile_permissions([], self._directs)
        account_ps = self.compile_permissions(account.roles, account.permissions)
        bootstrap.merge(account_ps)
        session.set_permissions(bootstrap)

    def can_execute(self, session: Session, perm_key: str) -> bool:
        return session.permissions.check(perm_key, PermBit.EXECUTE)

    def can_read(self, session: Session, perm_key: str) -> bool:
        return session.permissions.check(perm_key, PermBit.READ)

    def compile_permissions(
        self, roles: Iterable[str], direct: Iterable[str]
    ) -> PermissionSet:

        ps = PermissionSet()

        # 1) expand roles -> specs
        for role in roles:
            specs = self._roles.get(role)
            if specs is None:
                raise ValueError(f"Unknown role: {role}")
            for spec in specs:
                ps.add(self.parse_permission(spec))

        # 2) add direct specs
        for spec in direct:
            ps.add(self.parse_permission(spec))

        return ps

    def parse_permission(self, spec: str) -> Permission:
        """
        Formats:
        "auth:su|rx"
        "auth:su|rx:rx"   (two scopes)
        "-auth:su|x"      (deny)
        "-auth:su|rx:--"  (optional future idea; today we only parse r/x)
        """
        if not spec or not spec.strip():
            raise ValueError("Empty permission spec")

        s = spec.strip()
        deny = s.startswith("-")
        if deny:
            s = s[1:].strip()

        if "|" not in s:
            raise ValueError(f"Invalid permission (missing '|'): {spec}")

        key, rights = s.split("|", 1)
        key = key.strip()
        rights = rights.strip()

        if not key:
            raise ValueError(f"Invalid permission (empty command key): {spec}")

        # scope split: "rx" or "rx:rx"
        parts = rights.split(":")
        if len(parts) == 1:
            return Permission(
                command_key=key,
                scope1=PermBits.from_str(parts[0]),
                scope2=None,
                deny=deny,
            )
        if len(parts) == 2:
            return Permission(
                command_key=key,
                scope1=PermBits.from_str(parts[0]),
                scope2=PermBits.from_str(parts[1]),
                deny=deny,
            )

        raise ValueError(f"Invalid permission (too many scopes): {spec}")


# --- Role expansion (phase 1: map) ------------------------------------------

_ROLE_MAP: dict[str, list[str]] = {
    "admin": [
        "auth:su|rx",
        "shell:use|rx",
        "office.mailing:send|rx",
        # ...
    ],
    "user": [
        "shell:use|rx",
    ],
}
