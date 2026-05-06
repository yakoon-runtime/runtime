from __future__ import annotations

from collections.abc import Iterable

from yakoon.platform.runtime.sessions import Session

from ..models import PermBit, PermBits, Permission, PermissionSet


class PermissionService:

    _roles: dict[str, list[str]]
    _directs: list[str]

    def __init__(self):

        self._roles: dict[str, list[str]] = {}
        self._directs = [
            # ident
            "ident-app:su|rx",
            "ident-app:whoami|rx",
            "ident-app:user|rx",
            "ident-app:user.list|rx",
            # jobs
            "jobs:jobs|rx",
            # shell
            "shell-app:welcome|rx",
            "shell-app:version|rx",
            "shell-app:man|rx",
            "shell-app:exit|rx",
            "shell-app:quit|rx",
            "shell-app:test|rx",
            "shell-app:city.show.all|rx",
            "shell-app:su|rx",
            "shell-app:use|rx",
            "crm-customer:customer-create|rx",
            "crm-customer:wf:crm.customer.store|rx",
            "crm-customer:wf:crm.customer.validate|rx",
            "discovery:lookup|rx",
            # demo DSL
            "demo.dsl:demo.focus.simple|rx",
            "demo.dsl:demo.send.simple|rx",
            "demo.dsl:demo.receive.simple|rx",
            "demo.dsl:demo.delay.simple|rx",
            "demo.dsl:demo.present.simple|rx",
            # demo patterns
            "demo.patterns:demo.validate.simple|rx",
            "demo.patterns:demo.subflow.simple|rx",
            "demo.patterns:demo.form.simple|rx",
            "demo.patterns:demo.form.select|rx",
        ]

    # ----------------------------------
    # REGISTER
    # ----------------------------------

    async def register_role(self, name: str, specs: list[str]) -> None:
        if name in self._roles:
            raise ValueError(f"Role already registered: {name}")
        self._roles[name] = specs

    # ----------------------------------
    # APPLY
    # ----------------------------------

    def apply_bootstrap(self, session: Session):
        session.set_permissions(self._compile([], self._directs))

    def apply_account(self, session: Session, roles: list[str], permissions: list[str]):
        bootstrap = self._compile([], self._directs)
        account_ps = self._compile(roles, permissions)
        bootstrap.merge(account_ps)
        session.set_permissions(bootstrap)

    # ----------------------------------
    # CHECK EXECUTE / READ
    # ----------------------------------

    def can_execute(self, session: Session, perm_key: str) -> bool:
        return session.permissions.check(perm_key, PermBit.EXECUTE)

    def can_read(self, session: Session, perm_key: str) -> bool:
        return session.permissions.check(perm_key, PermBit.READ)

    # ----------------------------------
    # INTERNAL METHODS
    # ----------------------------------

    def _compile(self, roles: Iterable[str], direct: Iterable[str]) -> PermissionSet:

        ps = PermissionSet()

        # 1) expand roles -> specs
        for role in roles:
            specs = self._roles.get(role)
            if specs is None:
                raise ValueError(f"Unknown role: {role}")
            for spec in specs:
                ps.add(self._parse_spec(spec))

        # 2) add direct specs
        for spec in direct:
            ps.add(self._parse_spec(spec))

        return ps

    def _parse_spec(self, spec: str) -> Permission:
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
