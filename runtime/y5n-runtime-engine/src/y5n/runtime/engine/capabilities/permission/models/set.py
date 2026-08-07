from __future__ import annotations

from y5n.runtime.api.permissions import PermBits, Permission


class PermissionSet:
    """
    Holds effective permissions for a session/account.

    Policy:
      - Allows accumulate (union)
      - Denies subtract (deny wins over allow for the denied bits)
    """

    def __init__(self) -> None:
        self._allow: dict[str, Permission] = {}
        self._deny: dict[str, Permission] = {}

    def __iter__(self):
        yield from self._allow.values()
        yield from self._deny.values()

    def add(self, perm: Permission) -> None:
        target = self._deny if perm.deny else self._allow
        existing = target.get(perm.path)

        if not existing:
            target[perm.path] = perm
            return

        # merge bits (same deny/allow bucket)
        target[perm.path] = Permission(
            path=perm.path,
            bits=existing.bits.union(perm.bits),
            deny=perm.deny,
        )

    def merge(self, other: PermissionSet) -> None:
        for p in other:
            self.add(p)

    def check(self, path: str, need: str = "x") -> bool:
        """
        need: "r" | "w" | "x" | combinations like "rw", "rwx"
        """
        need_bits = PermBits.from_str(need)

        allow = self._allow.get(path)
        if not allow:
            return False

        # compute effective bits = allow - deny
        deny = self._deny.get(path)
        eff = allow.bits
        if deny:
            eff = eff.subtract(deny.bits)

        if need_bits.r and not eff.r:
            return False
        if need_bits.w and not eff.w:
            return False
        if need_bits.x and not eff.x:
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
                "allow": bits_to_str(a.bits) if a else "",
                "deny": bits_to_str(d.bits) if d else "",
            }
        return out
