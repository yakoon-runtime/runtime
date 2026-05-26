# services/permissions/parser.py

from __future__ import annotations

from ..models import PermBits, Permission


class PermissionParser:

    def parse(self, spec: str) -> Permission:
        """
        Formats:

        ident:user.edit|rx
        ident:user.edit|rx:rx
        -ident:user.edit|x
        """

        if not spec or not spec.strip():
            raise ValueError("Empty permission spec")

        s = spec.strip()
        deny = s.startswith("-")
        if deny:
            s = s[1:].strip()

        if "|" not in s:
            raise ValueError(f"Invalid permission " f"(missing '|'): {spec}")

        key, rights = s.split("|", 1)

        key = key.strip()
        rights = rights.strip()
        if not key:
            raise ValueError(f"Invalid permission " f"(empty key): {spec}")

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

        raise ValueError(f"Invalid permission " f"(too many scopes): {spec}")
