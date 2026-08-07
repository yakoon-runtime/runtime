# services/permissions/parser.py

from __future__ import annotations

from ..models import PermBits, Permission


class PermissionParser:

    def parse(self, spec: str) -> Permission:
        """
        Formats:

        /ident/users/list|rx
        -/ident/users/list|x
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

        if ":" in rights:
            raise ValueError(f"Invalid permission " f"(scope not supported): {spec}")

        return Permission(
            path=key,
            bits=PermBits.from_str(rights),
            deny=deny,
        )
