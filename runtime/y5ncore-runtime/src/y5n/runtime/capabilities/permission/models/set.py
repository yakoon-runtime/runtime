from __future__ import annotations

from .bit import PermBits
from .model import Permission


class PermissionSet:
    """
    Holds effective permissions for a session/account.

    Policy:
      - Allows accumulate (union)
      - Denies subtract (deny wins over allow for the denied bits)
      - For now we apply scope1 always; scope2 is stored but not enforced unless you pass a scope2 requirement.
    """

    def __init__(self) -> None:
        self._allow: dict[str, Permission] = {}
        self._deny: dict[str, Permission] = {}

    def __iter__(self):
        yield from self._allow.values()
        yield from self._deny.values()

    def add(self, perm: Permission) -> None:
        target = self._deny if perm.deny else self._allow
        existing = target.get(perm.command_key)

        if not existing:
            target[perm.command_key] = perm
            return

        # merge bits (same deny/allow bucket)
        merged_scope1 = existing.scope1.union(perm.scope1)
        merged_scope2 = None
        if existing.scope2 or perm.scope2:
            merged_scope2 = (existing.scope2 or PermBits()).union(
                perm.scope2 or PermBits()
            )

        target[perm.command_key] = Permission(
            command_key=perm.command_key,
            scope1=merged_scope1,
            scope2=merged_scope2,
            deny=perm.deny,
        )

    def merge(self, other: PermissionSet) -> None:
        for p in other:
            self.add(p)

    def check(
        self, command_key: str, need: str = "x", scope2_need: str | None = None
    ) -> bool:
        """
        need: "r" | "w" | "x" | combinations like "rw", "rwx"
        scope2_need: optional second-scope requirement (future use)
        """
        need_bits = PermBits.from_str(need)
        need2_bits = PermBits.from_str(scope2_need) if scope2_need else None

        allow = self._allow.get(command_key)
        if not allow:
            return False

        # compute effective scope1 bits = allow - deny
        deny = self._deny.get(command_key)
        eff1 = allow.scope1
        if deny:
            eff1 = eff1.subtract(deny.scope1)

        if need_bits.r and not eff1.r:
            return False
        if need_bits.w and not eff1.w:
            return False
        if need_bits.x and not eff1.x:
            return False

        # optional scope2 check (only if requested and available)
        if need2_bits:
            if not allow.scope2:
                return False
            eff2 = allow.scope2
            if deny and deny.scope2:
                eff2 = eff2.subtract(deny.scope2)

            if need2_bits.r and not eff2.r:
                return False
            if need2_bits.w and not eff2.w:
                return False
            if need2_bits.x and not eff2.x:
                return False

        return True

    def clone(self) -> PermissionSet:

        out = PermissionSet()

        out._allow = self._allow.copy()
        out._deny = self._deny.copy()

        return out

    def to_debug_dict(self) -> dict[str, dict[str, str]]:

        def bits_to_str(b: PermBits | None) -> str:
            if not b:
                return ""
            return ("r" if b.r else "") + ("w" if b.w else "") + ("x" if b.x else "")

        out: dict[str, dict[str, str]] = {}
        keys = set(self._allow.keys()) | set(self._deny.keys())
        for k in sorted(keys):
            a = self._allow.get(k)
            d = self._deny.get(k)
            out[k] = {
                "allow1": bits_to_str(a.scope1) if a else "",
                "allow2": bits_to_str(a.scope2) if a else "",
                "deny1": bits_to_str(d.scope1) if d else "",
                "deny2": bits_to_str(d.scope2) if d else "",
            }
        return out
