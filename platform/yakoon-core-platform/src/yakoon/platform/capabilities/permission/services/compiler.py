# services/permissions/bootstrap.py

from __future__ import annotations

from typing import Protocol

from yakoon.platform.capabilities.permission import Permission, PermissionSet


class PermissionCompiler:

    def __init__(
        self,
        permission_specs: list[str],
        on_parse: OnParsePermissionSpec,
    ):
        self.on_parse = on_parse
        self.permission_specs = permission_specs

    def compile(self) -> PermissionSet:
        out = PermissionSet()

        for spec in self.permission_specs:
            permission = self.on_parse(spec=spec)
            out.add(permission)

        return out


# ----------------------------------
# PORTS
# ----------------------------------


class OnParsePermissionSpec(Protocol):
    def __call__(self, *, spec: str) -> Permission: ...
