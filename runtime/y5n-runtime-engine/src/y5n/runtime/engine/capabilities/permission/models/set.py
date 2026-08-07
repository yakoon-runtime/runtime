from __future__ import annotations

from y5n.runtime.api.permissions import PermBits, Permission


class PermissionSet:
    """
    Holds effective permissions for a session/account.

    Policy:
      - A grant on a path applies to that path and all its descendants
        (segment-based inheritance along the runtime path hierarchy).
      - The most specific matching grant decides.
      - On the same level: allows accumulate (union), denies subtract
        (deny wins over allow for the denied bits).
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

        Allows and denies each accumulate along the whole path chain
        (most specific to most general ancestor, e.g. /usr/bin/ls ->
        /usr/bin -> /usr -> /). Effective bits = union(allows) minus
        union(denies). A deny only removes its own bits — a broader
        allow stays as the base.
        """
        need_bits = PermBits.from_str(need)

        allow_bits = PermBits()
        deny_bits = PermBits()
        has_allow = False

        for ancestor in _ancestors(path):
            allow = self._allow.get(ancestor)
            if allow:
                allow_bits = allow_bits.union(allow.bits)
                has_allow = True

            deny = self._deny.get(ancestor)
            if deny:
                deny_bits = deny_bits.union(deny.bits)

        if not has_allow:
            return False

        eff = allow_bits.subtract(deny_bits)

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


def _ancestors(path: str) -> list[str]:
    """Return path and all its ancestors, most specific first.

    "/usr/bin/ls" -> ["/usr/bin/ls", "/usr/bin", "/usr", "/"]
    """
    normalized = path.strip()
    if not normalized:
        return ["/"]

    parts = [p for p in normalized.strip("/").split("/") if p]
    if not parts:
        return ["/"]

    out: list[str] = []
    for i in range(len(parts), 0, -1):
        out.append("/" + "/".join(parts[:i]))
    out.append("/")
    return out
